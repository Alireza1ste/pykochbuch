import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog, ttk
from pykochbuch.storage.serialization import _recipe_to_dict, _dict_to_recipe
from pykochbuch.storage.json_store import JsonStore
from pykochbuch.storage.sqlite_store import SqliteStore
from pykochbuch.storage.memory_store import InMemoryStore
from pykochbuch.recipe_book import RecipeBook
from pathlib import Path
import json, re
from pykochbuch.models import Recipe, Ingredient, Unit


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
        # ADD THIS LINE RIGHT HERE:
        self.show_shopping_window = lambda totals: ShoppingListWindow(self.root, totals)
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

    def get_selected_recipes(self):
        """Helper to get Recipe objects from the current Listbox selection."""
        # This returns a tuple of integers (e.g., (0, 2, 5))
        indices = self.recipe_listbox.curselection()
        
        print(f"DEBUG: Selected Indices: {indices}") # Check your terminal!

        if not indices:
            # If nothing is selected, ask to export all
            if messagebox.askyesno("Export All?", "No recipes selected. Export all available recipes?"):
                return self.store.get_all_recipes()
            return []
            
        selected_recipes = []
        for i in indices:
            # Get the title text from the listbox at that specific index
            title = self.recipe_listbox.get(i)
            # Fetch the actual recipe object from the database/json
            recipe = self.store.get_recipe(title)
            selected_recipes.append(recipe)
            
        return selected_recipes

    def export_to_sqlite(self):
        recipes_to_export = self.get_selected_recipes()
        if not recipes_to_export:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db")]
        )
        
        if file_path:
            try:
                # Initialize the new database file
                new_store = SqliteStore(db_path=Path(file_path))
                for recipe in recipes_to_export:
                    new_store.save_recipe(recipe)
                messagebox.showinfo("Success", f"Exported {len(recipes_to_export)} recipes.")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def setup_ui(self):
        # 1. INITIALIZE VARIABLES (Must be first to avoid TraceErrors)
        # These hold the state of your search filters
        self.search_var = tk.StringVar()
        self.max_prep_var = tk.StringVar(value="180") # Default to 180 mins
        
        # --- TOP: ADVANCED SEARCH & FILTER PANEL ---
        top_frame = ttk.LabelFrame(self.root, text=" 🔍 Advanced Search & Filters ", padding="10")
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Row 0, Col 0-1: Text Query
        ttk.Label(top_frame, text="Query:").grid(row=0, column=0, padx=5, sticky="e")
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=25)
        self.search_entry.grid(row=0, column=1, padx=5, sticky="w")

        # Row 0, Col 2-3: Search Mode Dropdown
        ttk.Label(top_frame, text="Search in:").grid(row=0, column=2, padx=5, sticky="e")
        self.search_mode = ttk.Combobox(top_frame, values=["Title", "Tag", "Ingredient"], state="readonly", width=12)
        self.search_mode.set("Title")
        self.search_mode.grid(row=0, column=3, padx=5, sticky="w")

        # Row 0, Col 4-5: Max Prep Time
        ttk.Label(top_frame, text="Max Prep (mins):").grid(row=0, column=4, padx=5, sticky="e")
        self.max_prep_entry = ttk.Entry(top_frame, textvariable=self.max_prep_var, width=6)
        self.max_prep_entry.grid(row=0, column=5, padx=5, sticky="w")

        # --- MIDDLE: LIST AND DETAILS (PANED WINDOW) ---
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Side: Recipe List
        list_frame = ttk.Frame(paned)
        paned.add(list_frame, weight=1)
        
        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.recipe_listbox = tk.Listbox(
            list_frame, 
            font=("Arial", 11), 
            yscrollcommand=list_scroll.set,
            exportselection=False,
            selectmode=tk.MULTIPLE  # Essential for Selective Export and Shopping List
        )
        self.recipe_listbox.pack(fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.recipe_listbox.yview)
        self.recipe_listbox.bind("<<ListboxSelect>>", self.on_recipe_select)

        # Right Side: Recipe Details
        detail_frame = ttk.Frame(paned)
        paned.add(detail_frame, weight=3)
        
        self.title_label = ttk.Label(detail_frame, text="Select a Recipe", font=("Arial", 14, "bold"))
        self.title_label.pack(pady=5, anchor="w")
        
        self.details_text = tk.Text(detail_frame, state=tk.DISABLED, wrap=tk.WORD, bg="#f9f9f9", padx=10, pady=10)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # --- BOTTOM: ACTION BUTTONS ---
        action_bar = ttk.LabelFrame(self.root, text=" Administration & Tools ", padding="10")
        action_bar.pack(fill=tk.X, padx=10, pady=10)

        # Left Side: Core Recipe Management
        ttk.Button(action_bar, text="➕ Add Recipe", command=self.add_recipe_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="🗑 Delete Selected", command=self.delete_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="🛒 Shopping List", command=self.generate_shopping_list).pack(side=tk.LEFT, padx=5)
        
        # Right Side: Data Management (Using Clear Text Labels)
        
        # SQL Group
        sql_group = ttk.Frame(action_bar)
        sql_group.pack(side=tk.RIGHT, padx=10)
        ttk.Label(sql_group, text="SQL DB:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Button(sql_group, text="Import SQL", command=self.import_from_sqlite).pack(side=tk.LEFT, padx=2)
        ttk.Button(sql_group, text="Export SQL", command=self.export_to_sqlite).pack(side=tk.LEFT, padx=2)

        # JSON Group
        json_group = ttk.Frame(action_bar)
        json_group.pack(side=tk.RIGHT, padx=10)
        ttk.Label(json_group, text="JSON File:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Button(json_group, text="Import JSON", command=self.import_from_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(json_group, text="Export JSON", command=self.export_to_json).pack(side=tk.LEFT, padx=2)

        # Global Refresh
        ttk.Button(action_bar, text="🔄 Refresh", command=lambda: self.refresh_list()).pack(side=tk.RIGHT, padx=5)

        # --- FINAL STEP: ATTACH LISTENERS ---
        # We attach these LAST so they don't fire while the UI components are still being created
        self.search_var.trace_add("write", self.run_advanced_search)
        self.max_prep_var.trace_add("write", self.run_advanced_search)
        self.search_mode.bind("<<ComboboxSelected>>", self.run_advanced_search)


    # --- LOGIC ---

    def run_advanced_search(self, *args):
        # Ensure search_mode exists before calling .get()
        if not hasattr(self, 'search_mode'):
            return

        query = self.search_var.get().strip().lower()
        mode = self.search_mode.get()
        
        try:
            val = self.max_prep_var.get().strip()
            max_prep = int(val) if val else 999
        except ValueError:
            max_prep = 999
            
        # ... the rest of your filtering logic ...
        all_data = self.store.get_all_recipes()

        # 3. Perform the filtering in Python memory
        filtered = []
        for r in all_data:
            # Check Prep Time first
            if r.prep_time_minutes > max_prep:
                continue
            
            # If there's no text query, just add based on time
            if not query:
                filtered.append(r)
                continue

            # Check Text Query based on selected Mode
            if mode == "Title":
                if query in r.title.lower():
                    filtered.append(r)
            elif mode == "Tag":
                if any(query in t.lower() for t in r.tags):
                    filtered.append(r)
            elif mode == "Ingredient":
                if any(query in i.name.lower() for i in r.ingredients):
                    filtered.append(r)

        # 4. Update the Listbox with the results
        self.refresh_list(filtered)

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
        from pykochbuch.storage.serialization import _recipe_to_dict
        import json

        # 1. Get ONLY the selected objects
        recipes_to_export = self.get_selected_recipes()
        
        # If the user canceled the "Export All?" prompt, stop here
        if not recipes_to_export:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                # 2. Convert ONLY the selected recipes
                export_data = [_recipe_to_dict(r) for r in recipes_to_export]
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Exported {len(export_data)} selected recipes.")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
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
    
    def generate_shopping_list(self):
        recipes = self.get_selected_recipes()
        if not recipes:
            return

        # Dictionary to store totals: {(name, unit): amount}
        totals = {}

        for recipe in recipes:
            for ing in recipe.ingredients:
                key = (ing.name.lower().strip(), ing.unit.value)
                totals[key] = totals.get(key, 0) + ing.amount

        self.show_shopping_window(totals)

class ShoppingListWindow(tk.Toplevel):
    def __init__(self, parent, totals):
        super().__init__(parent)
        self.title("Your Shopping List")
        self.geometry("450x550") # Slightly wider/taller for better fit
        
        # 1. Main container
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 2. Header
        tk.Label(main_frame, text="🛒 Groceries Needed:", 
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # 3. BUTTON FRAME (We pack this with side=tk.BOTTOM so it stays visible)
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        
        ttk.Button(btn_frame, text="💾 Save to .txt", 
                   command=lambda: self.save_to_file(totals)).pack(side=tk.RIGHT, padx=2)
        
        ttk.Button(btn_frame, text="📋 Copy", 
                   command=lambda: self.copy_to_clipboard(totals)).pack(side=tk.RIGHT, padx=2)

        # 4. SCROLLABLE AREA (This fills the remaining space in the middle)
        container = ttk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create checkboxes
        for (name, unit), amount in sorted(totals.items()):
            display_text = f"{amount} {unit} {name.capitalize()}"
            cb = tk.Checkbutton(scrollable_frame, text=display_text, font=("Arial", 10))
            cb.pack(anchor="w", pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def get_header(self):
        """Helper to create a consistent header with the current date."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"--- MY SHOPPING LIST ({now}) ---\n\n"

    def copy_to_clipboard(self, totals):
        header = self.get_header()
        text_list = [f"- {amt} {unit} {name.capitalize()}" 
                     for (name, unit), amt in sorted(totals.items())]
        
        full_text = header + "\n".join(text_list)
        
        self.clipboard_clear()
        self.clipboard_append(full_text)
        messagebox.showinfo("Copied", "Shopping list with date copied to clipboard!")

    def save_to_file(self, totals):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"shopping_list_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        if file_path:
            try:
                header = self.get_header()
                text_list = [f"[ ] {amt} {unit} {name.capitalize()}" 
                             for (name, unit), amt in sorted(totals.items())]
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(header)
                    f.write("\n".join(text_list))
                    f.write("\n\nGenerated by PyKochbuch")
                
                messagebox.showinfo("Success", f"Shopping list saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")


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