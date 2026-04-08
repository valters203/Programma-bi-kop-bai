import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import os
import shutil

# Database setup
def create_database():
    conn = sqlite3.connect('beekeeping.db')
    c = conn.cursor()
    
    # Apiaries table
    c.execute('''CREATE TABLE IF NOT EXISTS apiaries (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    last_visit_date TEXT
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
                    date TEXT NOT NULL,
                    honey_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    money_earned REAL
                )''')
    
    # Recipes table
    c.execute('''CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )''')
    
    # Ingredients table
    c.execute('''CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )''')
    
    # Recipe ingredients table
    c.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    id INTEGER PRIMARY KEY,
                    recipe_id INTEGER,
                    ingredient_id INTEGER,
                    quantity REAL NOT NULL,
                    FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
                )''')
    
    conn.commit()
    conn.close()

# Main Application Class
class BeekeepingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Beekeeping Management")
        self.geometry("800x600")
        
        # Create database
        create_database()
        
        # Create images directory if not exists
        if not os.path.exists('images'):
            os.makedirs('images')
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Apiaries Tab
        self.apiaries_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.apiaries_frame, text="Apiaries")
        self.setup_apiaries_tab()
        
        # Honey Harvest Tab
        self.harvest_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.harvest_frame, text="Honey Harvest")
        self.setup_harvest_tab()
        
        # Recipes Tab
        self.recipes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recipes_frame, text="Recipes")
        self.setup_recipes_tab()

    def setup_apiaries_tab(self):
        # Apiary List
        self.apiary_listbox = tk.Listbox(self.apiaries_frame, height=10)
        self.apiary_listbox.pack(fill=tk.X, padx=10, pady=10)
        self.apiary_listbox.bind('<<ListboxSelect>>', self.on_apiary_select)
        
        # Apiary Buttons
        apiary_buttons_frame = ttk.Frame(self.apiaries_frame)
        apiary_buttons_frame.pack(fill=tk.X, padx=10)
        ttk.Button(apiary_buttons_frame, text="Add Apiary", command=self.add_apiary).pack(side=tk.LEFT, padx=5)
        ttk.Button(apiary_buttons_frame, text="Edit Apiary", command=self.edit_apiary).pack(side=tk.LEFT, padx=5)
        ttk.Button(apiary_buttons_frame, text="Delete Apiary", command=self.delete_apiary).pack(side=tk.LEFT, padx=5)
        ttk.Button(apiary_buttons_frame, text="Visit Today", command=self.visit_apiary).pack(side=tk.LEFT, padx=5)
        
        # Beehive List
        ttk.Label(self.apiaries_frame, text="Beehives:").pack(anchor=tk.W, padx=10)
        self.beehive_listbox = tk.Listbox(self.apiaries_frame, height=10)
        self.beehive_listbox.pack(fill=tk.X, padx=10, pady=10)
        
        # Beehive Buttons
        beehive_buttons_frame = ttk.Frame(self.apiaries_frame)
        beehive_buttons_frame.pack(fill=tk.X, padx=10)
        ttk.Button(beehive_buttons_frame, text="Add Beehive", command=self.add_beehive).pack(side=tk.LEFT, padx=5)
        ttk.Button(beehive_buttons_frame, text="Edit Beehive", command=self.edit_beehive).pack(side=tk.LEFT, padx=5)
        ttk.Button(beehive_buttons_frame, text="Delete Beehive", command=self.delete_beehive).pack(side=tk.LEFT, padx=5)
        ttk.Button(beehive_buttons_frame, text="Upload Image", command=self.upload_beehive_image).pack(side=tk.LEFT, padx=5)
        
        self.load_apiaries()

    def load_apiaries(self):
        self.apiary_listbox.delete(0, tk.END)
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT id, name, last_visit_date FROM apiaries ORDER BY name")
        apiaries = c.fetchall()
        conn.close()
        for apiary in apiaries:
            display_text = f"{apiary[1]} - Last visited: {apiary[2] or 'Never'}"
            self.apiary_listbox.insert(tk.END, display_text)
            self.apiary_listbox.itemconfig(tk.END, {'bg': 'lightblue' if apiary[2] else 'white'})

    def on_apiary_select(self, event):
        selection = self.apiary_listbox.curselection()
        if selection:
            index = selection[0]
            text = self.apiary_listbox.get(index)
            apiary_name = text.split(' - ')[0]
            self.selected_apiary_name = apiary_name
            self.load_beehives(apiary_name)

    def load_beehives(self, apiary_name):
        self.beehive_listbox.delete(0, tk.END)
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT id FROM apiaries WHERE name = ?", (apiary_name,))
        apiary_id = c.fetchone()[0]
        c.execute("SELECT name, description FROM beehives WHERE apiary_id = ?", (apiary_id,))
        beehives = c.fetchall()
        conn.close()
        for beehive in beehives:
            display_text = f"{beehive[0]} - {beehive[1] or ''}"
            self.beehive_listbox.insert(tk.END, display_text)

    def add_apiary(self):
        name = simpledialog.askstring("Add Apiary", "Enter apiary name:")
        if name:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("INSERT INTO apiaries (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            self.load_apiaries()

    def edit_apiary(self):
        selection = self.apiary_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select an apiary to edit")
            return
        index = selection[0]
        text = self.apiary_listbox.get(index)
        old_name = text.split(' - ')[0]
        new_name = simpledialog.askstring("Edit Apiary", "Enter new name:", initialvalue=old_name)
        if new_name:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("UPDATE apiaries SET name = ? WHERE name = ?", (new_name, old_name))
            conn.commit()
            conn.close()
            self.load_apiaries()

    def delete_apiary(self):
        selection = self.apiary_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select an apiary to delete")
            return
        if messagebox.askyesno("Confirm", "Delete this apiary and all its beehives?"):
            index = selection[0]
            text = self.apiary_listbox.get(index)
            name = text.split(' - ')[0]
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM apiaries WHERE name = ?", (name,))
            apiary_id = c.fetchone()[0]
            c.execute("DELETE FROM beehives WHERE apiary_id = ?", (apiary_id,))
            c.execute("DELETE FROM apiaries WHERE id = ?", (apiary_id,))
            conn.commit()
            conn.close()
            self.load_apiaries()
            self.beehive_listbox.delete(0, tk.END)

    def visit_apiary(self):
        selection = self.apiary_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select an apiary to visit")
            return
        index = selection[0]
        text = self.apiary_listbox.get(index)
        name = text.split(' - ')[0]
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("UPDATE apiaries SET last_visit_date = ? WHERE name = ?", (today, name))
        conn.commit()
        conn.close()
        self.load_apiaries()

    def add_beehive(self):
        if not hasattr(self, 'selected_apiary_name'):
            messagebox.showerror("Error", "Select an apiary first")
            return
        name = simpledialog.askstring("Add Beehive", "Enter beehive name:")
        if name:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM apiaries WHERE name = ?", (self.selected_apiary_name,))
            apiary_id = c.fetchone()[0]
            c.execute("INSERT INTO beehives (apiary_id, name) VALUES (?, ?)", (apiary_id, name))
            conn.commit()
            conn.close()
            self.load_beehives(self.selected_apiary_name)

    def edit_beehive(self):
        selection = self.beehive_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a beehive to edit")
            return
        index = selection[0]
        text = self.beehive_listbox.get(index)
        old_name = text.split(' - ')[0]
        new_name = simpledialog.askstring("Edit Beehive", "Enter new name:", initialvalue=old_name)
        if new_name:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM apiaries WHERE name = ?", (self.selected_apiary_name,))
            apiary_id = c.fetchone()[0]
            c.execute("UPDATE beehives SET name = ? WHERE apiary_id = ? AND name = ?", (new_name, apiary_id, old_name))
            conn.commit()
            conn.close()
            self.load_beehives(self.selected_apiary_name)

    def delete_beehive(self):
        selection = self.beehive_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a beehive to delete")
            return
        if messagebox.askyesno("Confirm", "Delete this beehive?"):
            index = selection[0]
            text = self.beehive_listbox.get(index)
            name = text.split(' - ')[0]
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM apiaries WHERE name = ?", (self.selected_apiary_name,))
            apiary_id = c.fetchone()[0]
            c.execute("DELETE FROM beehives WHERE apiary_id = ? AND name = ?", (apiary_id, name))
            conn.commit()
            conn.close()
            self.load_beehives(self.selected_apiary_name)

    def upload_beehive_image(self):
        selection = self.beehive_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a beehive to upload image")
            return
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
        if file_path:
            index = selection[0]
            text = self.beehive_listbox.get(index)
            name = text.split(' - ')[0]
            # Copy image to images folder
            filename = os.path.basename(file_path)
            dest_path = os.path.join('images', filename)
            shutil.copy(file_path, dest_path)
            # Update database
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM apiaries WHERE name = ?", (self.selected_apiary_name,))
            apiary_id = c.fetchone()[0]
            c.execute("UPDATE beehives SET image_path = ? WHERE apiary_id = ? AND name = ?", (dest_path, apiary_id, name))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Image uploaded")

    def setup_harvest_tab(self):
        # Harvest List
        self.harvest_tree = ttk.Treeview(self.harvest_frame, columns=("ID", "Date", "Type", "Amount", "Money"), show="headings")
        self.harvest_tree.heading("ID", text="ID")
        self.harvest_tree.heading("Date", text="Date")
        self.harvest_tree.heading("Type", text="Honey Type")
        self.harvest_tree.heading("Amount", text="Amount (kg)")
        self.harvest_tree.heading("Money", text="Money Earned")
        self.harvest_tree.column("ID", width=0, stretch=tk.NO)  # Hide ID column
        self.harvest_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(self.harvest_frame)
        buttons_frame.pack(fill=tk.X, padx=10)
        ttk.Button(buttons_frame, text="Add Harvest", command=self.add_harvest).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Edit Harvest", command=self.edit_harvest).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Delete Harvest", command=self.delete_harvest).pack(side=tk.LEFT, padx=5)
        
        self.load_harvests()

    def load_harvests(self):
        for item in self.harvest_tree.get_children():
            self.harvest_tree.delete(item)
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT id, date, honey_type, amount, money_earned FROM honey_harvests ORDER BY date DESC")
        harvests = c.fetchall()
        conn.close()
        for harvest in harvests:
            self.harvest_tree.insert("", tk.END, values=harvest)

    def add_harvest(self):
        date = simpledialog.askstring("Add Harvest", "Date (YYYY-MM-DD):", initialvalue=datetime.now().strftime("%Y-%m-%d"))
        if not date:
            return
        honey_type = simpledialog.askstring("Add Harvest", "Honey Type:")
        if not honey_type:
            return
        amount = simpledialog.askfloat("Add Harvest", "Amount (kg):")
        if amount is None:
            return
        money = simpledialog.askfloat("Add Harvest", "Money Earned:")
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("INSERT INTO honey_harvests (date, honey_type, amount, money_earned) VALUES (?, ?, ?, ?)", (date, honey_type, amount, money))
        conn.commit()
        conn.close()
        self.load_harvests()

    def edit_harvest(self):
        selected = self.harvest_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a harvest to edit")
            return
        item = self.harvest_tree.item(selected[0])
        values = item['values']
        id = values[0]
        date = simpledialog.askstring("Edit Harvest", "Date (YYYY-MM-DD):", initialvalue=values[1])
        if not date:
            return
        honey_type = simpledialog.askstring("Edit Harvest", "Honey Type:", initialvalue=values[2])
        if not honey_type:
            return
        amount = simpledialog.askfloat("Edit Harvest", "Amount (kg):", initialvalue=values[3])
        if amount is None:
            return
        money = simpledialog.askfloat("Edit Harvest", "Money Earned:", initialvalue=values[4])
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("UPDATE honey_harvests SET date=?, honey_type=?, amount=?, money_earned=? WHERE id=?", (date, honey_type, amount, money, id))
        conn.commit()
        conn.close()
        self.load_harvests()

    def delete_harvest(self):
        selected = self.harvest_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a harvest to delete")
            return
        if messagebox.askyesno("Confirm", "Delete this harvest record?"):
            item = self.harvest_tree.item(selected[0])
            id = item['values'][0]
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("DELETE FROM honey_harvests WHERE id=?", (id,))
            conn.commit()
            conn.close()
            self.load_harvests()

    def setup_recipes_tab(self):
        # Recipe List
        self.recipe_listbox = tk.Listbox(self.recipes_frame, height=10)
        self.recipe_listbox.pack(fill=tk.X, padx=10, pady=10)
        self.recipe_listbox.bind('<<ListboxSelect>>', self.on_recipe_select)
        
        # Recipe Buttons
        recipe_buttons_frame = ttk.Frame(self.recipes_frame)
        recipe_buttons_frame.pack(fill=tk.X, padx=10)
        ttk.Button(recipe_buttons_frame, text="Add Recipe", command=self.add_recipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(recipe_buttons_frame, text="Edit Recipe", command=self.edit_recipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(recipe_buttons_frame, text="Delete Recipe", command=self.delete_recipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(recipe_buttons_frame, text="Calculate Production", command=self.calculate_production).pack(side=tk.LEFT, padx=5)
        
        # Ingredients List
        ttk.Label(self.recipes_frame, text="Ingredients:").pack(anchor=tk.W, padx=10)
        self.ingredients_listbox = tk.Listbox(self.recipes_frame, height=10)
        self.ingredients_listbox.pack(fill=tk.X, padx=10, pady=10)
        
        # Ingredient Buttons
        ing_buttons_frame = ttk.Frame(self.recipes_frame)
        ing_buttons_frame.pack(fill=tk.X, padx=10)
        ttk.Button(ing_buttons_frame, text="Add Ingredient", command=self.add_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(ing_buttons_frame, text="Edit Ingredient", command=self.edit_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(ing_buttons_frame, text="Delete Ingredient", command=self.delete_ingredient).pack(side=tk.LEFT, padx=5)
        
        self.load_recipes()

    def load_recipes(self):
        self.recipe_listbox.delete(0, tk.END)
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT name FROM recipes ORDER BY name")
        recipes = c.fetchall()
        conn.close()
        for recipe in recipes:
            self.recipe_listbox.insert(tk.END, recipe[0])

    def on_recipe_select(self, event):
        selection = self.recipe_listbox.curselection()
        if selection:
            index = selection[0]
            recipe_name = self.recipe_listbox.get(index)
            self.selected_recipe_name = recipe_name
            self.load_ingredients(recipe_name)

    def load_ingredients(self, recipe_name):
        self.ingredients_listbox.delete(0, tk.END)
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT id FROM recipes WHERE name = ?", (recipe_name,))
        recipe_id = c.fetchone()[0]
        c.execute("""SELECT i.name, ri.quantity FROM recipe_ingredients ri
                     JOIN ingredients i ON ri.ingredient_id = i.id
                     WHERE ri.recipe_id = ?""", (recipe_id,))
        ingredients = c.fetchall()
        conn.close()
        for ing in ingredients:
            self.ingredients_listbox.insert(tk.END, f"{ing[0]}: {ing[1]}")

    def add_recipe(self):
        name = simpledialog.askstring("Add Recipe", "Enter recipe name:")
        if name:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("INSERT INTO recipes (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            self.load_recipes()

    def edit_recipe(self):
        selection = self.recipe_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a recipe to edit")
            return
        index = selection[0]
        old_name = self.recipe_listbox.get(index)
        new_name = simpledialog.askstring("Edit Recipe", "Enter new name:", initialvalue=old_name)
        if new_name:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("UPDATE recipes SET name = ? WHERE name = ?", (new_name, old_name))
            conn.commit()
            conn.close()
            self.load_recipes()

    def delete_recipe(self):
        selection = self.recipe_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a recipe to delete")
            return
        if messagebox.askyesno("Confirm", "Delete this recipe and all its ingredients?"):
            index = selection[0]
            name = self.recipe_listbox.get(index)
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM recipes WHERE name = ?", (name,))
            recipe_id = c.fetchone()[0]
            c.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
            c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
            conn.commit()
            conn.close()
            self.load_recipes()
            self.ingredients_listbox.delete(0, tk.END)

    def add_ingredient(self):
        if not hasattr(self, 'selected_recipe_name'):
            messagebox.showerror("Error", "Select a recipe first")
            return
        # First, select or add ingredient
        ing_name = simpledialog.askstring("Add Ingredient", "Ingredient name:")
        if not ing_name:
            return
        quantity = simpledialog.askfloat("Add Ingredient", "Quantity:")
        if quantity is None:
            return
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        # Check if ingredient exists
        c.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,))
        ing_id = c.fetchone()
        if not ing_id:
            c.execute("INSERT INTO ingredients (name) VALUES (?)", (ing_name,))
            ing_id = c.lastrowid
        else:
            ing_id = ing_id[0]
        # Add to recipe
        c.execute("SELECT id FROM recipes WHERE name = ?", (self.selected_recipe_name,))
        recipe_id = c.fetchone()[0]
        c.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (?, ?, ?)", (recipe_id, ing_id, quantity))
        conn.commit()
        conn.close()
        self.load_ingredients(self.selected_recipe_name)

    def edit_ingredient(self):
        # This is simplified, edit quantity
        selection = self.ingredients_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select an ingredient to edit")
            return
        index = selection[0]
        text = self.ingredients_listbox.get(index)
        ing_name = text.split(': ')[0]
        old_qty = float(text.split(': ')[1])
        new_qty = simpledialog.askfloat("Edit Ingredient", "New quantity:", initialvalue=old_qty)
        if new_qty is not None:
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM recipes WHERE name = ?", (self.selected_recipe_name,))
            recipe_id = c.fetchone()[0]
            c.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,))
            ing_id = c.fetchone()[0]
            c.execute("UPDATE recipe_ingredients SET quantity = ? WHERE recipe_id = ? AND ingredient_id = ?", (new_qty, recipe_id, ing_id))
            conn.commit()
            conn.close()
            self.load_ingredients(self.selected_recipe_name)

    def delete_ingredient(self):
        selection = self.ingredients_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select an ingredient to delete")
            return
        if messagebox.askyesno("Confirm", "Delete this ingredient from recipe?"):
            index = selection[0]
            text = self.ingredients_listbox.get(index)
            ing_name = text.split(': ')[0]
            conn = sqlite3.connect('beekeeping.db')
            c = conn.cursor()
            c.execute("SELECT id FROM recipes WHERE name = ?", (self.selected_recipe_name,))
            recipe_id = c.fetchone()[0]
            c.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,))
            ing_id = c.fetchone()[0]
            c.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ? AND ingredient_id = ?", (recipe_id, ing_id))
            conn.commit()
            conn.close()
            self.load_ingredients(self.selected_recipe_name)

    def calculate_production(self):
        if not hasattr(self, 'selected_recipe_name'):
            messagebox.showerror("Error", "Select a recipe first")
            return
        # Get ingredients and required quantities
        conn = sqlite3.connect('beekeeping.db')
        c = conn.cursor()
        c.execute("SELECT id FROM recipes WHERE name = ?", (self.selected_recipe_name,))
        recipe_id = c.fetchone()[0]
        c.execute("""SELECT i.name, ri.quantity FROM recipe_ingredients ri
                     JOIN ingredients i ON ri.ingredient_id = i.id
                     WHERE ri.recipe_id = ?""", (recipe_id,))
        ingredients = c.fetchall()
        conn.close()
        if not ingredients:
            messagebox.showinfo("Info", "No ingredients in this recipe")
            return
        # Ask for available amounts
        available = {}
        for ing in ingredients:
            name, req = ing
            avail = simpledialog.askfloat(f"Available {name}", f"How much {name} do you have?")
            if avail is None:
                return
            available[name] = avail / req if req > 0 else 0
        # Calculate max production (min ratio)
        if available:
            max_prod = min(available.values())
            messagebox.showinfo("Production", f"You can produce {max_prod:.2f} units of the product")
        else:
            messagebox.showinfo("Production", "No production possible")

if __name__ == "__main__":
    app = BeekeepingApp()
    app.mainloop()