import mysql.connector
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# AWS S3 connection
s3 = boto3.client('s3', 
                  aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                  aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

BUCKET_NAME = "se4220-photo-gallery-team3-bucket"

# Database connection
conn = mysql.connector.connect(
    host="photogallerydb-instance.cbqcmomws8dc.us-east-2.rds.amazonaws.com",
    user='root',
    passwd='password4220',
    db='photogallerydb'
)

cursor = conn.cursor()

# Get all photos with old URLs
cursor.execute("SELECT PhotoID, URL FROM photogallery2")
all_photos = cursor.fetchall()

# Delete from both S3 and database
for photo in all_photos:
    photo_id = photo[0]
    url = photo[1]
    
    # Extract filename from URL (e.g., "photos/dashboard-view.png")
    if "photos/" in url:
        s3_key = url.split(".com/")[-1]  # Gets "photos/filename.png"
        
        # Delete from S3
        try:
            s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            print(f"Deleted {s3_key} from S3")
        except Exception as e:
            print(f"Error deleting {s3_key} from S3: {e}")
    
    # Delete from database
    cursor.execute("DELETE FROM photogallery2 WHERE PhotoID = %s", (photo_id,))
    print(f"Deleted photo ID {photo_id} from database")

conn.commit()
cursor.close()
conn.close()

print("Cleanup complete!")