import mysql.connector
conn = mysql.connector.connect(
    host="photogallerydb-instance.cbqcmomws8dc.us-east-2.rds.amazonaws.com",
    user="root", passwd="password4220", db="photogallerydb", port=3306)
cursor = conn.cursor()
cursor.execute("SHOW TABLES;")
print(cursor.fetchall())
cursor.execute("DESCRIBE photogallery2;")
print(cursor.fetchall())
conn.close()