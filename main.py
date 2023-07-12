import git
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, loginForm
from flask_behind_proxy import FlaskBehindProxy
import sqlite3

connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# Create a Table
create_table_query = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
'''
cursor.execute(create_table_query)
connection.close()

app = Flask(__name__)
proxied = FlaskBehindProxy(app)  #to handle redirect in codio 

app.config['SECRET_KEY'] = "8ce4fcaac337fceeca98f8d9dddfd559"

@app.route("/")
def home():
    #we call render_template instead of returning raw HTML -- this is where we point 
    #corresponding template .html file and 
    #pass the missing info 
    return render_template('home.html', subtitle='Welcome to Weather App.', text='This is the home page')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit(): # checks if entries are valid
        # Establish SQLite connection and cursor
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        # Check if username or email already exists in the database
        select_query = '''
            SELECT * FROM users WHERE username=? OR email=?
        '''
        cursor.execute(select_query, (form.username.data, form.email.data))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username or email already exists. Please choose a different username or email.', 'danger')
            connection.close()
            return redirect(url_for('register'))

        # Insert form data into "users" table
        insert_query = '''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        '''
        username = form.username.data
        email = form.email.data
        password = form.password.data
        cursor.execute(insert_query, (username, email, password))
        connection.commit()
        # Close the connection
        connection.close()

        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit(): # checks if entries are valid
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        # Retrieve user from the database based on the provided username
        select_query = '''
            SELECT * FROM users WHERE username=?
        '''
        cursor.execute(select_query, (form.username.data,))
        user = cursor.fetchone()

        # Check if a user with the provided username exists and if the password matches
        if user and user[3] == form.password.data:  # Assuming password is stored in the fourth column (index 3)
            flash('Login successful!', 'success')
            connection.close()
            return redirect(url_for('home'))

        flash('Invalid username or password. Please try again.', 'danger')
        connection.close()
        return redirect(url_for('login'))
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")