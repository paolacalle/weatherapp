import git
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, loginForm
from flask_behind_proxy import FlaskBehindProxy
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
proxied = FlaskBehindProxy(app)  #to handle redirect in codio 

app.config['SECRET_KEY'] = "8ce4fcaac337fceeca98f8d9dddfd559"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(60), nullable=False)

  def __repr__(self):
    return f"User('{self.username}', '{self.email}')"

with app.app_context():
  db.create_all()

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
        # user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        # db.session.add(user)
        # db.session.commit()
        # print(user)
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit(): # checks if entries are valid
        # user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        # db.session.add(user)
        # db.session.commit()
        # print(user)
        flash(f'Welcome back {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")