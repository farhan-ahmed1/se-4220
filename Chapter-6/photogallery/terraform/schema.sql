-- Photogallery schema. Derived from the queries in main.py:
--   * users(Username, Password)              -- auth
--   * photogallery(PhotoID, UserID, ...)     -- one row per uploaded photo
--
-- Re-runnable: CREATE TABLE IF NOT EXISTS so the VM startup script can apply
-- this every boot without erroring.

CREATE TABLE IF NOT EXISTS users (
    Username VARCHAR(64)  NOT NULL PRIMARY KEY,
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS photogallery (
    PhotoID      VARCHAR(64)  NOT NULL PRIMARY KEY,
    UserID       VARCHAR(64)  NOT NULL,
    CreationTime DATETIME     NOT NULL,
    Title        VARCHAR(255),
    Description  TEXT,
    Tags         VARCHAR(255),
    URL          TEXT         NOT NULL,
    EXIF         JSON,
    INDEX idx_photogallery_user (UserID),
    CONSTRAINT fk_photogallery_user
        FOREIGN KEY (UserID) REFERENCES users(Username)
        ON DELETE CASCADE
);
