import mysql.connector
import dotenv
import os

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_HOSTNAME = "photogallerydb-instance.cbqcmomws8dc.us-east-2.rds.amazonaws.com"
DB_USERNAME = 'root'
DB_PASSWORD = 'password4220'
DB_NAME = 'photogallerydb'

conn = mysql.connector.connect(host=DB_HOSTNAME,
                        user=DB_USERNAME,
                        passwd=DB_PASSWORD,
                        db=DB_NAME,
                        port=3306)

cursor = conn.cursor()
cursor.execute("SELECT VERSION()")
version = cursor.fetchone()
print("MySQL version:", version[0])

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    UserID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    Username VARCHAR(255) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL
    );""")

print("Users table created successfully.")

cursor.close()
conn.close()
