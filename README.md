# Beekeeping Management Application

A web-based application for managing beekeeping activities, including apiaries, beehives, honey harvests, recipes, and visit history.

## Features

- **User Authentication**: Register new users and login securely with password hashing.
- **Apiaries Management**: Add, edit, delete apiaries with optional location and GPS coordinates.
- **Visit Tracking**: Mark apiary visits with custom dates and notes, and view full visit history for each apiary.
- **Beehive Management**: Add, edit, and delete beehives within apiaries, with descriptions and image uploads.
- **Honey Harvest Tracking**: Record honey harvest events with date, honey type, amount, and money earned.
- **Recipe Management**: Create recipes, add ingredients with quantity and units, and store recipe yields for production planning.
- **Production Calculator**: Estimate how much product can be produced from available ingredient quantities.
- **Weather Dashboard**: View current weather and forecast data on the home dashboard.
- **Data Export**: Export apiaries, hives, visits, harvests, recipes, and ingredients to Excel files, including full workbook export.

## Requirements

- Python 3.x
- Flask
- Flask-Login
- pandas
- openpyxl
- bcrypt

## Installation

1. Clone or download the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the web application:

```bash
python web_app.py
```

Open your browser and go to `http://localhost:5000`.

You will be redirected to the login page. You can register a new account or log in with the default admin account.

The application automatically creates a local SQLite database (`beekeeping.db`) and an `images` folder for storing beehive photos.

## Default Credentials

- Username: `admin`
- Password: `admin123`

> The admin account is created automatically the first time the application runs.

## Data Export

Export options include:

- **Apiaries and Hives**: Download apiary details together with beehive information.
- **Visit History**: Export visit logs for each apiary.
- **Honey Harvests**: Export harvest records with amount and earnings.
- **Recipes**: Export recipes, yields, and ingredient lists.
- **Full Export**: Download all beekeeping data in one Excel workbook with separate sheets.

## Database Structure

The SQLite database (`beekeeping.db`) includes these tables:

- `users` - registered user accounts
- `apiaries` - apiary information with optional location and GPS coordinates
- `apiary_visits` - visit records linked to apiaries
- `beehives` - beehive records linked to apiaries, with descriptions and image paths
- `honey_harvests` - honey harvest records linked to users
- `recipes` - recipes linked to users, including yield and yield unit
- `ingredients` - ingredient names linked to users
- `recipe_ingredients` - recipe ingredient quantities and units

## Web Interface

The application provides a clean interface with these sections:

1. **Home Dashboard**: Weather summary, totals for apiaries, beehives, harvests, visits, honey, and income.
2. **Apiaries**: Manage apiaries, track visits, and view visit history.
3. **Beehives**: Manage beehives within each apiary and upload photos.
4. **Honey Harvest**: Record and manage harvest entries.
5. **Recipes**: Create recipes, add ingredients, and calculate production capacity.
6. **Statistics**: View summary statistics and latest activity.

## Notes

- Beehive photos are stored in the `images/` directory.
- All application data is stored locally in `beekeeping.db`.
- The app is designed for local use and easy extension.
- Admin credentials: Username: Admin, Password: (stored as bcrypt hash)