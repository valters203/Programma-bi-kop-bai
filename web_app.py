from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
import sqlite3
import os
from datetime import datetime
import shutil
import pandas as pd
from io import BytesIO

import bcrypt
import time
from functools import wraps
from flask import session

import urllib.request
import urllib.error
import json

app = Flask(__name__)
app.secret_key = 'beekeeping_secret_key'

# Database setup
def create_database():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Users table first
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Check if admin user exists, if not create it
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_password_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('admin', admin_password_hash))
    
    # Apiaries table
    c.execute('''CREATE TABLE IF NOT EXISTS apiaries (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT,
                    latitude REAL,
                    longitude REAL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
    
    # Apiary visits table
    c.execute('''CREATE TABLE IF NOT EXISTS apiary_visits (
                    id INTEGER PRIMARY KEY,
                    apiary_id INTEGER,
                    visit_date TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (apiary_id) REFERENCES apiaries (id)
                )''')
    
    # Beehives table
    c.execute('''CREATE TABLE IF NOT EXISTS beehives (
                    id INTEGER PRIMARY KEY,
                    apiary_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    image_path TEXT,
                    FOREIGN KEY (apiary_id) REFERENCES apiaries (id)
                )''')
    
    # Honey harvests table
    c.execute('''CREATE TABLE IF NOT EXISTS honey_harvests (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    honey_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    money_earned REAL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
    
    # Recipes table
    c.execute('''CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
    
    # Ingredients table
    c.execute('''CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Recipe ingredients table
    c.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    id INTEGER PRIMARY KEY,
                    recipe_id INTEGER,
                    ingredient_id INTEGER,
                    quantity REAL NOT NULL,
                    unit TEXT,
                    FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
                )''')
    
    # Add unit column if not exists (for upgrades)
    try:
        c.execute("ALTER TABLE recipe_ingredients ADD COLUMN unit TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add yield column to recipes if not exists
    try:
        c.execute("ALTER TABLE recipes ADD COLUMN yield REAL NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add yield_unit column to recipes if not exists
    try:
        c.execute("ALTER TABLE recipes ADD COLUMN yield_unit TEXT DEFAULT 'units'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add location column to apiaries if not exists
    try:
        c.execute("ALTER TABLE apiaries ADD COLUMN location TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add latitude column to apiaries if not exists
    try:
        c.execute("ALTER TABLE apiaries ADD COLUMN latitude REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add longitude column to apiaries if not exists
    try:
        c.execute("ALTER TABLE apiaries ADD COLUMN longitude REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add user_id column to apiaries if not exists
    try:
        c.execute("ALTER TABLE apiaries ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add user_id column to honey_harvests if not exists
    try:
        c.execute("ALTER TABLE honey_harvests ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add user_id column to recipes if not exists
    try:
        c.execute("ALTER TABLE recipes ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add user_id column to ingredients if not exists
    try:
        c.execute("ALTER TABLE ingredients ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()

create_database()

# Ensure images directory exists
if not os.path.exists('images'):
    os.makedirs('images')

def get_weather_forecast(lat=56.97, lon=21.96):
    """Fetch weather from Open-Meteo for the given coordinates (Kuldīga)."""
    api_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current_weather=true&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=auto"
    )
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = response.read().decode('utf-8')
            weather = json.loads(data)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        return {
            'error': 'Unable to fetch weather data at this time.',
            'details': str(e)
        }

    return {
        'current': weather.get('current_weather', {}),
        'daily': weather.get('daily', {}),
        'timezone': weather.get('timezone', 'UTC'),
        'location': {
            'latitude': lat,
            'longitude': lon
        }
    }

@app.before_request
def require_login():
    allowed = {"login", "register", "logout", "static", "serve_image"}  # names of view functions that don't require auth
    # request.endpoint is the view function name (e.g. "login")
    if request.endpoint not in allowed and not session.get("logged_in"):
        return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def login():
    # if already logged in, send to admin home
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check users table
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and password and bcrypt.checkpw(password.encode(), user[1]):
            session["logged_in"] = True
            session["username"] = username
            session["user_id"] = user[0]
            session["is_admin"] = (username == 'admin')
            return redirect(url_for("index"))
        else:
            time.sleep(2)  # slows brute-force
            flash("Invalid username or password")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not username or not password:
            flash("Username and password are required")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long")
            return render_template("register.html")

        # Hash the password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        try:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            conn.close()
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists")
            return render_template("register.html")

    return render_template("register.html")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/home")
@login_required
def index():
    # Default coordinates are for Riga; change producer location if needed.
    weather = get_weather_forecast(lat=56.95, lon=24.11)

    daily_count = 0
    if weather and not weather.get('error'):
        daily = weather.get('daily', {})
        days = daily.get('time', []) if isinstance(daily.get('time', []), list) else []
        daily_count = min(len(days), 3)

    return render_template("index.html", weather=weather, daily_count=daily_count)

@app.route("/dashboard")
@login_required
def dashboard():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    user_id = session['user_id']
    
    # Total apiaries
    c.execute("SELECT COUNT(*) FROM apiaries WHERE user_id = ?", (user_id,))
    total_apiaries = c.fetchone()[0]
    
    # Total beehives
    c.execute("""
        SELECT COUNT(*) FROM beehives 
        WHERE apiary_id IN (SELECT id FROM apiaries WHERE user_id = ?)
    """, (user_id,))
    total_beehives = c.fetchone()[0]
    
    # Total visits
    c.execute("""
        SELECT COUNT(*) FROM apiary_visits 
        WHERE apiary_id IN (SELECT id FROM apiaries WHERE user_id = ?)
    """, (user_id,))
    total_visits = c.fetchone()[0]
    
    # Total honey harvested
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM honey_harvests WHERE user_id = ?", (user_id,))
    total_honey = c.fetchone()[0]
    
    # Total income
    c.execute("SELECT COALESCE(SUM(money_earned), 0) FROM honey_harvests WHERE user_id = ?", (user_id,))
    total_income = c.fetchone()[0]
    
    # Latest visit
    c.execute("""
        SELECT visit_date, notes FROM apiary_visits 
        WHERE apiary_id IN (SELECT id FROM apiaries WHERE user_id = ?) 
        ORDER BY visit_date DESC LIMIT 1
    """, (user_id,))
    latest_visit_row = c.fetchone()
    latest_visit = {'date': latest_visit_row[0], 'notes': latest_visit_row[1]} if latest_visit_row else None
    
    # Latest harvest
    c.execute("SELECT date, honey_type, amount FROM honey_harvests WHERE user_id = ? ORDER BY date DESC LIMIT 1", (user_id,))
    latest_harvest_row = c.fetchone()
    latest_harvest = {'date': latest_harvest_row[0], 'type': latest_harvest_row[1], 'amount': latest_harvest_row[2]} if latest_harvest_row else None
    
    conn.close()
    
    return render_template("statistics.html", 
                           total_apiaries=total_apiaries,
                           total_beehives=total_beehives,
                           total_visits=total_visits,
                           total_honey=total_honey,
                           total_income=total_income,
                           latest_visit=latest_visit,
                           latest_harvest=latest_harvest)

@app.route('/apiaries')
@login_required
def apiaries():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("""
        SELECT a.id, a.name, a.location, a.latitude, a.longitude, MAX(av.visit_date) as last_visit
        FROM apiaries a
        LEFT JOIN apiary_visits av ON a.id = av.apiary_id
        WHERE a.user_id = ?
        GROUP BY a.id, a.name, a.location, a.latitude, a.longitude
        ORDER BY a.name
    """, (session['user_id'],))
    apiaries_list = c.fetchall()
    conn.close()
    return render_template('apiaries.html', apiaries=apiaries_list)

@app.route('/apiaries/add', methods=['GET', 'POST'])
@login_required
def add_apiary():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("INSERT INTO apiaries (user_id, name, location, latitude, longitude) VALUES (?, ?, ?, ?, ?)", (session['user_id'], name, location, lat, lng))
        conn.commit()
        conn.close()
        flash('Apiary added successfully!')
        return redirect(url_for('apiaries'))
    return render_template('add_apiary.html')

@app.route('/apiaries/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_apiary(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Check if apiary belongs to current user
    c.execute("SELECT user_id FROM apiaries WHERE id = ?", (id,))
    apiary_owner = c.fetchone()
    if not apiary_owner or apiary_owner[0] != session['user_id']:
        conn.close()
        flash('Access denied')
        return redirect(url_for('apiaries'))
    
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
        c.execute("UPDATE apiaries SET name = ?, location = ?, latitude = ?, longitude = ? WHERE id = ? AND user_id = ?", (name, location, lat, lng, id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Apiary updated successfully!')
        return redirect(url_for('apiaries'))
    c.execute("SELECT name, location, latitude, longitude FROM apiaries WHERE id = ? AND user_id = ?", (id, session['user_id']))
    apiary = c.fetchone()
    conn.close()
    return render_template('edit_apiary.html', apiary=apiary, id=id)

@app.route('/apiaries/delete/<int:id>')
@login_required
def delete_apiary(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Check if apiary belongs to current user
    c.execute("SELECT user_id FROM apiaries WHERE id = ?", (id,))
    apiary_owner = c.fetchone()
    if not apiary_owner or apiary_owner[0] != session['user_id']:
        conn.close()
        flash('Access denied')
        return redirect(url_for('apiaries'))
    
    c.execute("DELETE FROM beehives WHERE apiary_id = ?", (id,))
    c.execute("DELETE FROM apiaries WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Apiary deleted successfully!')
    return redirect(url_for('apiaries'))

@app.route('/apiaries/mark_visit/<int:apiary_id>', methods=['GET', 'POST'])
def mark_visit(apiary_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT name, location, latitude, longitude FROM apiaries WHERE id = ?", (apiary_id,))
    apiary = c.fetchone()
    apiary_name = apiary[0]
    apiary_location = apiary[1]
    apiary_lat = apiary[2]
    apiary_lng = apiary[3]
    conn.close()
    
    if request.method == 'POST':
        visit_date = request.form['visit_date']
        notes = request.form.get('notes', '')
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("INSERT INTO apiary_visits (apiary_id, visit_date, notes) VALUES (?, ?, ?)", (apiary_id, visit_date, notes))
        conn.commit()
        conn.close()
        flash('Visit marked successfully!')
        return redirect(url_for('apiaries'))
    
    return render_template('mark_visit.html', apiary_name=apiary_name, apiary_location=apiary_location, apiary_lat=apiary_lat, apiary_lng=apiary_lng, apiary_id=apiary_id, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/apiaries/<int:apiary_id>/visits')
def view_visit_history(apiary_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT name, location, latitude, longitude FROM apiaries WHERE id = ?", (apiary_id,))
    apiary = c.fetchone()
    apiary_name = apiary[0]
    apiary_location = apiary[1]
    apiary_lat = apiary[2]
    apiary_lng = apiary[3]
    c.execute("SELECT visit_date, notes FROM apiary_visits WHERE apiary_id = ? ORDER BY visit_date DESC", (apiary_id,))
    visits = c.fetchall()
    conn.close()
    return render_template('visit_history.html', apiary_name=apiary_name, apiary_location=apiary_location, apiary_lat=apiary_lat, apiary_lng=apiary_lng, visits=visits, apiary_id=apiary_id)
@app.route('/apiaries/<int:apiary_id>')
@login_required
def view_apiary(apiary_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT name, location, latitude, longitude FROM apiaries WHERE id = ? AND user_id = ?", (apiary_id, session['user_id']))
    apiary = c.fetchone()
    if not apiary:
        conn.close()
        flash('Access denied')
        return redirect(url_for('apiaries'))
    
    apiary_name = apiary[0]
    apiary_location = apiary[1]
    apiary_lat = apiary[2]
    apiary_lng = apiary[3]
    c.execute("SELECT id, name, description, image_path FROM beehives WHERE apiary_id = ?", (apiary_id,))
    beehives = c.fetchall()
    conn.close()
    return render_template('beehives.html', apiary_name=apiary_name, apiary_location=apiary_location, apiary_lat=apiary_lat, apiary_lng=apiary_lng, beehives=beehives, apiary_id=apiary_id)

@app.route('/beehives/add/<int:apiary_id>', methods=['GET', 'POST'])
def add_beehive(apiary_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        image = request.files.get('image')
        image_path = None
        if image and image.filename:
            filename = f"{apiary_id}_{name}_{image.filename}"
            image_path = os.path.join('images', filename)
            image.save(image_path)
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("INSERT INTO beehives (apiary_id, name, description, image_path) VALUES (?, ?, ?, ?)", 
                  (apiary_id, name, description, image_path))
        conn.commit()
        conn.close()
        flash('Beehive added successfully!')
        return redirect(url_for('view_apiary', apiary_id=apiary_id))
    return render_template('add_beehive.html', apiary_id=apiary_id)

@app.route('/beehives/edit/<int:id>', methods=['GET', 'POST'])
def edit_beehive(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        image = request.files.get('image')
        image_path = None
        if image and image.filename:
            filename = f"beehive_{id}_{image.filename}"
            image_path = os.path.join('images', filename)
            image.save(image_path)
            c.execute("UPDATE beehives SET image_path = ? WHERE id = ?", (image_path, id))
        c.execute("UPDATE beehives SET name = ?, description = ? WHERE id = ?", (name, description, id))
        conn.commit()
        flash('Beehive updated successfully!')
        # Get apiary_id to redirect (before closing connection)
        c.execute("SELECT apiary_id FROM beehives WHERE id = ?", (id,))
        apiary_id = c.fetchone()[0]
        conn.close()
        return redirect(url_for('view_apiary', apiary_id=apiary_id))
    c.execute("SELECT name, description FROM beehives WHERE id = ?", (id,))
    beehive = c.fetchone()
    # Get apiary_id for the template
    c.execute("SELECT apiary_id FROM beehives WHERE id = ?", (id,))
    apiary_id = c.fetchone()[0]
    conn.close()
    return render_template('edit_beehive.html', beehive=beehive, id=id, apiary_id=apiary_id)

@app.route('/beehives/delete/<int:id>')
def delete_beehive(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT apiary_id FROM beehives WHERE id = ?", (id,))
    apiary_id = c.fetchone()[0]
    c.execute("DELETE FROM beehives WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Beehive deleted successfully!')
    return redirect(url_for('view_apiary', apiary_id=apiary_id))

@app.route('/harvests')
@login_required
def harvests():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT id, date, honey_type, amount, money_earned FROM honey_harvests WHERE user_id = ? ORDER BY date DESC", (session['user_id'],))
    harvests_list = c.fetchall()
    conn.close()
    return render_template('harvests.html', harvests=harvests_list)

@app.route('/harvests/add', methods=['GET', 'POST'])
@login_required
def add_harvest():
    if request.method == 'POST':
        date = request.form['date']
        honey_type = request.form['honey_type']
        amount = float(request.form['amount'])
        money_earned_str = request.form.get('money_earned', '').strip()
        money_earned = float(money_earned_str) if money_earned_str else 0
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("INSERT INTO honey_harvests (user_id, date, honey_type, amount, money_earned) VALUES (?, ?, ?, ?, ?)", 
                  (session['user_id'], date, honey_type, amount, money_earned))
        conn.commit()
        conn.close()
        flash('Harvest added successfully!')
        return redirect(url_for('harvests'))
    return render_template('add_harvest.html', current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/harvests/edit/<int:id>', methods=['GET', 'POST'])
def edit_harvest(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    if request.method == 'POST':
        date = request.form['date']
        honey_type = request.form['honey_type']
        amount = float(request.form['amount'])
        money_earned_str = request.form.get('money_earned', '').strip()
        money_earned = float(money_earned_str) if money_earned_str else 0
        c.execute("UPDATE honey_harvests SET date=?, honey_type=?, amount=?, money_earned=? WHERE id=?", 
                  (date, honey_type, amount, money_earned, id))
        conn.commit()
        conn.close()
        flash('Harvest updated successfully!')
        return redirect(url_for('harvests'))
    c.execute("SELECT date, honey_type, amount, money_earned FROM honey_harvests WHERE id = ?", (id,))
    harvest = c.fetchone()
    conn.close()
    return render_template('edit_harvest.html', harvest=harvest, id=id)

@app.route('/harvests/delete/<int:id>')
def delete_harvest(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("DELETE FROM honey_harvests WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash('Harvest deleted successfully!')
    return redirect(url_for('harvests'))

@app.route('/recipes')
@login_required
def recipes():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT id, name, yield, yield_unit FROM recipes WHERE user_id = ? ORDER BY name", (session['user_id'],))
    recipes_list = c.fetchall()
    conn.close()
    return render_template('recipes.html', recipes=recipes_list)

@app.route('/recipes/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'POST':
        name = request.form['name']
        yield_amount = float(request.form.get('yield', 1))
        yield_unit = request.form.get('yield_unit', 'units')
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("INSERT INTO recipes (user_id, name, yield, yield_unit) VALUES (?, ?, ?, ?)", (session['user_id'], name, yield_amount, yield_unit))
        conn.commit()
        conn.close()
        flash('Recipe added successfully!')
        return redirect(url_for('recipes'))
    return render_template('add_recipe.html')

@app.route('/recipes/edit/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        yield_amount = float(request.form.get('yield', 1))
        yield_unit = request.form.get('yield_unit', 'units')
        c.execute("UPDATE recipes SET name = ?, yield = ?, yield_unit = ? WHERE id = ?", (name, yield_amount, yield_unit, id))
        conn.commit()
        conn.close()
        flash('Recipe updated successfully!')
        return redirect(url_for('recipes'))
    c.execute("SELECT name, yield, yield_unit FROM recipes WHERE id = ?", (id,))
    recipe = c.fetchone()
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe, id=id)

@app.route('/recipes/delete/<int:id>')
def delete_recipe(id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT id FROM recipes WHERE id = ?", (id,))
    recipe_id = id
    c.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()
    flash('Recipe deleted successfully!')
    return redirect(url_for('recipes'))

@app.route('/recipes/<int:recipe_id>')
def view_recipe(recipe_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT name, yield, yield_unit FROM recipes WHERE id = ?", (recipe_id,))
    recipe_data = c.fetchone()
    recipe_name = recipe_data[0]
    recipe_yield = recipe_data[1]
    recipe_yield_unit = recipe_data[2]
    c.execute("""SELECT i.id, i.name, ri.quantity, ri.unit FROM recipe_ingredients ri
                 JOIN ingredients i ON ri.ingredient_id = i.id
                 WHERE ri.recipe_id = ?""", (recipe_id,))
    ingredients = c.fetchall()
    conn.close()
    return render_template('ingredients.html', recipe_name=recipe_name, ingredients=ingredients, recipe_id=recipe_id, recipe_yield=recipe_yield, recipe_yield_unit=recipe_yield_unit)

@app.route('/ingredients/add/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def add_ingredient(recipe_id):
    # Check if recipe belongs to user
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM recipes WHERE id = ?", (recipe_id,))
    recipe_owner = c.fetchone()
    if not recipe_owner or recipe_owner[0] != session['user_id']:
        conn.close()
        flash('Access denied')
        return redirect(url_for('recipes'))
    
    if request.method == 'POST':
        ing_name = request.form['name']
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
        # Check if ingredient exists for this user
        c.execute("SELECT id FROM ingredients WHERE name = ? AND user_id = ?", (ing_name, session['user_id']))
        ing_id = c.fetchone()
        if not ing_id:
            c.execute("INSERT INTO ingredients (user_id, name) VALUES (?, ?)", (session['user_id'], ing_name))
            ing_id = c.lastrowid
        else:
            ing_id = ing_id[0]
        # Add to recipe
        c.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (?, ?, ?, ?)", (recipe_id, ing_id, quantity, unit))
        conn.commit()
        conn.close()
        flash('Ingredient added successfully!')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    conn.close()
    return render_template('add_ingredient.html', recipe_id=recipe_id)

@app.route('/ingredients/edit/<int:recipe_id>/<int:ing_id>', methods=['GET', 'POST'])
def edit_ingredient(recipe_id, ing_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    if request.method == 'POST':
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
        c.execute("UPDATE recipe_ingredients SET quantity = ?, unit = ? WHERE recipe_id = ? AND ingredient_id = ?", (quantity, unit, recipe_id, ing_id))
        conn.commit()
        conn.close()
        flash('Ingredient updated successfully!')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    c.execute("SELECT i.name, ri.quantity, ri.unit FROM recipe_ingredients ri JOIN ingredients i ON ri.ingredient_id = i.id WHERE ri.recipe_id = ? AND ri.ingredient_id = ?", (recipe_id, ing_id))
    ingredient = c.fetchone()
    conn.close()
    return render_template('edit_ingredient.html', ingredient=ingredient, recipe_id=recipe_id, ing_id=ing_id)

@app.route('/ingredients/delete/<int:recipe_id>/<int:ing_id>')
def delete_ingredient(recipe_id, ing_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ? AND ingredient_id = ?", (recipe_id, ing_id))
    conn.commit()
    conn.close()
    flash('Ingredient deleted successfully!')
    return redirect(url_for('view_recipe', recipe_id=recipe_id))

@app.route('/calculate/<int:recipe_id>', methods=['GET', 'POST'])
def calculate_production(recipe_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT name, yield, yield_unit FROM recipes WHERE id = ?", (recipe_id,))
    recipe_data = c.fetchone()
    recipe_name = recipe_data[0]
    recipe_yield = recipe_data[1]
    recipe_yield_unit = recipe_data[2]
    c.execute("""SELECT i.name, ri.quantity, ri.unit FROM recipe_ingredients ri
                 JOIN ingredients i ON ri.ingredient_id = i.id
                 WHERE ri.recipe_id = ?""", (recipe_id,))
    ingredients = c.fetchall()
    conn.close()
    if request.method == 'POST':
        available = {}
        for ing in ingredients:
            name, req, unit = ing
            avail = float(request.form.get(f'avail_{name}', 0))
            available[name] = avail / req if req > 0 else 0
        max_prod = min(available.values()) if available else 0
        max_prod *= recipe_yield  # Multiply by yield to get actual product amount
        return render_template('calculate.html', recipe_name=recipe_name, ingredients=ingredients, max_prod=max_prod, recipe_id=recipe_id, recipe_yield=recipe_yield, recipe_yield_unit=recipe_yield_unit)
    return render_template('calculate.html', recipe_name=recipe_name, ingredients=ingredients, max_prod=None, recipe_id=recipe_id, recipe_yield=recipe_yield, recipe_yield_unit=recipe_yield_unit)

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

@app.route('/export/apiaries')
@login_required
def export_apiaries():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    # Get apiaries with their hives
    c.execute("""
        SELECT a.name as apiary_name, a.location, a.latitude, a.longitude, b.name as hive_name, b.description, b.image_path
        FROM apiaries a
        LEFT JOIN beehives b ON a.id = b.apiary_id
        WHERE a.user_id = ?
        ORDER BY a.name, b.name
    """, (session['user_id'],))
    apiaries_data = c.fetchall()
    
    # Get visits
    c.execute("""
        SELECT a.name as apiary_name, a.location, a.latitude, a.longitude, av.visit_date, av.notes
        FROM apiaries a
        JOIN apiary_visits av ON a.id = av.apiary_id
        WHERE a.user_id = ?
        ORDER BY a.name, av.visit_date DESC
    """, (session['user_id'],))
    visits_data = c.fetchall()
    
    conn.close()
    
    apiaries_df = pd.DataFrame(apiaries_data, columns=['Apiary Name', 'Location', 'Latitude', 'Longitude', 'Hive Name', 'Hive Description', 'Image Path'])
    visits_df = pd.DataFrame(visits_data, columns=['Apiary Name', 'Location', 'Latitude', 'Longitude', 'Visit Date', 'Notes'])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        apiaries_df.to_excel(writer, sheet_name='Apiaries and Hives', index=False)
        visits_df.to_excel(writer, sheet_name='Visit History', index=False)
    
    output.seek(0)
    return send_file(output, download_name='apiaries_hives.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export/harvests')
@login_required
def export_harvests():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    c.execute("SELECT date, honey_type, amount, money_earned FROM honey_harvests WHERE user_id = ? ORDER BY date DESC", (session['user_id'],))
    data = c.fetchall()
    conn.close()
    
    df = pd.DataFrame(data, columns=['Date', 'Honey Type', 'Amount (kg)', 'Money Earned'])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Honey Harvests', index=False)
    
    output.seek(0)
    return send_file(output, download_name='honey_harvests.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export/recipes')
@login_required
def export_recipes():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Get ingredients with recipe names
    c.execute("""
        SELECT r.name as recipe_name, r.yield, r.yield_unit, i.name as ingredient_name, ri.quantity, ri.unit
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE r.user_id = ?
        ORDER BY r.name, i.name
    """, (session['user_id'],))
    ingredients_data = c.fetchall()
    conn.close()
    
    ingredients_df = pd.DataFrame(ingredients_data, columns=['Recipe Name', 'Yield', 'Yield Unit', 'Ingredient Name', 'Quantity', 'Unit'])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ingredients_df.to_excel(writer, sheet_name='Recipes', index=False)
    
    output.seek(0)
    return send_file(output, download_name='recipes.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export/all')
def export_all():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Apiaries and hives
    c.execute("""
        SELECT a.name as apiary_name, b.name as hive_name, b.description, b.image_path
        FROM apiaries a
        LEFT JOIN beehives b ON a.id = b.apiary_id
        ORDER BY a.name, b.name
    """)
    apiaries_data = c.fetchall()
    
    # Apiary visits
    c.execute("""
        SELECT a.name as apiary_name, av.visit_date, av.notes
        FROM apiaries a
        JOIN apiary_visits av ON a.id = av.apiary_id
        ORDER BY a.name, av.visit_date DESC
    """)
    visits_data = c.fetchall()
    
    # Harvests
    c.execute("SELECT date, honey_type, amount, money_earned FROM honey_harvests ORDER BY date DESC")
    harvests_data = c.fetchall()
    
    # Recipes
    c.execute("SELECT name, yield, yield_unit FROM recipes ORDER BY name")
    recipes_data = c.fetchall()
    
    # Ingredients
    c.execute("""
        SELECT r.name as recipe_name, i.name as ingredient_name, ri.quantity, ri.unit
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        ORDER BY r.name, i.name
    """)
    ingredients_data = c.fetchall()
    
    conn.close()
    
    apiaries_df = pd.DataFrame(apiaries_data, columns=['Apiary Name', 'Hive Name', 'Hive Description', 'Image Path'])
    visits_df = pd.DataFrame(visits_data, columns=['Apiary Name', 'Visit Date', 'Notes'])
    harvests_df = pd.DataFrame(harvests_data, columns=['Date', 'Honey Type', 'Amount (kg)', 'Money Earned'])
    recipes_df = pd.DataFrame(recipes_data, columns=['Recipe Name', 'Yield', 'Yield Unit'])
    ingredients_df = pd.DataFrame(ingredients_data, columns=['Recipe Name', 'Ingredient Name', 'Quantity', 'Unit'])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        apiaries_df.to_excel(writer, sheet_name='Apiaries and Hives', index=False)
        visits_df.to_excel(writer, sheet_name='Visit History', index=False)
        harvests_df.to_excel(writer, sheet_name='Honey Harvests', index=False)
        recipes_df.to_excel(writer, sheet_name='Recipes', index=False)
        ingredients_df.to_excel(writer, sheet_name='Recipe Ingredients', index=False)
    
    output.seek(0)
    return send_file(output, download_name='beekeeping_data.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export/visit_history/<int:apiary_id>')
def export_visit_history(apiary_id):
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Get apiary name
    c.execute("SELECT name FROM apiaries WHERE id = ?", (apiary_id,))
    apiary_name = c.fetchone()[0]
    
    # Get visits for this apiary
    c.execute("""
        SELECT visit_date, notes
        FROM apiary_visits
        WHERE apiary_id = ?
        ORDER BY visit_date DESC
    """, (apiary_id,))
    visits_data = c.fetchall()
    
    conn.close()
    
    visits_df = pd.DataFrame(visits_data, columns=['Visit Date', 'Notes'])
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        visits_df.to_excel(writer, sheet_name=f'{apiary_name} Visits', index=False)
    
    output.seek(0)
    filename = f'{apiary_name}_visit_history.xlsx'.replace(' ', '_')
    return send_file(output, download_name=filename, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)