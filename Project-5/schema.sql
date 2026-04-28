-- Schema for the classifieds demo. Apply once against a fresh MySQL database:
--   mysql -h <host> -u <user> -p classifieds_db < schema.sql

CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(64)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sections (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    slug  VARCHAR(64)  NOT NULL UNIQUE,
    name  VARCHAR(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    section_id  INT          NOT NULL,
    slug        VARCHAR(64)  NOT NULL UNIQUE,
    name        VARCHAR(128) NOT NULL,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS listings (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    category_id  INT            NOT NULL,
    user_id      INT            NULL,
    title        VARCHAR(255)   NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,
    city         VARCHAR(128)   NOT NULL,
    phone        VARCHAR(32)    NOT NULL,
    description  TEXT           NOT NULL,
    image_url    VARCHAR(512)   NULL,
    attributes   JSON           NOT NULL,
    created_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE SET NULL,
    INDEX idx_category_created (category_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
