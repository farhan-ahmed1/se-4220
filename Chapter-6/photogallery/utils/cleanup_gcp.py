import mysql.connector
from google.cloud import storage
import os
import dotenv

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

GCP_KEY_FILE = os.environ.get("GCP_KEY_FILE",
    os.path.join(os.path.dirname(__file__), '..', 'gcp-key.json'))
GCS_BUCKET = os.environ.get("GCS_BUCKET")

gcs_client = storage.Client.from_service_account_json(GCP_KEY_FILE)
bucket = gcs_client.bucket(GCS_BUCKET)

conn = mysql.connector.connect(
    host=os.environ.get("DB_HOSTNAME"),
    user=os.environ.get("DB_USERNAME"),
    passwd=os.environ.get("DB_PASSWORD"),
    db=os.environ.get("DB_NAME"),
    port=3306
)

cursor = conn.cursor()

cursor.execute("SELECT PhotoID, URL FROM photogallery")
all_photos = cursor.fetchall()

for photo in all_photos:
    photo_id = photo[0]
    url = photo[1]

    if "photos/" in url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        gcs_key = parsed.path.lstrip('/')

        try:
            blob = bucket.blob(gcs_key)
            blob.delete()
            print(f"Deleted {gcs_key} from GCS")
        except Exception as e:
            print(f"Error deleting {gcs_key} from GCS: {e}")

    cursor.execute("DELETE FROM photogallery WHERE PhotoID = %s", (photo_id,))
    print(f"Deleted photo ID {photo_id} from database")

conn.commit()
cursor.close()
conn.close()

print("Cleanup complete!")
