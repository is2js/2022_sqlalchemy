CREATE DATABASE IF NOT EXISTS cinema;

USE cinema;

CREATE TABLE IF NOT EXISTS filmes (
    title VARCHAR(50) NOT NULL,
    genre VARCHAR(30) NOT NULL,
    age INT NOT NULL,
    PRIMARY KEY(title)
);

CREATE TABLE IF NOT EXISTS artists (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    title_filmes VARCHAR(50) NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY (title_filmes) REFERENCES filmes(title)
);

INSERT INTO filmes (title, genre, age)
VALUE ("Forest Gump", "Drama", 1994);

INSERT INTO artists (name, title_filmes)
VALUE ("Tom Hanks", "Forest Gump");