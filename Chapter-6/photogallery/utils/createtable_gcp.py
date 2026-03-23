import mysql.connector
import dotenv
import os

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_HOSTNAME = os.environ.get("DB_HOSTNAME")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME     = os.environ.get("DB_NAME")

conn = mysql.connector.connect(host=DB_HOSTNAME,
                        user=DB_USERNAME,
                        passwd=DB_PASSWORD,
                        db=DB_NAME,
                        port=3306)

cursor = conn.cursor()
cursor.execute("SELECT VERSION()")
version = cursor.fetchone()
print("MySQL version:", version[0])

cursor.execute("""CREATE TABLE IF NOT EXISTS photogallery (
    PhotoID VARCHAR(36) PRIMARY KEY,
    UserID VARCHAR(255) NOT NULL,
    CreationTime TEXT NOT NULL,
    Title TEXT NOT NULL,
    Description TEXT NOT NULL,
    Tags TEXT NOT NULL,
    URL TEXT NOT NULL,
    EXIF TEXT,
    INDEX idx_user (UserID)
    );""")

print("photogallery table created successfully.")

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    UserID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    Username VARCHAR(255) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL
    );""")

print("users table created successfully.")

cursor.close()
conn.close()
