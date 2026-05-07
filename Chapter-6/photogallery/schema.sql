-- Schema for the photogallery app.
-- Run once against a fresh MySQL instance:
--   mysql -h <host> -u <user> -p < schema.sql

CREATE DATABASE IF NOT EXISTS photogallerydb;
USE photogallerydb;

CREATE TABLE IF NOT EXISTS users (
    Username VARCHAR(64)  NOT NULL PRIMARY KEY,
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS photogallery (
    PhotoID      VARCHAR(36)  NOT NULL PRIMARY KEY,
    UserID       VARCHAR(64)  NOT NULL,
    CreationTime DATETIME     NOT NULL,
    Title        VARCHAR(255),
    Description  TEXT,
    Tags         VARCHAR(500),
    URL          TEXT,
    EXIF         JSON,
    INDEX idx_user (UserID),
    FOREIGN KEY (UserID) REFERENCES users(Username) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
