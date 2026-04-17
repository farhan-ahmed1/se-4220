'''
MIT License

Copyright (c) 2019 Arshdeep Bahga and Vijay Madisetti

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

# App Engine Standard (Python 3.12) entry point.
# gunicorn runs this as `main:app` automatically per app.yaml.

from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect, session, send_file
from functools import wraps
from flask_bcrypt import Bcrypt
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import os
import io
import uuid
import time
import datetime
import exifread
import json
import mysql.connector
from google.cloud import storage

db_config = {
    'host':   os.environ.get("DB_HOSTNAME"),
    'user':   os.environ.get("DB_USERNAME"),
    'passwd': os.environ.get("DB_PASSWORD"),
    'db':     os.environ.get("DB_NAME"),
    'port':   3306,
    # Give up quickly if the MySQL VM's firewall is blocking us,
    # instead of hanging the App Engine request for the full TCP timeout.
    'connection_timeout': 10,
}

GCP_KEY_FILE = os.environ.get("GCP_KEY_FILE", "gcp-key.json")
GCS_BUCKET   = os.environ.get("GCS_BUCKET")

# On App Engine Standard only /tmp is writable. We upload there,
# push to GCS, and delete the temp file immediately.
UPLOAD_FOLDER = "/tmp"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__, static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")
bcrypt = Bcrypt(app)

# Reuse a single GCS client across requests within the same instance.
_gcs_client = None


def get_gcs_client():
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client.from_service_account_json(GCP_KEY_FILE)
    return _gcs_client


def get_db():
    return mysql.connector.connect(**db_config)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def getExifData(path_name):
    with open(path_name, 'rb') as f:
        tags = exifread.process_file(f)
    ExifData = {}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail',
                       'Filename', 'EXIF MakerNote'):
            ExifData[str(tag)] = str(tags[tag])
    return ExifData


def gcs_upload(filename, filenameWithPath):
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(f"photos/{filename}")
    blob.upload_from_filename(filenameWithPath)
    blob.make_public()
    return blob.public_url


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE Username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['Password'], password):
            session['username'] = username
            return redirect('/')
        else:
            error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm  = request.form['confirm']

        if password != confirm:
            error = 'Passwords do not match.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE Username = %s", (username,))
            existing = cursor.fetchone()

            if existing:
                error = 'Username already exists.'
            else:
                hashed = bcrypt.generate_password_hash(password).decode('utf-8')
                cursor.execute(
                    "INSERT INTO users (Username, Password) VALUES (%s, %s)",
                    (username, hashed)
                )
                conn.commit()
                cursor.close()
                conn.close()
                return redirect('/login')

            cursor.close()
            conn.close()

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


@app.route('/', methods=['GET', 'POST'])
@login_required
def home_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM photogallery WHERE UserID = %s",
        (session['username'],)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    items = []
    for row in rows:
        items.append({
            'PhotoID':      row['PhotoID'],
            'CreationTime': row['CreationTime'],
            'Title':        row['Title'],
            'Description':  row['Description'],
            'Tags':         row['Tags'],
            'URL':          row['URL'],
        })
    return render_template('index.html', photos=items)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_photo():
    if request.method == 'POST':
        uploadedFileURL = ''
        file = request.files['imagefile']
        title = request.form['title']
        tags = request.form['tags']
        description = request.form['description']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            tmp_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(tmp_path)

            try:
                uploadedFileURL = gcs_upload(filename, tmp_path)
                ExifData = getExifData(tmp_path)
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

            ts = time.time()
            timestamp = datetime.datetime.\
                        fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            photo_id = str(uuid.uuid4())
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO photogallery
                   (PhotoID, UserID, CreationTime, Title, Description, Tags, URL, EXIF)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (photo_id, session['username'], timestamp,
                 title, description, tags, uploadedFileURL,
                 json.dumps(ExifData))
            )
            conn.commit()
            cursor.close()
            conn.close()

        return redirect('/')
    else:
        return render_template('form.html')


@app.route('/photo/<string:photoID>', methods=['GET'])
@login_required
def view_photo(photoID):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM photogallery WHERE PhotoID = %s AND UserID = %s",
        (photoID, session['username'])
    )
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if not item:
        abort(404)

    exif_data = {}
    if item['EXIF']:
        try:
            exif_data = json.loads(item['EXIF'])
        except (json.JSONDecodeError, TypeError):
            exif_data = {}

    photo = {
        'PhotoID':      item['PhotoID'],
        'CreationTime': item['CreationTime'],
        'Title':        item['Title'],
        'Description':  item['Description'],
        'Tags':         item['Tags'],
        'URL':          item['URL'],
        'ExifData':     exif_data,
    }
    tags     = photo['Tags'].split(',')
    exifdata = photo['ExifData']

    return render_template('photodetail.html', photo=photo,
                            tags=tags, exifdata=exifdata)


@app.route('/photo/<string:photoID>/download', methods=['GET'])
@login_required
def download_photo(photoID):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM photogallery WHERE PhotoID = %s AND UserID = %s",
        (photoID, session['username'])
    )
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if not item:
        abort(404)

    url = item['URL']
    parsed = urlparse(url)
    gcs_key = parsed.path.lstrip('/')
    # blob.public_url returns ".../<bucket>/<object-key>", so after stripping
    # the leading slash the bucket name is still prefixed to the path. Strip it
    # so we don't ask GCS for bucket/bucket/photos/file.jpg and get a 404.
    bucket_prefix = f"{GCS_BUCKET}/"
    if gcs_key.startswith(bucket_prefix):
        gcs_key = gcs_key[len(bucket_prefix):]
    filename = gcs_key.split('/')[-1]

    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(gcs_key)
    data = blob.download_as_bytes()

    return send_file(
        io.BytesIO(data),
        download_name=filename,
        as_attachment=True,
    )


@app.route('/search', methods=['GET'])
@login_required
def search_page():
    query = request.args.get('query', '')
    search_term = f"%{query}%"

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM photogallery
           WHERE Title LIKE %s OR Description LIKE %s OR Tags LIKE %s""",
        (search_term, search_term, search_term)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    items = []
    for row in rows:
        exif_data = {}
        if row['EXIF']:
            try:
                exif_data = json.loads(row['EXIF'])
            except (json.JSONDecodeError, TypeError):
                exif_data = {}

        items.append({
            'PhotoID':      row['PhotoID'],
            'CreationTime': row['CreationTime'],
            'Title':        row['Title'],
            'Description':  row['Description'],
            'Tags':         row['Tags'],
            'URL':          row['URL'],
            'ExifData':     exif_data,
        })
    return render_template('search.html', photos=items,
                            searchquery=query)


# Lightweight health check so `gcloud app deploy`'s startup probes
# (and any future uptime checks) don't touch MySQL.
@app.route('/_ah/warmup')
def warmup():
    return '', 200


# No app.run() block: App Engine Standard invokes gunicorn per app.yaml.
