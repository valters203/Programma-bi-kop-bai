# Beekeeping Management Application

A simple web-based application for managing beekeeping activities, including apiaries, beehives, honey harvests, and recipes.

## Features

- **Admin Login**: Secure authentication system with username and password for accessing the application.
- **Apiaries Management**: Add, edit, delete apiaries and track visit history with custom dates and notes.
- **Visit Tracking**: Mark visits with today's date or custom past dates, view complete visit history per apiary.
- **Beehive Management**: Manage beehives within apiaries, including descriptions and images.
- **Honey Harvest Tracking**: Record honey extraction events with date, type, amount, and earnings.
- **Recipe Management**: Create recipes for honey-based products with ingredients and production calculator.
- **Data Export**: Export all data to Excel files for backup or analysis, including individual apiary visit histories.

## Requirements

- Python 3.x
- Flask
- pandas
- openpyxl

## Installation

1. Clone or download the repository.
2. Install dependencies: `pip install -r requirements.txt`

## Usage

Run the web application:

```bash
python web_app.py
```

Open your browser and go to `http://localhost:5000`

You will be redirected to the login page. Use the admin credentials to access the application.

The application will create a local SQLite database (`beekeeping.db`) and an `images` folder for storing beehive photos.

## Data Export

You can export your data to Excel files:

- **Individual Sections**: Use the "Export to Excel" buttons on each page (Apiaries, Honey Harvest, Recipes)
- **All Data**: Use the "Export All Data to Excel" button on the home page

Exported files include:
- Apiaries and Hives: Combined sheet with apiary and beehive information
- Honey Harvests: All harvest records
- Recipes: Recipe names and detailed ingredient lists
- Full Export: All data in separate sheets within one Excel file

## Database Structure

The SQLite database (`beekeeping.db`) includes these tables:
- `apiaries` - apiary information
- `beehives` - beehive details linked to apiaries
- `honey_harvests` - harvest records
- `recipes` - recipe names
- `ingredients` - ingredient names
- `recipe_ingredients` - links recipes to ingredients with quantities

## Web Interface

The application provides a clean web interface with navigation between sections:

1. **Apiaries**: Manage apiaries and their beehives
2. **Honey Harvest**: Record and view honey extraction data
3. **Recipes**: Manage recipes and calculate production based on available ingredients

## Notes

- Images for beehives are stored locally in the `images/` directory and served via the web app.
- All data is stored locally in the SQLite database.
- The application runs on `localhost:5000` by default.
- All data is stored locally in the SQLite database.
- The application is designed to be simple and expandable.
- Admin credentials: Username: Admin, Password: (stored as bcrypt hash)