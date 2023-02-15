DROP DATABASE sqlalchemy;
CREATE DATABASE IF NOT EXISTS sqlalchemy;

USE sqlalchemy;

CREATE TABLE IF NOT EXISTS test
(
    title VARCHAR(50) NOT NULL,
    genre VARCHAR(30) NOT NULL,
    age   INT         NOT NULL,
    PRIMARY KEY (title)
);

INSERT INTO test (title, genre, age)
    VALUES ("Forest Gump", "Drama", 1994);