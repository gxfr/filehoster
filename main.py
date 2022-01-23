from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, abort
from werkzeug.utils import secure_filename
from string import ascii_letters, digits
import random, json, pathlib, uuid, os, mysql.connector, yaml
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def make_id(num):
    return ''.join([random.choice(ascii_letters+digits) for n in range(num)])

def abspath(path):
    return os.path.dirname(os.path.abspath(__file__)) + path

with open(abspath("/config.yaml")) as configuration:
    config = yaml.safe_load(configuration)
    trim_blocks = config["trim_blocks"]
    lstrip_blocks = config["lstrip_blocks"]
    host = config["host"]
    user = config["user"]
    password = config["password"]
    database = config["database"]
    extensions = config["extensions"]
    port = config["port"]
    debug = config["debug"]
    default_limits = config["default_limits"]

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex
app.jinja_env.trim_blocks = trim_blocks
app.jinja_env.lstrip_blocks = lstrip_blocks
limiter = Limiter(app, key_func=get_remote_address, default_limits=default_limits)
db = mysql.connector.connect(host = host, user = user, password = password, database = database)
mycursor = db.cursor(buffered = True)
mycursor.execute("CREATE TABLE IF NOT EXISTS collections (cid VARCHAR(255), iids VARCHAR(255))")
if not os.path.exists(abspath('/files/')):
    os.mkdir(abspath('/files/'))
    
@app.errorhandler(HTTPException)
def error_handler(e):
    return render_template('error.html.jinja',error=e), e.code

@limiter.limit("6/minute")
@app.get('/')
def index():
    return render_template('index.html.jinja')

@limiter.limit("6/minute")
@app.get('/files/<file>')
def view_file(file):
    return send_from_directory(abspath('/files/'), file)

@limiter.limit("6/minute")
@app.get('/c/<cid>')
def collection(cid):
    mycursor.execute(f"SELECT * FROM collections WHERE cid ='{cid}';")
    s = [x for x in mycursor]
    t = s[0][1]
    ids = t.replace(']','').replace('[','').replace("'",'').replace(',', ' ').split()#i have no idea what i am doing
    return render_template('collection.html.jinja', collection = ids, cid = cid)

@limiter.limit("2/minute")
@app.post('/upload')
def upload_files():
    if 'file' not in request.files:
        flash('no file part')
        return redirect('/')
    files = request.files.getlist('file')
    if files[0].filename == '':
        flash('no file selected')
        return redirect('/')
    x = 0
    ids = []
    for file in files:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            extension = filename.split('.')[-1]
            idname = f"{make_id(15)}.{extension}"
            file.save(abspath('/files/') + idname)
            ids.append(idname)
            x += 1
    if x == 1:
        return redirect('/files/' + idname)
    collectionid = make_id(20)
    sql = "INSERT INTO collections (cid, iids) VALUES (%s, %s)"
    val = (collectionid, str(ids))
    mycursor.execute(sql, val)
    db.commit()
    return redirect('/c/' + collectionid)

if __name__ == "__main__":
    app.run(host = host, port = port, debug = debug)