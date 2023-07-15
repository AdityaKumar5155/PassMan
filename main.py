from flask import Flask, render_template, request, redirect, session
from cryptography.fernet import Fernet
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key

# Read the encryption key from the file
with open('key.txt', 'rb') as key_file:
    key = key_file.read()

# Database initialization
conn = sqlite3.connect('passwords.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')
conn.commit()
conn.close()

def encrypt_password(password):
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(password.encode())
    return cipher_text

def decrypt_password(cipher_text):
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(cipher_text)
    return plain_text.decode()

def genPass():
    charset = [['a', 'b', 'c', 'd', 'e', 'f','g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'],['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],['0','1','2','3','4','5','6','7','8','9'],['!','@','#','$','%','^','&','*','(',')','~','`','=','<','>','/']]
    password = """"""
    for i in range(25):
        currSet=random.choice(charset)
        currChar=random.choice(currSet)
        password = password + currChar
    return password
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

        conn = sqlite3.connect('passwords.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        c.execute(f"CREATE TABLE IF NOT EXISTS passwords_{username} (id INTEGER PRIMARY KEY AUTOINCREMENT, website TEXT, username TEXT, encrypted_password TEXT)")
        conn.commit()
        conn.close()

        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('passwords.db')
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and password == user[1]:
            session['username'] = username
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        conn = sqlite3.connect('passwords.db')
        c = conn.cursor()
        c.execute(f"SELECT id, website, username FROM passwords_{username}")
        passwords = c.fetchall()
        conn.close()
        return render_template('dashboard.html', username=username, passwords=passwords)
    else:
        return redirect('/login')

@app.route('/add_password', methods=['GET', 'POST'])
def add_password():
    if request.method == 'POST':
        website = request.form['website']
        user_name = request.form['username']
        password = request.form['password']
        if password=="":
            password = genPass()
        username = session['username']
        encrypted_password = encrypt_password(password)

        conn = sqlite3.connect('passwords.db')
        c = conn.cursor()
        c.execute(f"INSERT INTO passwords_{username} (website, username, encrypted_password) VALUES (?, ?, ?)", (website, user_name, encrypted_password))
        conn.commit()
        conn.close()

        return redirect('/dashboard')
    else:
        return render_template('add_password.html')

@app.route('/view_password/<password_id>')
def view_password(password_id):
    username = session['username']
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute(f"SELECT encrypted_password FROM passwords_{username} WHERE id=?", (password_id,))
    encrypted_password = c.fetchone()[0]
    conn.close()

    password = decrypt_password(encrypted_password)

    return render_template('view_password.html', password=password)

@app.route('/delete_password/<password_id>')
def delete_password(password_id):
    username = session['username']
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM passwords_{username} WHERE id=?", (password_id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
