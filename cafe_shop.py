import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import os
import random

# --- CONFIGURATION ---
SCALE_FACTOR = 3      
CUST_SCALE = 4  
DRINK_SCALE = 12 

def init_db():
    conn = sqlite3.connect("cafe_data.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (username TEXT PRIMARY KEY, password TEXT, coins INTEGER, served INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

class MushroomCafe:
    def __init__(self, root, username, starting_coins):
        self.root = root
        self.username = username
        self.coins = starting_coins
        self.drinks_served = 0 # Track session progress
        
        self.root.title(f'Print("coffee") Cafe - User: {self.username}')
        self.win_w, self.win_h = 1168, 554
        self.root.geometry(f"{self.win_w}x{self.win_h}")
        self.root.resizable(False, False)
        
        self.selected_ingredients = []
        self.is_animating = False 
        self.patience_value = 100
        self.timer_active = False

        self.tiers = {
            "Classic Coffee & Tea": {"unlocked": True, "price": 0},
            "Specialty & Sweet Drinks": {"unlocked": False, "price": 750},
            "Fantasy & Signature Brews": {"unlocked": False, "price": 1000}
        }

        # Recipes & Ingredients (Keeping your full list)
        self.master_menu = {
            "Latte": {"ing": ["Espresso", "Milk Bottle", "Whipped Cream"], "tier": "Classic Coffee & Tea"},
            "Cappuccino": {"ing": ["Espresso", "Milk Bottle", "Cinnamon Powder"], "tier": "Classic Coffee & Tea"},
            "Espresso": {"ing": ["Coffee Beans", "Coffee Beans"], "tier": "Classic Coffee & Tea"},
            "Mocha": {"ing": ["Espresso", "Chocolate Syrup", "Milk Bottle"], "tier": "Classic Coffee & Tea"},
            "Americano": {"ing": ["Espresso", "Hot Water"], "tier": "Classic Coffee & Tea"},
            "Iced Americano": {"ing": ["Espresso", "Water", "Ice Cubes"], "tier": "Classic Coffee & Tea"},
            "Flat White": {"ing": ["Espresso", "Milk Bottle"], "tier": "Classic Coffee & Tea"},
            "Macchiato": {"ing": ["Espresso", "Milk Foam"], "tier": "Classic Coffee & Tea"},
            "Cortado": {"ing": ["Espresso", "Milk Bottle"], "tier": "Classic Coffee & Tea"},
            "Red Eye": {"ing": ["Drip Coffee", "Espresso"], "tier": "Classic Coffee & Tea"},
            "Cafe au Lait": {"ing": ["Drip Coffee", "Milk Bottle"], "tier": "Classic Coffee & Tea"},
            "Turkish Coffee": {"ing": ["Fine Coffee Grounds", "Sugar Cubes", "Cardamom"], "tier": "Classic Coffee & Tea"},
            "Matcha Latte": {"ing": ["Matcha Powder", "Milk Bottle", "Sugar Cubes"], "tier": "Specialty & Sweet Drinks"},
            "Hot Chocolate": {"ing": ["Chocolate Syrup", "Milk Bottle", "Whipped Cream"], "tier": "Specialty & Sweet Drinks"},
            "Irish Coffee": {"ing": ["Coffee Beans", "Whiskey Syrup", "Whipped Cream"], "tier": "Specialty & Sweet Drinks"},
            "Spanish Latte": {"ing": ["Espresso", "Condensed Milk", "Milk Bottle"], "tier": "Specialty & Sweet Drinks"},
            "Affogato": {"ing": ["Espresso", "Vanilla Ice Cream"], "tier": "Specialty & Sweet Drinks"},
            "Golden Milk Latte": {"ing": ["Turmeric", "Milk Bottle", "Cinnamon Powder"], "tier": "Specialty & Sweet Drinks"},
            "Caramel Frappuccino": {"ing": ["Espresso", "Caramel Syrup", "Ice Cubes", "Whipped Cream"], "tier": "Specialty & Sweet Drinks"},
            "Iced Mocha": {"ing": ["Espresso", "Chocolate Syrup", "Ice Cubes", "Milk Bottle"], "tier": "Specialty & Sweet Drinks"},
            "Fantasy Glowing Drink": {"ing": ["Glowing Ingredient", "Sugar Cubes", "Ice Cubes"], "tier": "Fantasy & Signature Brews"},
            "Unicorn Frappe": {"ing": ["Glowing Ingredient", "Milk Bottle", "Rainbow Sprinkles", "Ice Cubes"], "tier": "Fantasy & Signature Brews"},
            "Cat Spirit Cooler": {"ing": ["Matcha Powder", "Milk Bottle", "Catnip Mint", "Ice Cubes"], "tier": "Fantasy & Signature Brews"},
            "Slime Soda": {"ing": ["Lime Syrup", "Glowing Ingredient", "Sparkling Water", "Ice Cubes"], "tier": "Fantasy & Signature Brews"}
        }

        self.ing_categories = {
            "BASES": ["Espresso", "Coffee Beans", "Drip Coffee", "Fine Coffee Grounds", "Matcha Powder", "Water", "Hot Water", "Sparkling Water"],
            "MILK & FOAM": ["Milk Bottle", "Milk Foam", "Condensed Milk", "Vanilla Ice Cream"],
            "SYRUPS & SWEETS": ["Chocolate Syrup", "Caramel Syrup", "Sugar Cubes", "Whiskey Syrup", "Lime Syrup"],
            "TOPPINGS": ["Whipped Cream", "Cinnamon Powder", "Cardamom", "Ice Cubes", "Rainbow Sprinkles"],
            "MAGICAL": ["Glowing Ingredient", "Turmeric", "Catnip Mint"]
        }

        self.load_assets()
        self.setup_ui()
        self.spawn_new_customer()

    def save_to_db(self):
        conn = sqlite3.connect("cafe_data.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coins = ? WHERE username = ?", (self.coins, self.username))
        conn.commit()
        conn.close()

    def load_assets(self):
        try: self.bg_photo = tk.PhotoImage(file="assets/bg/mushroom_bg.png").subsample(SCALE_FACTOR, SCALE_FACTOR)
        except: self.bg_photo = None
        self.customer_photos = []
        path = "assets/customers"
        if os.path.exists(path):
            for f in sorted(os.listdir(path)):
                if f.lower().endswith(".png"):
                    try: self.customer_photos.append(tk.PhotoImage(file=os.path.join(path, f)).subsample(CUST_SCALE, CUST_SCALE))
                    except: pass
        self.drink_icons = {}
        for d in self.master_menu.keys():
            p = f"assets/drinks/{d}.png"
            if os.path.exists(p):
                try: self.drink_icons[d] = tk.PhotoImage(file=p).subsample(DRINK_SCALE, DRINK_SCALE)
                except: pass

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#5d4037", width=320)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Main Canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="#2d3e30")
        self.canvas.pack(side="right", expand=True, fill="both")
        if self.bg_photo: self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        
        # UI Elements
        self.coin_display = self.canvas.create_text(70, 40, text=f"🪙 {self.coins}", fill="white", font=("Arial", 18, "bold"))
        
        # --- MENU BUTTON ---
        tk.Button(self.sidebar, text="☰ MENU", bg="#3e2723", fg="#a5d6a7", relief="flat",
                  font=("Courier", 12, "bold"), command=self.toggle_main_menu).pack(fill="x", pady=5)

        tk.Label(self.sidebar, text='Coffee Cafe', bg="#5d4037", fg="#a5d6a7", font=("Courier", 14, "bold")).pack(pady=5)
        
        # Kitchen Scroll
        self.ing_canvas = tk.Canvas(self.sidebar, bg="#5d4037", highlightthickness=0)
        ing_scroll = tk.Scrollbar(self.sidebar, orient="vertical", command=self.ing_canvas.yview)
        self.ing_frame = tk.Frame(self.ing_canvas, bg="#5d4037")
        self.ing_frame.bind("<Configure>", lambda e: self.ing_canvas.configure(scrollregion=self.ing_canvas.bbox("all")))
        self.ing_canvas.create_window((0, 0), window=self.ing_frame, anchor="nw", width=300)
        self.ing_canvas.configure(yscrollcommand=ing_scroll.set)
        self.ing_canvas.bind_all("<MouseWheel>", lambda e: self.ing_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        ing_scroll.pack(side="right", fill="y")
        self.ing_canvas.pack(side="top", fill="both", expand=True, padx=5)
        self.refresh_kitchen_buttons()
        
        self.preview_label = tk.Label(self.sidebar, text="Mixing: None", bg="#3e2723", fg="#d7ccc8", height=3, wraplength=280)
        self.preview_label.pack(pady=10, fill="x", padx=10)
        
        tk.Button(self.sidebar, text="📖 RECIPE BOOK", bg="#7b1fa2", fg="white", command=self.show_recipes).pack(fill="x", padx=40, pady=2)
        tk.Button(self.sidebar, text="🗑️ TRASH", bg="#e53935", fg="white", command=self.clear_mix).pack(fill="x", padx=40, pady=2)
        tk.Button(self.sidebar, text="SERVE", bg="#43a047", fg="white", font=("Arial", 14, "bold"), command=self.check_order).pack(side="bottom", pady=15, padx=20, fill="x")
        
        # Overlays
        self.recipe_overlay = tk.Frame(self.sidebar, bg="#3e2723")
        self.main_menu_overlay = tk.Frame(self.sidebar, bg="#1b1b1b") # Darker for the main menu

    def toggle_main_menu(self):
        """Shows/Hides the main navigation menu."""
        if self.main_menu_overlay.winfo_ismapped():
            self.main_menu_overlay.place_forget()
        else:
            for w in self.main_menu_overlay.winfo_children(): w.destroy()
            self.main_menu_overlay.place(x=0, y=0, relwidth=1, relheight=1)
            self.main_menu_overlay.lift()
            
            tk.Label(self.main_menu_overlay, text="SYSTEM MENU", bg="#1b1b1b", fg="#a5d6a7", font=("Courier", 16, "bold")).pack(pady=40)
            
            # Stats Info
            tk.Label(self.main_menu_overlay, text=f"User: {self.username}", bg="#1b1b1b", fg="white", font=("Courier", 10)).pack()
            tk.Label(self.main_menu_overlay, text=f"Served: {self.drinks_served} drinks", bg="#1b1b1b", fg="white", font=("Courier", 10)).pack(pady=5)
            
            tk.Button(self.main_menu_overlay, text="[ RETURN TO CAFE ]", bg="#4caf50", fg="white", width=20, 
                      command=self.main_menu_overlay.place_forget).pack(pady=20)
            
            tk.Button(self.main_menu_overlay, text="[ LOGOUT ]", bg="#fb8c00", fg="white", width=20, 
                      command=self.logout_action).pack(pady=5)
            
            tk.Button(self.main_menu_overlay, text="[ SHUTDOWN APP ]", bg="#b71c1c", fg="white", width=20, 
                      command=self.root.quit).pack(pady=5)

    def logout_action(self):
        if messagebox.askyesno("Confirm", "Save and logout?"):
            self.save_to_db()
            self.timer_active = False
            for widget in self.root.winfo_children(): widget.destroy()
            AuthSystem(self.root)

    def refresh_kitchen_buttons(self):
        for widget in self.ing_frame.winfo_children(): widget.destroy()
        unlocked_ings = set()
        for d in self.master_menu.values():
            if self.tiers[d["tier"]]["unlocked"]:
                for i in d["ing"]: unlocked_ings.add(i)
        for cat, items in self.ing_categories.items():
            vis = [i for i in items if i in unlocked_ings]
            if vis:
                tk.Label(self.ing_frame, text=f"~ {cat} ~", bg="#5d4037", fg="#ffcc80", font=("Arial", 9, "bold")).pack(pady=(15, 5))
                g = tk.Frame(self.ing_frame, bg="#5d4037")
                g.pack(fill="x", padx=5)
                g.columnconfigure((0,1,2), weight=1)
                for i, ing in enumerate(vis):
                    btn = tk.Button(g, text=ing, command=lambda x=ing: self.add_ing(x), bg="#8d6e63", fg="white", font=("Arial", 8), relief="flat", pady=5)
                    btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="nsew")

    def spawn_new_customer(self):
        self.is_animating = True
        self.timer_active = False 
        self.canvas.delete("customer", "bubble", "patience", "reward_txt")
        self.patience_value = 100
        unlocked = [n for n, d in self.master_menu.items() if self.tiers[d["tier"]]["unlocked"]]
        self.current_order = random.choice(unlocked)
        self.cust_x, self.cust_y = 950, self.win_h - 80
        self.target_x = (self.win_w - 320) // 2
        if self.customer_photos:
            self.active_cust_img = random.choice(self.customer_photos)
            self.canvas.create_image(self.cust_x, self.cust_y, image=self.active_cust_img, tags="customer")
        else: self.canvas.create_oval(self.cust_x-40, self.cust_y-40, self.cust_x+40, self.cust_y+40, fill="#ce93d8", tags="customer")
        self.slide_in()

    def slide_in(self):
        if self.cust_x > self.target_x:
            self.cust_x -= 12
            self.canvas.coords("customer", self.cust_x, self.cust_y)
            self.root.after(20, self.slide_in)
        else:
            self.is_animating = False
            self.show_bubble()
            self.start_patience_timer()

    def start_patience_timer(self):
        self.timer_active = True
        bx, by = self.target_x - 50, self.cust_y - 180
        self.canvas.create_rectangle(bx, by, bx+100, by+10, fill="black", tags="patience")
        self.patience_bar = self.canvas.create_rectangle(bx, by, bx+100, by+10, fill="#4caf50", tags="patience")
        self.tick_timer()

    def tick_timer(self):
        if not self.timer_active or self.is_animating: return
        self.patience_value -= 0.4 
        try:
            bx, by = self.target_x - 50, self.cust_y - 180
            self.canvas.coords(self.patience_bar, bx, by, bx + self.patience_value, by + 10)
            if self.patience_value < 30: self.canvas.itemconfig(self.patience_bar, fill="red")
            elif self.patience_value < 60: self.canvas.itemconfig(self.patience_bar, fill="orange")
            if self.patience_value <= 0:
                self.trigger_timeout()
            else: self.root.after(100, self.tick_timer)
        except: pass

    def trigger_timeout(self):
        self.timer_active = False; self.is_animating = True
        self.show_reward_txt("-15 Time Out", "red"); self.coins -= 15
        self.save_to_db()
        self.canvas.itemconfig(self.coin_display, text=f"🪙 {self.coins}")
        self.canvas.delete("bubble"); self.root.after(500, self.slide_out)

    def check_order(self):
        if self.is_animating: return
        self.timer_active = False; self.is_animating = True
        goal = self.master_menu[self.current_order]["ing"]
        is_correct = sorted(self.selected_ingredients) == sorted(goal)
        tier = self.master_menu[self.current_order]["tier"]
        reward = 30 if tier == "Classic Coffee & Tea" else 60 if "Specialty" in tier else 100
        bx, by = self.cust_x + 80, self.cust_y - 150
        self.canvas.delete("content", "patience")
        if is_correct:
            self.coins += reward; self.show_reward_txt(f"+{reward}", "#00ff00"); emoji = "😊"
            self.drinks_served += 1
        else:
            self.coins -= 20; self.show_reward_txt("-20", "red"); emoji = "💢"
        self.canvas.create_text(bx+70, by+45, text=emoji, font=("Arial", 30), tags=("bubble", "content"))
        self.canvas.itemconfig(self.coin_display, text=f"🪙 {self.coins}")
        self.save_to_db()
        self.clear_mix(); self.root.after(1000, self.slide_out)

    def slide_out(self):
        self.timer_active = False; self.canvas.delete("patience")
        if self.cust_x > -250:
            self.cust_x -= 18
            self.canvas.coords("customer", self.cust_x, self.cust_y)
            self.canvas.move("bubble", -18, 0)
            self.root.after(20, self.slide_out)
        else: self.spawn_new_customer()

    def show_reward_txt(self, text, color):
        lbl = self.canvas.create_text(self.cust_x, self.cust_y-200, text=text, fill=color, font=("Arial", 16, "bold"), tags="reward_txt")
        self.animate_reward_txt(lbl, self.cust_y-200)

    def animate_reward_txt(self, item, cy):
        if cy > self.cust_y-280:
            cy -= 2; self.canvas.coords(item, self.cust_x, cy); self.root.after(20, lambda: self.animate_reward_txt(item, cy))
        else: self.canvas.delete(item)

    def show_bubble(self):
        bx, by = self.cust_x + 80, self.cust_y - 150
        self.canvas.create_oval(bx, by, bx+140, by+90, fill="white", outline="#3e2723", width=2, tags="bubble")
        if self.current_order in self.drink_icons:
            self.canvas.create_image(bx+70, by+35, image=self.drink_icons[self.current_order], tags=("bubble", "content"))
            self.canvas.create_text(bx+70, by+68, text=self.current_order, fill="black", font=("Arial", 8, "bold"), tags=("bubble", "content"), width=120, justify="center")
        else:
            self.canvas.create_text(bx+70, by+45, text=self.current_order, fill="black", font=("Arial", 8, "bold"), tags=("bubble", "content"), width=120, justify="center")

    def show_recipes(self):
        for w in self.recipe_overlay.winfo_children(): w.destroy()
        self.recipe_overlay.place(x=0, y=0, relwidth=1, relheight=1); self.recipe_overlay.lift()
        tk.Label(self.recipe_overlay, text='FILE: recipes.py', bg="#3e2723", fg="#f3e5ab", font=("Courier", 14, "bold")).pack(pady=10)
        btn_f = tk.Frame(self.recipe_overlay, bg="#3e2723"); btn_f.pack(fill="x", padx=5, pady=5)
        for c, i in self.tiers.items():
            if not i["unlocked"]:
                tk.Button(btn_f, text=f"Unlock {c.split(' ')[0]}\n({i['price']}🪙)", bg="#ff9800", font=("Arial", 7, "bold"), command=lambda x=c: self.unlock_category(x)).pack(side="left", expand=True, padx=2)
        con = tk.Frame(self.recipe_overlay, bg="#3e2723"); con.pack(fill="both", expand=True)
        can = tk.Canvas(con, bg="#3e2723", highlightthickness=0); scr = tk.Scrollbar(con, orient="vertical", command=can.yview); frm = tk.Frame(can, bg="#3e2723")
        frm.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all"))); can.create_window((0,0), window=frm, anchor="nw", width=280); can.configure(yscrollcommand=scr.set)
        can.bind_all("<MouseWheel>", lambda e: can.yview_scroll(int(-1*(e.delta/120)), "units"))
        scr.pack(side="right", fill="y"); can.pack(side="left", fill="both", expand=True)
        sorted_d = sorted(self.master_menu.keys())
        for tn, ti in self.tiers.items():
            tk.Label(frm, text=f"--- {tn} ---", bg="#3e2723", fg="#ffcc80", font=("Arial", 9, "bold")).pack(pady=10)
            if not ti["unlocked"]: tk.Label(frm, text="[ LOCKED ]", bg="#3e2723", fg="#9e9e9e", font=("Arial", 8, "italic")).pack(); continue
            for n in sorted_d:
                if self.master_menu[n]["tier"] == tn:
                    f = tk.Frame(frm, bg="#4e342e", pady=5); f.pack(fill="x", padx=10, pady=2)
                    tk.Label(f, text=n, bg="#4e342e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w", padx=5)
                    tk.Label(f, text=" + ".join(self.master_menu[n]["ing"]), bg="#4e342e", fg="#d7ccc8", font=("Arial", 8), wraplength=240).pack(anchor="w", padx=5)
        foot = tk.Frame(self.recipe_overlay, bg="#3e2723", pady=10); foot.pack(side="bottom", fill="x")
        tk.Button(foot, text="✖ CLOSE", bg="#e53935", fg="white", font=("Arial", 11, "bold"), command=self.hide_book).pack()

    def hide_book(self):
        self.recipe_overlay.place_forget()
        self.ing_canvas.bind_all("<MouseWheel>", lambda e: self.ing_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def unlock_category(self, c):
        if self.coins >= self.tiers[c]["price"]:
            self.coins -= self.tiers[c]["price"]; self.tiers[c]["unlocked"] = True
            self.canvas.itemconfig(self.coin_display, text=f"🪙 {self.coins}")
            self.save_to_db()
            self.refresh_kitchen_buttons(); self.show_recipes()
        else: messagebox.showwarning("Locked", "Collect more coins!")

    def add_ing(self, ing):
        if self.is_animating or self.recipe_overlay.winfo_ismapped(): return
        self.selected_ingredients.append(ing)
        self.preview_label.config(text="Mixing:\n" + ", ".join(self.selected_ingredients))

    def clear_mix(self):
        self.selected_ingredients = []; self.preview_label.config(text="Mixing: None")

# --- AUTH SYSTEM ---
class AuthSystem:
    def __init__(self, root):
        self.root = root
        self.root.title('Print("coffee") Cafe - Login')
        
        # Match the game size exactly
        self.win_w, self.win_h = 1168, 554
        self.root.geometry(f"{self.win_w}x{self.win_h}")
        self.root.resizable(False, False)
        
        # 1. LOAD BACKGROUND (Landscape)
        try:
            # If the image is still too big, increase these numbers (e.g., 2, 2) 
            # to shrink it further.
            self.bg_img = tk.PhotoImage(file="assets/bg/login_bg.png")
            # If your image is 2x too big, uncomment the line below:
            # self.bg_img = self.bg_img.subsample(2, 2) 
            
            self.bg_label = tk.Label(self.root, image=self.bg_img)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except:
            self.root.configure(bg="#2d3e30")
            print("[ERROR] Login background not found.")

        self.setup_ui()

    def setup_ui(self):
        # We no longer use a 'Frame'. We place widgets directly on self.root
        # Use 'relx' and 'rely' to center them (0.5 is the middle)
        
        # TITLE
        tk.Label(self.root, text='Print ("coffe") Cafe', font=("Courier", 24, "bold"), 
                 bg="#2d3e30", fg="#a5d6a7").place(relx=0.5, rely=0.2, anchor="center")

        # USERNAME
        tk.Label(self.root, text="USERNAME", bg="#2d3e30", fg="white", font=("Courier", 12)).place(relx=0.5, rely=0.35, anchor="center")
        self.u_entry = tk.Entry(self.root, font=("Arial", 14), width=30)
        self.u_entry.place(relx=0.5, rely=0.42, anchor="center")
        
        # PASSWORD
        tk.Label(self.root, text="PASSWORD", bg="#2d3e30", fg="white", font=("Courier", 12)).place(relx=0.5, rely=0.52, anchor="center")
        self.p_entry = tk.Entry(self.root, font=("Arial", 14), show="*", width=30)
        self.p_entry.place(relx=0.5, rely=0.59, anchor="center")
        
        # BUTTONS
        tk.Button(self.root, text="[ LOGIN ]", command=self.login, 
                  bg="#4caf50", fg="white", width=20, font=("Courier", 12, "bold")).place(relx=0.5, rely=0.72, anchor="center")
        
        tk.Button(self.root, text="[ SIGN UP ]", command=self.signup, 
                  bg="#7b1fa2", fg="white", width=20, font=("Courier", 12, "bold")).place(relx=0.5, rely=0.82, anchor="center")

    def login(self):
        # strip() removes spaces, lower() ignores Capital Letters
        user = self.u_entry.get().strip().lower()
        raw_pw = self.p_entry.get().strip()
        
        if not user or not raw_pw:
            messagebox.showwarning("Access Denied", "Enter Username and Password")
            return

        pw = hash_pw(raw_pw)
        conn = sqlite3.connect("cafe_data.db")
        cur = conn.cursor()
        # Check for matching user and hashed password
        cur.execute("SELECT coins FROM users WHERE username=? AND password=?", (user, pw))
        res = cur.fetchone()
        conn.close()

        if res:
            print(f"[SYSTEM] Auth Success: {user}")
            self.launch_game(user, res[0])
        else:
            messagebox.showerror("Error", "Invalid Credentials")
    def launch_game(self, user, coins):
        # This clears every button, entry, and background on the login page
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # This starts the actual Cafe game using the data from the database
        MushroomCafe(self.root, user, coins)

    def signup(self):
        user = self.u_entry.get().strip().lower()
        raw_pw = self.p_entry.get().strip()

        if len(user) < 3 or len(raw_pw) < 3:
            messagebox.showwarning("Security", "ID/KEY must be 3+ characters")
            return

        pw = hash_pw(raw_pw)
        conn = sqlite3.connect("cafe_data.db")
        cur = conn.cursor()
        
        try:
            # We check explicitly if it exists first to give a better error
            cur.execute("SELECT username FROM users WHERE username=?", (user,))
            if cur.fetchone():
                messagebox.showerror("Conflict", f"User '{user}' already in database.")
            else:
                cur.execute("INSERT INTO users (username, password, coins) VALUES (?, ?, ?)", (user, pw, 67))
                conn.commit()
                messagebox.showinfo("Success", "Account Registered. You may now LOGIN.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not write to disk: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    AuthSystem(root)
    root.mainloop()