from flask import Flask, render_template, request, redirect, session
from cryptography.fernet import Fernet
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key

# Read the encryption key from the file
with open('key.txt', 'rb') as key_file:
    key = key_file.read()

# MongoDB initialization
client = MongoClient('mongodb+srv://cyberKids:pXhoFAd8g3bGaZjv@cluster0.jeolobf.mongodb.net/?retryWrites=true&w=majority')
db = client['passwords']

def encrypt_password(password):
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(password.encode())
    return cipher_text

def decrypt_password(cipher_text):
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(cipher_text)
    return plain_text.decode()

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/dashboard')
    else:
        return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = db['users']
        users.insert_one({'username': username, 'password': password})

        # Create a collection for the user's passwords
        user_collection = db["user_"+username]
        user_collection.create_index('website', unique=True)

        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = db['users']
        user = users.find_one({'username': username})

        if user and password == user['password']:
            session['username'] = username

            # Store the user's password collection name in the session
            session['collection'] = username

            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        user_collection = db["user_"+username]
        passwords = user_collection.find({})
        return render_template('dashboard.html', username=username, passwords=passwords)
    else:
        return redirect('/login')

@app.route('/add_password', methods=['GET', 'POST'])
def add_password():
    if request.method == 'POST':
        website = request.form['website']
        username = request.form['username']
        password = request.form['password']

        encrypted_password = encrypt_password(password)

        user_collection = db["user_"+session['username']]
        user_collection.insert_one({'website': website, 'username': username, 'encrypted_password': encrypted_password})

        return redirect('/dashboard')
    else:
        username = session['username']
        return render_template('add_password.html', username=username)

@app.route('/view_password/<password_id>')
def view_password(password_id):
    user_collection = db["user_"+session['username']]
    password = user_collection.find_one({'_id': ObjectId(password_id)})
    decrypted_password = decrypt_password(password['encrypted_password'])

    return render_template('view_password.html', password=decrypted_password)

@app.route('/delete_password/<password_id>')
def delete_password(password_id):
    user_collection = db["user_"+session['username']]
    user_collection.delete_one({'_id': ObjectId(password_id)})

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
