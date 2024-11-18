from flask import Flask, render_template, request, redirect, flash, jsonify
import hashlib
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import datetime
from waitress import serve



app = Flask(__name__)
app.secret_key = 'ThisIsMyReallyLongSecret#ey'

# Initialize Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'json/myutils-437714-bd0d0a3e77bd.json'  # Update this path
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

USERS_SHEET_ID = '1_YhYay1XVZ9rvVUf85vZR-ZpSbwdkDoP_b-CWCfklso'
USERS_RANGE_NAME = 'USERS!A2:E' 


def encrypt_with_hash(input_string):
    """Encrypts a string using SHA-256 hashing (deterministic)."""
    return hashlib.sha256(input_string.encode()).hexdigest()

def get_user(username):
    #"""Read all users from the JSON file."""
    # with open(DATA_FILE, "r") as file:
    #     return json.load(file)
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=USERS_SHEET_ID, range=USERS_RANGE_NAME).execute()
    values = result.get('values', [])
    filtered_values = [row for row in values if row and row[0] >= username]
    return filtered_values

def write_user(username,passwordhash,lastlogin,token):
    #"""Write users to the JSON file."""
    
    # with open(DATA_FILE, "w") as file:
    #     json.dump(users, file, indent=4)
    #Insert user into GSheet
    values = [[username, passwordhash, lastlogin, token]]  
    service = build('sheets', 'v4', credentials=creds)
        
    print(values)
    body = {
        'values': values
    }
    service.spreadsheets().values().append(
        spreadsheetId=USERS_SHEET_ID,
        range=USERS_RANGE_NAME,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()


#Next step - Use the Sasthas Hub Users sheet to add manage access
#future step - Generate a token and save it to session to be used by selected apps while connecting from nginx


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        #email = request.form['email']
        password = request.form['password']

        if not username or not password:
            flash("All fields are required!", "danger")
            return redirect('/register')

        user = get_user(username)
        if user:
            flash("User already exists!", "warning")
            return redirect('/register')

        hashed_password = encrypt_with_hash(password)
        
        write_user(username,hashed_password,"","")

        flash("Registration successful!", "success")
        return redirect('/login')

    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def redirect():
    return render_template('login.html', message="")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return render_template('login.html', message="All fields are required!")
            
        iuser = get_user(username)
        hashed_password = encrypt_with_hash(password)

        if iuser and iuser[0][1] == hashed_password:
            return render_template('landing.html', message="Login successful!")
        else:
            return render_template('login.html', message="Invalid Username or Password. Retry !!!")
            

 

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
