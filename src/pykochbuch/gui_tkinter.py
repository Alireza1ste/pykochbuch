import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from pykochbuch.storage.serialization import _recipe_to_dict, _dict_to_recipe
from pykochbuch.storage.json_store import JsonStore
from pykochbuch.storage.sqlite_store import SqliteStore
from pykochbuch.storage.memory_store import InMemoryStore
from pykochbuch.recipe_book import RecipeBook
from pathlib import Path
import json


class AddRecipeDialog(tk.Toplevel):
    def __init__(self, parent, app_instance, store):
        super().__init__(parent)
        self.store = store
        self.app_instance = app_instance
        self.title("Add New Recipe")
        self.geometry("500x600")
        self.transient(parent)
        self.grab_set()

        # Main container
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Recipe Title
        tk.Label(main_frame, text="Recipe Title:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.title_entry = tk.Entry(main_frame)
        self.title_entry.pack(fill=tk.X, pady=(0, 10))

        # 2. Servings & Prep Time (Side by Side)
        row2 = tk.Frame(main_frame)
        row2.pack(fill=tk.X, pady=10)
        
        tk.Label(row2, text="Servings:").pack(side=tk.LEFT)
        self.servings_entry = tk.Entry(row2, width=10)
        self.servings_entry.insert(0, "4")
        self.servings_entry.pack(side=tk.LEFT, padx=10)

        tk.Label(row2, text="Prep Time (mins):").pack(side=tk.LEFT)
        self.prep_entry = tk.Entry(row2, width=10) # <--- This was missing!
        self.prep_entry.insert(0, "15")
        self.prep_entry.pack(side=tk.LEFT, padx=10)

        # 3. Description
        tk.Label(main_frame, text="Description:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.desc_entry = tk.Entry(main_frame)
        self.desc_entry.pack(fill=tk.X, pady=(0, 10))

        # 4. Ingredients
        tk.Label(main_frame, text="Ingredients (e.g., 500 g Flour, 2 pc Egg):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ing_entry = tk.Entry(main_frame)
        self.ing_entry.pack(fill=tk.X, pady=(0, 5))
        tk.Label(main_frame, text="Use: Amount Unit Name (split by commas)", font=("Arial", 8), fg="gray").pack(anchor="w", pady=(0, 10))

        # 5. Instructions
        tk.Label(main_frame, text="Instructions (Split by commas):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.instr_entry = tk.Entry(main_frame)
        self.instr_entry.pack(fill=tk.X, pady=(0, 10))

        # 6. Tags
        tk.Label(main_frame, text="Tags (comma separated):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.tags_entry = tk.Entry(main_frame)
        self.tags_entry.insert(0, "Easy, Dinner")
        self.tags_entry.pack(fill=tk.X, pady=(0, 20))

        # Save Button
        tk.Button(main_frame, text="💾 Save to Cookbook", bg="#28a745", fg="white", 
                  font=("Arial", 11, "bold"), height=2, command=self.save).pack(fill=tk.X)

    def save(self):
        from pykochbuch.models import Recipe, Ingredient, Unit
        import re

        try:
            # 1. Capture and Sanitize Inputs
            title = self.title_entry.get().strip()
            # re.sub removes everything that isn't a digit
            servings = int(re.sub(r"\D", "", self.servings_entry.get()) or "0")
            prep_time = int(re.sub(r"\D", "", self.prep_entry.get()) or "0")
            description = self.desc_entry.get().strip()
            
            # Tags conversion
            tags_raw = self.tags_entry.get().split(",")
            tags = frozenset(t.strip() for t in tags_raw if t.strip())

            # 2. Parse Ingredients
            ing_raw = self.ing_entry.get().strip()
            parsed_ingredients = []
            if ing_raw:
                for item in ing_raw.split(","):
                    parts = item.strip().split(" ")
                    if len(parts) >= 3:
                        amount = float(parts[0])
                        unit_val = parts[1].lower()
                        name = " ".join(parts[2:])
                        # This assumes your Unit Enum values are 'g', 'pc', 'l', etc.
                        parsed_ingredients.append(Ingredient(name=name, amount=amount, unit=Unit(unit_val)))

            if not parsed_ingredients:
                messagebox.showerror("Error", "You must add at least one ingredient!\nFormat: 500 g Flour")
                return

            # 3. Create Recipe Object
            new_recipe = Recipe(
                title=title,
                servings=servings,
                ingredients=tuple(parsed_ingredients),
                instructions=tuple(s.strip() for s in self.instr_entry.get().split(",") if s.strip()),
                tags=tags,
                description=description,
                prep_time_minutes=prep_time
            )

            # 4. Store and Refresh
            print(f"DEBUG: Attempting to save {new_recipe.title} to {type(self.store).__name__}")
            self.store.save_recipe(new_recipe)
            messagebox.showinfo("Success", f"'{title}' has been added!")
            self.app_instance.refresh_list()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Save Error", f"Details: {str(e)}")
class CookbookGUI:
    def __init__(self, root, store):
        self.root = root
        self.store = store
        self.root.title(f"Cookbook Administrator - {type(store).__name__}")
        self.root.geometry("1000x650")
        
        self.setup_styles()
        self.setup_ui()
        self.refresh_list()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure("Admin.TButton", font=("Arial", 10, "bold"))
    
    def import_from_sqlite(self):
        """Loads recipes from a DIFFERENT .db file into the CURRENT store."""
        file_path = filedialog.askopenfilename(
            title="Select SQLite Database to Import",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # 1. Create a temporary store to read the external file
            # Your dataclass handles the connection and table checks automatically
            external_store = SqliteStore(db_path=Path(file_path))
            external_recipes = external_store.get_all_recipes()
            
            # 2. Save each recipe into our active store
            count = 0
            for recipe in external_recipes:
                try:
                    self.store.save_recipe(recipe)
                    count += 1
                except ValueError:
                    # Skip duplicates if the title already exists
                    continue
            
            messagebox.showinfo("Success", f"Imported {count} recipes from {Path(file_path).name}")
            self.refresh_list()
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to load SQL file: {e}")

    def export_to_sqlite(self):
        """Saves all recipes from the CURRENT store into a NEW .db file."""
        file_path = filedialog.asksaveasfilename(
            title="Export to New SQLite Database",
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db")]
        )
        if not file_path:
            return

        try:
            # 1. Initialize a new database file using your dataclass
            new_store = SqliteStore(db_path=Path(file_path))
            
            # 2. Get all data from our current active store
            all_recipes = self.store.get_all_recipes()
            
            # 3. Write it all into the new file
            for recipe in all_recipes:
                new_store.save_recipe(recipe)
                
            messagebox.showinfo("Success", f"All recipes exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save SQL file: {e}")

    def setup_ui(self):
        # --- TOP: Search Bar ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="🔍 Search Recipes:").pack(side=tk.LEFT)
        
        # This variable tracks what you type in real-time
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        
        # Link ONLY THIS ONE entry to search_var
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # --- MIDDLE: List and Details ---
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10)

        # Left Listbox Side for checkmarks
        list_frame = ttk.Frame(paned)
        paned.add(list_frame, weight=1)
        
        # Added a scrollbar so you can actually scroll through long lists
        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.recipe_listbox = tk.Listbox(
            list_frame, 
            font=("Arial", 11), 
            yscrollcommand=list_scroll.set,
            exportselection=False # This keeps the recipe highlighted when you click buttons
        )
        self.recipe_listbox.pack(fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.recipe_listbox.yview)
        self.recipe_listbox.bind("<<ListboxSelect>>", self.on_recipe_select)

        # Right Text View Side
        detail_frame = ttk.Frame(paned)
        paned.add(detail_frame, weight=3)
        self.title_label = ttk.Label(detail_frame, text="Select a Recipe", font=("Arial", 14, "bold"))
        self.title_label.pack(pady=5, anchor="w")
        
        # Added some padding to the text box for better readability
        self.details_text = tk.Text(detail_frame, state=tk.DISABLED, wrap=tk.WORD, bg="#f9f9f9", padx=10, pady=10)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # --- BOTTOM: Action Buttons ---
        action_bar = ttk.LabelFrame(self.root, text=" Data Management ", padding="10")
        action_bar.pack(fill=tk.X, padx=10, pady=10)

        # Basic Actions (Left)
        ttk.Button(action_bar, text="➕ Add Recipe", command=self.add_recipe_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="🗑 Delete", command=self.delete_current).pack(side=tk.LEFT, padx=5)
        
        # SQL Management (Right)
        sql_frame = ttk.Frame(action_bar)
        sql_frame.pack(side=tk.RIGHT, padx=10)
        ttk.Label(sql_frame, text="SQL:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Button(sql_frame, text="📥 Import", command=self.import_from_sqlite).pack(side=tk.LEFT, padx=2)
        ttk.Button(sql_frame, text="📤 Export", command=self.export_to_sqlite).pack(side=tk.LEFT, padx=2)

        # JSON Management (Right)
        json_frame = ttk.Frame(action_bar)
        json_frame.pack(side=tk.RIGHT, padx=10)
        ttk.Label(json_frame, text="JSON:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Button(json_frame, text="📥 Import", command=self.import_from_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(json_frame, text="📤 Export", command=self.export_to_json).pack(side=tk.LEFT, padx=2)


    # --- LOGIC ---

    def on_search_change(self, *args):
        # 1. Get the text from the search box
        query = self.search_var.get().strip()
        
        # 2. If empty, show everything
        if not query:
            self.refresh_list()
            return

        # 3. Otherwise, filter using your search function
        try:
            results = self.store.search_by_title(query)
            # IMPORTANT: Pass the results to refresh_list
            self.refresh_list(results) 
        except Exception as e:
            print(f"Search Error: {e}")

    def refresh_list(self, recipes=None):
        """Clears and repopulates the listbox."""
        self.recipe_listbox.delete(0, tk.END)
        
        # Use provided results, or fetch all if None
        data = recipes if recipes is not None else self.store.get_all_recipes()
        
        for r in data:
            self.recipe_listbox.insert(tk.END, r.title)

    def on_recipe_select(self, event):
        selection = self.recipe_listbox.curselection()
        if selection:
            title = self.recipe_listbox.get(selection[0])
            recipe = self.store.get_recipe(title)
            self.display_recipe_details(recipe)

    def display_recipe_details(self, recipe):
        self.title_label.config(text=recipe.title)
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        
        info = f"Servings: {recipe.servings} | Prep: {recipe.prep_time_minutes}m\n"
        info += f"Description: {recipe.description}\n"
        info += f"Tags: {', '.join(recipe.tags)}\n"
        info += "-"*30 + "\nIngredients:\n"
        for ing in recipe.ingredients:
            info += f"• {ing.amount} {ing.unit.value} {ing.name}\n"
        info += "\nInstructions:\n"
        for i, step in enumerate(recipe.instructions, 1):
            info += f"{i}. {step}\n"
            
        self.details_text.insert(tk.END, info)
        self.details_text.config(state=tk.DISABLED)

    def add_recipe_dialog(self):
        AddRecipeDialog(self.root, self, self.store)

    def delete_current(self):
        selection = self.recipe_listbox.curselection()
        if selection:
            title = self.recipe_listbox.get(selection[0])
            if messagebox.askyesno("Confirm", f"Delete {title}?"):
                self.store.delete_recipe(title)
                self.refresh_list()

    def export_to_json(self):
        import json
        from pykochbuch.storage.serialization import _recipe_to_dict
        
        # 1. Ask the user where to save
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return

        try:
            # 2. Get all data from the current store
            all_recipes = self.store.get_all_recipes()
            
            # 3. Convert recipe objects to plain dictionaries
            export_data = [_recipe_to_dict(r) for r in all_recipes]
            
            # 4. Physically write the file to the disk
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Successfully exported {len(export_data)} recipes to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def import_from_json(self):
        
        # 1. Select the file
        file_path = filedialog.askopenfilename(
            title="Select JSON Recipe File",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not file_path:
            return

        try:
            # 2. Read the JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 3. Convert and save each recipe into the CURRENT store
            count = 0
            for item in data:
                recipe = _dict_to_recipe(item)
                self.store.save_recipe(recipe)
                count += 1
            
            messagebox.showinfo("Import Success", f"Imported {count} recipes into {type(self.store).__name__}")
            self.refresh_list() # Update the UI
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not import recipes: {e}")
# --- LAUNCHER ---

def main():
    def start_app():
        mode = backend_var.get()
        launcher.destroy() 
        
        root = tk.Tk() # This is the object that has the 'tk' attribute
        try:
            if mode == "sqlite":
                store = SqliteStore(Path("cookbook.db"))
            elif mode == "json":
                store = JsonStore(Path("recipes.json"))
            else:
                store = InMemoryStore(_book=RecipeBook())
            
            # We pass 'root' to the class so the class can build things inside it
            app = CookbookGUI(root, store) 
            
            root.mainloop() # This starts the window
        except Exception as e:
            print(f"Error: {e}")
    # Launcher Window Setup
    launcher = tk.Tk()
    launcher.title("Cookbook Launcher")
    launcher.geometry("350x250")

    tk.Label(launcher, text="Administrative Access", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(launcher, text="Select Storage Backend:").pack()

    backend_var = tk.StringVar(value="sqlite")
    
    ttk.Radiobutton(launcher, text="SQLite Database (.db)", variable=backend_var, value="sqlite").pack(pady=5)
    ttk.Radiobutton(launcher, text="JSON Flat-file (.json)", variable=backend_var, value="json").pack(pady=5)
    ttk.Radiobutton(launcher, text="In-Memory (Session only)", variable=backend_var, value="memory").pack(pady=5)

    ttk.Button(launcher, text="Launch Admin Panel", command=start_app).pack(pady=20)
    launcher.mainloop()

if __name__ == "__main__":
    main()