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

#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect, session
from functools import wraps
from flask_bcrypt import Bcrypt
import os
import time
import datetime
import exifread
import json
import boto3  
import mysql.connector
import dotenv
dotenv.load_dotenv()

aws_acess_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION_NAME")

app = Flask(__name__, static_url_path="")
app.secret_key = 'photogallery-secret-key-4220'
bcrypt = Bcrypt(app)

UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
BASE_URL="http://localhost:5000/media/"
BUCKET_NAME="se4220-photo-gallery-team3-bucket"
DB_HOSTNAME="photogallerydb-instance.cbqcmomws8dc.us-east-2.rds.amazonaws.com"
DB_USERNAME = 'root'
DB_PASSWORD = 'password4220'
DB_NAME = 'photogallerydb'


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
    f = open(path_name, 'rb')
    tags = exifread.process_file(f)
    ExifData={}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 
                       'Filename', 'EXIF MakerNote'):
            key="%s"%(tag)
            val="%s"%(tags[tag])
            ExifData[key]=val
    return ExifData

def s3uploading(filename, filenameWithPath):
    s3 = boto3.client('s3', aws_access_key_id=aws_acess_key,
                            aws_secret_access_key=aws_secret)
                       
    bucket = BUCKET_NAME
    path_filename = "photos/" + filename
    print(path_filename)
    s3.upload_file(filenameWithPath, bucket, path_filename)  
    s3.put_object_acl(ACL='public-read', 
                Bucket=bucket, Key=path_filename)

    return f"https://{bucket}.s3.us-east-2.amazonaws.com/{path_filename}"

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

        conn = mysql.connector.connect(host=DB_HOSTNAME,
                    user=DB_USERNAME, passwd=DB_PASSWORD,
                    db=DB_NAME, port=3306)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE Username=%s;", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
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
        confirm = request.form['confirm']

        if password != confirm:
            error = 'Passwords do not match.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            conn = mysql.connector.connect(host=DB_HOSTNAME,
                        user=DB_USERNAME, passwd=DB_PASSWORD,
                        db=DB_NAME, port=3306)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE Username=%s;", (username,))
            existing = cursor.fetchone()

            if existing:
                conn.close()
                error = 'Username already exists.'
            else:
                hashed = bcrypt.generate_password_hash(password).decode('utf-8')
                cursor.execute("INSERT INTO users (Username, Password) VALUES (%s, %s);",
                               (username, hashed))
                conn.commit()
                conn.close()
                return redirect('/login')

    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/', methods=['GET', 'POST'])
@login_required
def home_page():
    conn = mysql.connector.connect (host = DB_HOSTNAME,
                        user = DB_USERNAME,
                        passwd = DB_PASSWORD,
                        db = DB_NAME, 
            port = 3306)
    cursor = conn.cursor ()
    cursor.execute("SELECT * FROM photogallerydb.photogallery2;")
    results = cursor.fetchall()
    
    items=[]
    for item in results:
        photo={}
        photo['PhotoID'] = item[0]
        photo['CreationTime'] = item[1]
        photo['Title'] = item[2]
        photo['Description'] = item[3]
        photo['Tags'] = item[4]
        photo['URL'] = item[5]
        items.append(photo)
    conn.close()        
    print(items)
    return render_template('index.html', photos=items)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_photo():
    if request.method == 'POST':    
        uploadedFileURL=''
        file = request.files['imagefile']
        title = request.form['title']
        tags = request.form['tags']
        description = request.form['description']

        print(title,tags,description)
        if file and allowed_file(file.filename):
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            print(filenameWithPath)
            file.save(filenameWithPath)            
            uploadedFileURL = s3uploading(filename, filenameWithPath)
            ExifData=getExifData(filenameWithPath)
            print(ExifData)
            ts=time.time()
            timestamp = datetime.datetime.\
                        fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            conn = mysql.connector.connect (host = DB_HOSTNAME,
                        user = DB_USERNAME,
                        passwd = DB_PASSWORD,
                        db = DB_NAME, 
            port = 3306)
            cursor = conn.cursor ()

            statement = "INSERT INTO photogallerydb.photogallery2 \
                        (CreationTime,Title,Description,Tags,URL,EXIF) \
                        VALUES ("+\
                        "'"+str(timestamp)+"', '"+\
                        title+"', '"+\
                        description+"', '"+\
                        tags+"', '"+\
                        uploadedFileURL+"', '"+\
                        json.dumps(ExifData)+"');"
            
            print(statement)
            result = cursor.execute(statement)
            conn.commit()
            conn.close()

        return redirect('/')
    else:
        return render_template('form.html')

@app.route('/<int:photoID>', methods=['GET'])
@login_required
def view_photo(photoID):    
    conn = mysql.connector.connect (host = DB_HOSTNAME,
                        user = DB_USERNAME,
                        passwd = DB_PASSWORD,
                        db = DB_NAME, 
            port = 3306)
    cursor = conn.cursor ()

    cursor.execute("SELECT * FROM photogallerydb.photogallery2 \
                    WHERE PhotoID="+str(photoID)+";")

    results = cursor.fetchall()

    items=[]
    for item in results:
        photo={}
        photo['PhotoID'] = item[0]
        photo['CreationTime'] = item[1]
        photo['Title'] = item[2]
        photo['Description'] = item[3]
        photo['Tags'] = item[4]
        photo['URL'] = item[5]
        photo['ExifData']=json.loads(item[6])
        items.append(photo)
    conn.close()        
    tags=items[0]['Tags'].split(',')
    exifdata=items[0]['ExifData']
    
    return render_template('photodetail.html', photo=items[0], 
                            tags=tags, exifdata=exifdata)

@app.route('/search', methods=['GET'])
@login_required
def search_page():
    query = request.args.get('query', None)    
    conn = mysql.connector.connect (host = DB_HOSTNAME,
                        user = DB_USERNAME,
                        passwd = DB_PASSWORD,
                        db = DB_NAME, 
            port = 3306)
    cursor = conn.cursor ()
    
    cursor.execute("SELECT * FROM photogallerydb.photogallery2 \
                    WHERE Title LIKE '%"+query+ "%' \
                    UNION SELECT * FROM \
                    photogallerydb.photogallery2 WHERE \
                    Description LIKE '%"+query+ "%' UNION \
                    SELECT * FROM photogallerydb.photogallery2 \
                    WHERE Tags LIKE '%"+query+"%' ;")

    results = cursor.fetchall()

    items=[]
    for item in results:
        photo={}
        photo['PhotoID'] = item[0]
        photo['CreationTime'] = item[1]
        photo['Title'] = item[2]
        photo['Description'] = item[3]
        photo['Tags'] = item[4]
        photo['URL'] = item[5]
        photo['ExifData']=item[6]
        items.append(photo)
    conn.close()        
    print(items)
    return render_template('search.html', photos=items, 
                            searchquery=query)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
