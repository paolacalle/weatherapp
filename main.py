import git
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, loginForm
from flask_behind_proxy import FlaskBehindProxy
import sqlite3
import bcrypt
import requests



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

@app.route("/recommend", methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        state = request.form['state']
        desired_temp = float(request.form['temperature'])

        cities = {
            'New York': ['New York', 'Buffalo', 'Rochester'],
            'California': ['Los Angeles', 'San Francisco', 'San Diego'],
            'Texas': ['Houston', 'Dallas', 'Austin']
            # add more states and cities as needed
        }

        closest_city = None
        closest_temp_diff = float('inf')

        for city in cities.get(state, []):
            weather = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid=12d7632e8289198b000b09b0ec1e303e&units=imperial')
            data = weather.json()
            city_temp = data['main']['temp']

            temp_diff = abs(city_temp - desired_temp)

            if temp_diff < closest_temp_diff:
                closest_temp_diff = temp_diff
                closest_city = city

        return render_template('recommend.html', temperature=desired_temp, cities=closest_city)

    
    return render_template('recommend.html')



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
            flash('Error: Username must be at least 4 characters long.')
        if len(password) < 4:
            flash('Error: Password must be at least 4 characters long.')
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

        # Check if a user with the provided username exists and if the password matches
        login_password = form.password.data
        hashed_password = user[3]
        if user and verify_password(hashed_password, login_password):  # Assuming password is stored in the fourth column (index 3)
            flash('Login successful!', 'success')
            connection.close()
            return redirect(url_for('home'))

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

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
