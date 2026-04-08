# Beekeeping Management Application - Database Structure

## Overview
This document provides a detailed description of the SQLite database schema for the Beekeeping Management Application. The database tracks apiaries, beehives, honey harvests, recipes, and ingredients used in beekeeping operations.

---

## Tables

### 1. `apiaries`
**Purpose:** Stores information about apiaries (bee yards/locations).

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each apiary |
| name | TEXT | NOT NULL | Name of the apiary location |

**Relationships:**
- One apiary has many beehives (1:N relationship with `beehives`)
- One apiary has many visits (1:N relationship with `apiary_visits`)

**Example Data:**
- Pie meža (Forest Apiary)
- Park apiary

---

### 2. `apiary_visits`
**Purpose:** Tracks visits to each apiary with dates and notes about maintenance or observations.

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each visit record |
| apiary_id | INTEGER | FOREIGN KEY (apiaries.id) | References the apiary being visited |
| visit_date | TEXT | NOT NULL | Date of the visit (format: YYYY-MM-DD) |
| notes | TEXT | NULLABLE | Optional notes about the visit (observations, maintenance performed, etc.) |

**Relationships:**
- Many visits belong to one apiary (N:1 relationship with `apiaries`)

**Example Data:**
- Apiary 1, 2026-03-17, "Spring inspection"
- Apiary 1, 2026-02-05, "Winter maintenance"

---

### 3. `beehives`
**Purpose:** Stores information about individual beehives within apiaries.

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each beehive |
| apiary_id | INTEGER | FOREIGN KEY (apiaries.id) | References the parent apiary |
| name | TEXT | NOT NULL | Name or identifier for the beehive (e.g., "Hive 1", "Queen Colony") |
| description | TEXT | NULLABLE | Additional details about the hive (queen age, strain type, etc.) |
| image_path | TEXT | NULLABLE | File path to an image of the beehive (e.g., "images/1_1_images.jpg") |

**Relationships:**
- Many beehives belong to one apiary (N:1 relationship with `apiaries`)

**Example Data:**
- id=1, apiary_id=1, name="nav apraksts", description=NULL, image_path="images/1_1_images.jpg"

---

### 4. `honey_harvests`
**Purpose:** Records honey harvest events with yield and financial information.

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each harvest |
| date | TEXT | NOT NULL | Date of the harvest (format: YYYY-MM-DD) |
| honey_type | TEXT | NOT NULL | Type/variety of honey harvested (e.g., "Spring honey", "Acacia honey") |
| amount | REAL | NOT NULL | Quantity of honey harvested (numeric value) |
| money_earned | REAL | NULLABLE | Revenue from selling the honey (optional) |

**Relationships:**
- Standalone table (no direct foreign keys, but relates to overall beekeeping operations)

**Example Data:**
- id=1, date="2026-03-17", honey_type="Pavasara" (Spring), amount=50.0, money_earned=NULL

---

### 5. `recipes`
**Purpose:** Stores recipe names for honey-based products.

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each recipe |
| name | TEXT | NOT NULL | Name of the recipe (e.g., "Honey Cakes", "Honey with nuts") |

**Relationships:**
- One recipe has many ingredients (1:N relationship with `recipe_ingredients`)

**Example Data:**
- id=1, name="Medus konfektes" (Honey Confections)

---

### 6. `ingredients`
**Purpose:** Stores individual ingredients that can be used in recipes.

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each ingredient |
| name | TEXT | NOT NULL | Name of the ingredient (e.g., "honey", "gelatin", "sugar") |

**Relationships:**
- One ingredient can be used in many recipes (1:N relationship with `recipe_ingredients`)

**Example Data:**
- id=1, name="želatīns" (Gelatin)
- id=2, name="Medus" (Honey)

---

### 7. `recipe_ingredients`
**Purpose:** Junction table implementing many-to-many relationship between recipes and ingredients with quantity specifications.

**Columns:**
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | Unique identifier for each recipe-ingredient association |
| recipe_id | INTEGER | FOREIGN KEY (recipes.id) | References the recipe |
| ingredient_id | INTEGER | FOREIGN KEY (ingredients.id) | References the ingredient |
| quantity | REAL | NOT NULL | Amount of the ingredient required |
| unit | TEXT | NULLABLE | Unit of measurement (e.g., "kg", "g", "ml", "cups") |

**Relationships:**
- Many associations belong to one recipe (N:1 relationship with `recipes`)
- Many associations belong to one ingredient (N:1 relationship with `ingredients`)

**Example Data:**
- id=1, recipe_id=1, ingredient_id=1, quantity=0.5, unit="kg"
- id=2, recipe_id=1, ingredient_id=2, quantity=200, unit="g"

---

## Entity Relationship Diagram (Conceptual)

```
┌─────────────────────┐
│     apiaries        │
├─────────────────────┤
│ id (PK)             │
│ name                │
└─────────────────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼ (1:N)                              ▼ (1:N)
┌──────────────────────────┐      ┌──────────────────────────┐
│      beehives            │      │    apiary_visits         │
├──────────────────────────┤      ├──────────────────────────┤
│ id (PK)                  │      │ id (PK)                  │
│ apiary_id (FK)           │      │ apiary_id (FK)           │
│ name                     │      │ visit_date               │
│ description              │      │ notes                    │
│ image_path               │      └──────────────────────────┘
└──────────────────────────┘

┌─────────────────────────────┐       ┌──────────────────────┐
│    honey_harvests           │       │     recipes          │
├─────────────────────────────┤       ├──────────────────────┤
│ id (PK)                     │       │ id (PK)              │
│ date                        │       │ name                 │
│ honey_type                  │       └──────────────────────┘
│ amount                      │                 │
│ money_earned                │                 │ (1:N)
└─────────────────────────────┘                 │
                                         ┌──────────────────────────────┐
                                         │  recipe_ingredients          │
                                         ├──────────────────────────────┤
                                         │ id (PK)                      │
                                         │ recipe_id (FK)               │
                                         │ ingredient_id (FK)           │
                                         │ quantity                     │
                                         │ unit                         │
                                         └──────────────────────────────┘
                                                   │
                                                   │ (N:1)
                                                   │
                                         ┌──────────────────────┐
                                         │    ingredients       │
                                         ├──────────────────────┤
                                         │ id (PK)              │
                                         │ name                 │
                                         └──────────────────────┘
```

---

## Key Relationships

### 1. Apiary → Beehive (1:N)
- One apiary can have many beehives
- Delete cascade consideration: Deleting an apiary should cascade delete related beehives

### 2. Apiary → Visits (1:N)
- One apiary can have many visit records
- Delete cascade consideration: Deleting an apiary should cascade delete related visit records

### 3. Recipe → Ingredients (M:N through junction table)
- One recipe can use many ingredients
- One ingredient can be used in many recipes
- The junction table `recipe_ingredients` manages this relationship with quantity and unit information

---

## Data Type Notes

- **TEXT:** Used for names, descriptions, notes, and dates (stored as ISO 8601 format: YYYY-MM-DD)
- **INTEGER:** Used for IDs and primary/foreign keys
- **REAL:** Used for numerical quantities (amounts, money) to support decimal values

---

## Constraints and Foreign Keys

| Table | Column | References | On Delete | On Update |
|---|---|---|---|---|
| beehives | apiary_id | apiaries.id | (Not specified) | (Not specified) |
| apiary_visits | apiary_id | apiaries.id | (Not specified) | (Not specified) |
| recipe_ingredients | recipe_id | recipes.id | (Not specified) | (Not specified) |
| recipe_ingredients | ingredient_id | ingredients.id | (Not specified) | (Not specified) |

**Note:** SQLite does not enforce foreign keys by default. The application layer should handle cascade deletes and data integrity.

---

## Database Statistics

**Current Data Sample:**
- Apiaries: 1 (Pie meža)
- Beehives: 1 (associated with Pie meža)
- Apiary Visits: 3 (recorded dates: 2026-02-05, 2026-03-06, 2026-03-10, 2026-03-17)
- Honey Harvests: 1 (Spring honey, 2026-03-17)
- Recipes: 1 (Medus konfektes - Honey Confections)
- Ingredients: 2 (želatīns, Medus)
- Recipe Ingredients: 2 (associations between Honey Confections recipe and its ingredients)

---

## Usage Notes

### Date Format
All dates are stored as TEXT in ISO 8601 format (YYYY-MM-DD) for consistency and easy sorting.

### Image Storage
Beehive images are stored as file paths in the `image_path` column, with files typically located in the `images/` directory. The naming convention appears to be `{apiary_id}_{beehive_id}_images.jpg`.

### Units in Recipes
The `unit` column in `recipe_ingredients` stores measurement units such as:
- kg (kilograms)
- g (grams)
- ml (milliliters)
- cups
- tbsp (tablespoons)
- tsp (teaspoons)

### Optional Fields
Fields marked as NULLABLE in the design include:
- `beehives.description` - Can be empty if no description is provided
- `beehives.image_path` - Can be empty if no image is uploaded
- `apiary_visits.notes` - Can be empty for visits with no notes
- `honey_harvests.money_earned` - Can be empty if harvest wasn't sold or revenue unknown
- `recipe_ingredients.unit` - Can be empty if quantity unit is not specified

---

## Database File Location
`beekeeping.db` - SQLite database file located in the application root directory.

