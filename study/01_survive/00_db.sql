DROP DATABASE cinema;
CREATE DATABASE IF NOT EXISTS cinema;

USE cinema;

CREATE TABLE IF NOT EXISTS filmes (
    title VARCHAR(50) NOT NULL,
    genre VARCHAR(30) NOT NULL,
    age INT NOT NULL,
    PRIMARY KEY(title)
);

INSERT INTO filmes (title, genre, age)
VALUE ("Forest Gump", "Drama", 1994);

