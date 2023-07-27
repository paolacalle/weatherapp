import git
from flask import Flask, render_template, url_for, flash, redirect, request, session
from forms import RegistrationForm, loginForm
from flask_behind_proxy import FlaskBehindProxy
import sqlite3
import bcrypt
import requests
import re

API_KEY = '297665b94cba0bb5002c9d0fb571cecc'
TEMPERATURE_THRESHOLD = 5  # Cities within this range of the desired temperature will be recommended


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

@app.route("/recommend", methods=['GET'])
def recommend():
    temperature = float(request.args.get('temperature', 20))  # Default to 20C if no temperature provided

    # List of cities to check weather
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Philadelphia']  # Replace with your list of cities

    recommended_cities = []
    for city in cities:
        # Get the current weather for the city
        response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric')
        data = response.json()

        # If the city's temperature is within the desired range, add it to the list of recommended cities
        city_temp = data['main']['temp']
        if abs(city_temp - temperature) <= TEMPERATURE_THRESHOLD:
            recommended_cities.append(city)

    return render_template('recommend.html', temperature=temperature, cities=recommended_cities)


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
        # Check if the password is at least 4 characters long
        if len(username) < 4:
            flash('Error: Username must be at least 4 characters long.', 'danger')
        if len(password) < 12:
            flash('Error: Password must be at least 12 characters long.', 'danger')

        elif not len(re.findall(r"[A-Z]", password)) >= 4:
            flash('Error: Password must have at least 4 upper letter.', 'danger')
        elif not len(re.findall(r"[a-z]", password)) >= 4:
            flash('Error: Password must have at least 4 lower letter.', 'danger')
        elif not len(re.findall(r"\d", password)) >= 3:
            flash('Error: Password must have at least 3 number.', 'danger')
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            flash('Error: Password must have at least one special character: !@#$%^&*(),.?\":}{|<>.', 'danger')
        else:
            hashed_password = hash_password(password)
            cursor.execute(insert_query, (username, email, hashed_password))
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

        if user is None: 
            flash('Invalid username.', 'danger')
            connection.close()
            return redirect(url_for('login'))
        # Check if a user with the provided username exists and if the password matches
        login_password = form.password.data
        hashed_password = user[3]
        
        if user and verify_password(hashed_password, login_password):  # Assuming password is stored in the fourth column (index 3)
            flash('Login successful!', 'success')
            connection.close()

            session['username'] = user[1] 

            return redirect(url_for('user_dashboard', username=user[1]))

        flash('Invalid username or password. Please try again.', 'danger')
        connection.close()
        return redirect(url_for('login'))
    return render_template('login.html', title='Login', form=form)

def hash_password(password):
    # Generate a random salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(hashed_password, password):
    # Verify the entered password against the stored hash
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

@app.route("/user_dashboard/<username>")
def user_dashboard(username):
    # You can retrieve user-specific data here based on the provided 'username'
    # For example, you can query the database to get user-specific information

    # Example: Retrieving user-specific data from the database
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    select_query = '''
        SELECT * FROM users WHERE username=?
    '''
    cursor.execute(select_query, (username,))
    user = cursor.fetchone()

    connection.close()

    return render_template('user_dashboard.html', title='User Dashboard', user=user)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
