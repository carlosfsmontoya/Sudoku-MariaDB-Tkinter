/*
    @author javiermontoya@unah.hn
    @author fausto.maradiaga@unah.hn
    @version 0.1.10
    @date 2021/04/20
*/

DROP DATABASE IF EXISTS GameData;

CREATE DATABASE GameData CHARACTER SET utf8;

USE GameData;

-- Funciones.

DELIMITER $$

    -- Esta función buscará un usuario en la base de datos, será usada para evitar que ingresen usuarios iguales.
    CREATE FUNCTION fn_searchUser(V_USER TEXT) RETURNS BIGINT UNSIGNED
    BEGIN

    RETURN (SELECT COUNT(*) FROM UserInformation WHERE tex_user REGEXP BINARY CONCAT("^", V_USER, "$") AND bit_enable = 1);

    END$$

    -- Esta función retornará el id del board del ultimo juego de un jugador.
    CREATE FUNCTION fn_selectBoard(ID_USER TEXT) RETURNS BIGINT UNSIGNED
    BEGIN

    RETURN (SELECT s.id_board_fk FROM SudokuGame s INNER JOIN UserInformation u ON s.id_user_fk=u.id WHERE u.id=ID_USER ORDER BY s.id DESC LIMIT 1);

    END$$

    -- Funcion para extraer un trablero de un json recibiendo su nombre como parámetro
    CREATE FUNCTION fn_jsonBoard(jso_board JSON) RETURNS TEXT
    BEGIN
        RETURN JSON_UNQUOTE(JSON_EXTRACT(jso_board,'$.board'));
    END$$

    -- Función para extraer el nombre de un tablero de un json recibiendo el JSON como parámetro
    CREATE FUNCTION fn_boardName(jso_board JSON) RETURNS TEXT
    BEGIN
        RETURN JSON_UNQUOTE(JSON_EXTRACT(jso_board,'$.name'));
    END$$

    -- Esta función recuperará el tablero en progreso.
    CREATE FUNCTION fn_decrypt_answer(answer VARBINARY(20)) RETURNS TEXT
    BEGIN
    
        RETURN(CONVERT(aes_decrypt(answer,'Psudoku2021') USING utf8));

    END$$
DELIMITER ;


-- Procedimientos almacenados.

DELIMITER $$

    -- Este procedimiento validará si el usuario y/o contraseña existen o coinciden y almacenará el id, rol y status.
    DROP PROCEDURE IF EXISTS sp_validate$$
    CREATE PROCEDURE sp_validate(IN V_USER TEXT, IN V_PASSWORD TEXT, OUT ID_USER BIGINT UNSIGNED, OUT ROL_USER BIGINT UNSIGNED, OUT STATUS_USER BIT)
    BEGIN

    SELECT 
        id,
        id_rol_fk,
        bit_status
    FROM 
        UserInformation 
    WHERE 
        tex_user REGEXP BINARY CONCAT("^", V_USER, "$")
    AND 
        tex_password REGEXP BINARY CONCAT("^", V_PASSWORD, "$")
    AND 
        bit_enable = 1
    INTO 
        ID_USER,
        ROL_USER,
        STATUS_USER
        ;
    
    END$$

    -- Este procedimiento actualizará los estados de un juego pausado.
    DROP PROCEDURE IF EXISTS sp_updateStatus$$
    CREATE PROCEDURE sp_updateStatus(IN ID_USER BIGINT UNSIGNED)
    BEGIN

    UPDATE 
        SudokuGame 
    SET 
        bit_defeated = 1 
    WHERE 
        id = (SELECT id FROM SudokuGame WHERE id_user_fk = ID_USER ORDER BY id DESC LIMIT 1);
    
    UPDATE 
        UserInformation 
    SET 
        bit_status = 0 
    WHERE 
        id = ID_USER;
    
    END$$

    -- Este procedimiento eliminará los puntajes que no estén en la lista de los mejores 10.
    -- Para evitar que la base de datos se llene de datos que no serán utilizados.
    DROP PROCEDURE IF EXISTS sp_deleteScore$$
    CREATE PROCEDURE sp_deleteScore(IN ID_USER INT)
    BEGIN

        DELETE
            Score
        FROM 
            Score
        LEFT JOIN 
            (SELECT 
                tim_date 
            FROM 
                Score 
            WHERE 
                id_userInformation_fk = ID_USER 
            ORDER BY 
                tim_score, tim_date 
            LIMIT 10) Subquery
        ON Subquery.tim_date = Score.tim_date 
        WHERE 
            Score.id_userInformation_fk = ID_USER AND Subquery.tim_date IS NULL;

    END$$

    -- Este procedimiento enripta las respuestas del usuario y luego las inserta en la tabla.
    DROP PROCEDURE IF EXISTS sp_pushMove$$
    CREATE PROCEDURE sp_pushMove(IN id_game INT, tiny_row TINYINT, tiny_column TINYINT, answer INT)
    BEGIN
    
        INSERT INTO Moveset(id_sudokuGame_fk, tin_row, tin_column, Answer_b) VALUES 
            (id_game, tiny_row, tiny_column, AES_ENCRYPT(answer,'Psudoku2021'))
        ;
    
    END$$

DELIMITER ;


-- Tablas

CREATE TABLE Rol(
    id SERIAL PRIMARY KEY,
    tex_rol TEXT NOT NULL
)COMMENT "Tabla que representa el rol de un usuario en el sistema. ('Role' es una palabra reservada en SQL por lo que se usara 'Rol' en su lugar)";

CREATE TABLE UserInformation(
    id SERIAL PRIMARY KEY,
    id_rol_fk BIGINT UNSIGNED NOT NULL COMMENT "Rol dentro del juego",
    tex_user TEXT NOT NULL COMMENT "Usuario",
    tex_password TEXT NOT NULL COMMENT "Contraseña",
    bit_enable BIT(1) NOT NULL DEFAULT 1 COMMENT "BIT que representa si el usuario está en el estado deshabilitado",
    bit_status BIT(1) NOT NULL DEFAULT 0 COMMENT "BIT para representar el estado activo o inactivo de un usuario.",
    FOREIGN KEY (id_rol_fk) REFERENCES Rol(id)
) COMMENT "Tabla de usuarios";

CREATE TABLE Board(
    id SERIAL PRIMARY KEY,
    jso_board JSON NOT NULL COMMENT "JSON contenedor del nombre del tablero y un arreglo bidimensional que sirve para contener el tablero."
) COMMENT "Tabla que contiene información campo multi-valor con los tableros del juego.";

CREATE TABLE SudokuGame(
    id SERIAL PRIMARY KEY,
    id_board_fk BIGINT UNSIGNED NOT NULL COMMENT "llave foranea que referencia una relacion 1:1 (Cada juego de Sudoku contiene un unico tablero) ", 
    id_user_fk BIGINT UNSIGNED NOT NULL COMMENT "llave foranea que referencia una relacion 1:N (Cada juego tiene un unico usuario, un usuario puede tener varios juegos)",
    tim_invested TIME DEFAULT '00:00:00' COMMENT "Tiempo invertido en un juego de sudoku",
    bit_defeated BIT NOT NULL DEFAULT 0 COMMENT "IF (bit_defeated=1, 'Finalizado como derrota', 'Completado con una victoria') AS Completacion",
    FOREIGN KEY (id_board_fk) REFERENCES Board(id),
    FOREIGN KEY (id_user_fk) REFERENCES UserInformation(id)
) COMMENT "Tabla que contiene data de cada juego que se inicia en el sistema" ;

CREATE TABLE Moveset(
    id SERIAL PRIMARY KEY,
    id_sudokuGame_fk BIGINT UNSIGNED NOT NULL,
    tin_row TINYINT NOT NULL COMMENT "Fila donde se colocó una respuesta",
    tin_column TINYINT NOT NULL COMMENT "Columna donde se colocó una respuesta",
    Answer_b VARBINARY(20) COMMENT "Campo que almacenará las respuestas encriptadas",
    FOREIGN KEY(id_sudokuGame_fk) REFERENCES SudokuGame(id)
) COMMENT "Tabla de movimientos del jugador";

CREATE TABLE Score(
    id_userInformation_fk BIGINT UNSIGNED NOT NULL,
    id_board_fk BIGINT UNSIGNED NOT NULL COMMENT "Llave foránea que apunta al tablero en el cual se terminó el juego.",
    tim_score TIME NOT NULL COMMENT "Tiempo de juego en el tablero.",
    tim_date TIMESTAMP DEFAULT NOW() COMMENT "Fecha y hora en la cual se obtuvo el score.",
    FOREIGN KEY (id_userInformation_fk) REFERENCES UserInformation(id),
    FOREIGN KEY (id_board_fk) REFERENCES Board(id)
) COMMENT "Tabla de puntajes";

CREATE TABLE Log(
    id SERIAL PRIMARY KEY,
    id_user_fk BIGINT UNSIGNED NOT NULL COMMENT "llave foránea que referencia una relacion 1:N (Cada usuario tiene varias acciones en la bitácora)",
    tex_description VARCHAR(500) NOT NULL COMMENT "Descripción de lo que esta entrada significa",
    dat_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "Fecha en la cual se registra esta entrada",
    FOREIGN KEY (id_user_fk) REFERENCES UserInformation(id)
)COMMENT "Tabla que servirá como bitácora para el sistema, donde se almacenarán varias acciones.";


-- Inserción de datos.

INSERT INTO 
    Rol(tex_rol) 
VALUES
    ("admin"), ("player");

INSERT INTO
    UserInformation(id_rol_fk, tex_user, tex_password)
VALUES
    (1, "admin", "admin");

INSERT INTO Board(jso_board) VALUES
    ('{
        "name": "debug", 
        "board": 
            [
                [2,1,7,3,8,5,4,6,9],
                [3,8,5,4,6,9,7,1,2],
                [4,9,6,7,2,1,8,3,5],
                [5,2,4,8,1,6,9,7,3],
                [6,3,9,5,4,7,2,8,1],
                [8,7,1,2,9,3,5,4,6],
                [7,6,2,1,5,8,3,9,4],
                [9,5,3,6,7,4,1,2,8],
                [1,4,8,9,3,2,6,5,0]
            ]
            }'
    ),
    ('{
        "name": "n00b",
        "board":
            [
                [2,1,0,0,0,0,4,0,0],
                [3,8,0,4,0,0,7,0,2],
                [0,0,0,7,2,0,0,0,0],
                [0,2,4,8,0,6,9,0,0],
                [0,0,0,0,0,0,0,0,0],
                [0,0,1,2,0,3,5,4,0],
                [0,0,0,0,5,8,0,0,0],
                [9,0,3,0,0,4,0,2,8],
                [0,0,8,0,0,0,0,5,7]
            ]
            }'
    ),
    ('{
        "name": "l33t",
        "board":
            [
                [8,0,9,2,0,0,0,0,0],
                [2,0,0,9,8,0,1,6,0],
                [0,3,0,0,0,7,0,0,8],
                [0,0,8,6,0,0,5,0,0],
                [4,0,0,0,0,0,0,0,2],
                [0,0,3,0,0,8,4,0,0],
                [3,0,0,4,0,0,0,5,0],
                [0,4,5,0,3,2,0,0,6],
                [0,0,0,0,0,6,2,0,5]
            ]
            }'
    ),
    ('{
        "name": "error",
        "board": 
            [
                [8,0,9,2,0,0,0,0,0],
                [2,0,0,9,8,0,1,6,0],
                [0,3,0,0,0,7,0,0,8],
                [0,0,8,6,0,0,5,0,0],
                [4,0,0,0,0,0,0,0,2],
                [0,0,3,0,0,8,4,0,0],
                [3,0,0,4,0,0,0,5,0],
                [0,4,5,0,3,2,0,0,6]
            ]
            }'
    )
;


-- Triggers.

DELIMITER $$
    -- Creación del Trigger que será el encargado de la agregar a la tabla Log la opción de bitácora: Usuario Ingresado
    CREATE TRIGGER tg_insertUser
        AFTER INSERT
        ON UserInformation FOR EACH ROW 
    BEGIN 
        INSERT INTO Log(id_user_fk,tex_description) VALUES 
            (1,"Usuario Ingresado")
        ; 
    END$$

    -- Creación del Trigger que será el encargado de la agregar a la tabla Log la opción de bitácora: Usuario Actualizado
    CREATE TRIGGER tg_updateUser
        AFTER UPDATE 
        ON UserInformation FOR EACH ROW 
    BEGIN
        INSERT INTO Log(id_user_fk,tex_description) VALUES 
            (1,"Usuario Actualizado")
        ; 
    END $$ 
    
    -- Creación del Trigger que será el encargado de la agregar a la tabla Log la opción de bitácora: Eliminar Usuario
    CREATE TRIGGER tg_deleteUser
        AFTER DELETE 
        ON UserInformation FOR EACH ROW
    BEGIN
        INSERT INTO Log(id_user_fk,tex_description) VALUES 
            (1,"Usuario Eliminado")
        ; 
    END $$

    -- Vista de los scores con los nombres de los tableros
    CREATE VIEW vw_allScores AS 
    SELECT 
        id_userInformation_fk AS id_user,
        tim_date, 
        tim_score, 
        (   SELECT 
                fn_boardName(jso_board) 
            FROM 
                Board 
            WHERE 
                id = id_board_fk) AS 'tex_tableName' 
        FROM 
        Score
        ORDER BY tim_score, tim_date$$

DELIMITER ; 