import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
from cryptography.fernet import Fernet
import unittest

class EncryptionManager:
    """ Klase, kas pārvalda šifrēšanu un atšifrēšanu"""
    def __init__(self, key_file = "secret.key"):
        self.key_file = key_file
        self.key = self.load_or_gen_key()
        self.fernet = Fernet(self.key)

    def load_or_gen_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as key_file:
                key_file.write(key)
            return key
        
    def encrypt(self, message):
        if isinstance(message, str):
            message = message.encode()
        return self.fernet.encrypt(message).decode()
    
    def decrypt(self, token):
        try:
            return self.fernet.decrypt(token.encode()).decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return token

# Datubāzes darbības
class DatabaseManager:
    """ Klase, kas pārvalda datubāzi  """
    def __init__(self, db_name="games.db"):
        self.db_name = db_name
        self.encryption_manager = EncryptionManager()
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS developers ( 
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE)''') # Izstrādātāju tabula
    
        cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        image_path TEXT,
                        description TEXT,
                        developer_id INTEGER,
                        FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL)''') # Spēļu tabula
        conn.commit()
        conn.close()

    def add_developer(self, name): # Pievieno izstrādātāju datubāzei
        conn = self.connect()
        cursor = conn.cursor()
        encryption_dev = self.encryption_manager.encrypt(name)
        try:
            cursor.execute("INSERT INTO developers (name) VALUES (?)", (encryption_dev,))
            conn.commit()
        except sqlite3.IntegrityError: # Izstrādātājs jau eksistē
            pass 
        conn.close()

    def remove_developer(self, dev_id): # Izdzēš izstrādātāju no datubāzes
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM developers WHERE id = ?", (dev_id,))
        conn.commit()
        conn.close()
        

    def get_developers(self): # Atgriež visus izstrādātājus
        conn = self.connect()
        cursor = conn.cursor()
        cursor = conn.execute("SELECT id, name FROM developers")
        developers = cursor.fetchall()
        conn.close()
        decry_dev = [(dev_id, self.encryption_manager.decrypt(dev_name)) for dev_id, dev_name in developers] # Atšifrē izstrādātāju nosaukumus
        return decry_dev

    def add_game(self, title, image_path, description, developer_id): # Pievieno spēli datubāzei
        conn = self.connect()
        cursor = conn.cursor()
        encry_title = self.encryption_manager.encrypt(title) # Šifrē spēles nosaukumu
        encry_image_path = self.encryption_manager.encrypt(image_path) # Šifrē attēla ceļu
        encry_description = self.encryption_manager.encrypt(description) # Šifrē spēles aprakstu
        cursor.execute("INSERT INTO games (title, image_path, description, developer_id) VALUES (?, ?, ?, ?)", (encry_title, encry_image_path, encry_description, developer_id))
        conn.commit()
        conn.close()
        

    def remove_game(self, game_id): # Izdzēš spēli no datubāzes
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
        conn.commit()
        conn.close()
        

    def get_games(self, query=None): # Ielādē visas spēles no datubāzes
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""SELECT games.id, games.title, games.image_path, games.description, developers.name
                            FROM games
                            LEFT JOIN developers ON games.developer_id = developers.id
                           """)
        games = cursor.fetchall()
        conn.close()
        decry_games = []
        for game_id, encry_title, encry_image_path, encry_description, encry_dev in games:
            title = self.encryption_manager.decrypt(encry_title)
            image_path = self.encryption_manager.decrypt(encry_image_path)
            description = self.encryption_manager.decrypt(encry_description) if encry_description is not None else None
            dev_name = self.encryption_manager.decrypt(encry_dev) if encry_dev is not None else None
            decry_games.append((game_id, title, image_path, description, dev_name))
        if query and query.strip():
            decry_games = [game for game in decry_games if query.strip().lower() in game[1].lower()] # Filtrē spēles pēc nosaukuma
        return decry_games
    
class GameCollectionApp:
    """Klase GUI izveidei"""
    def __init__(self, root): # GUI izveide
        self.root = root
        self.root.title("Game Collection")
        self.root.geometry("600x550") # Loga izmērs
        self.root.iconbitmap("icon.ico")
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_games()
        
    
    def setup_ui(self):
        # Filtrēšanas rāmītis
        self.filter_frame = ttk.Frame(self.root, padding=10)
        self.filter_frame.pack(side="top", fill="x")
        ttk.Label(self.filter_frame, text="Filter by Title:").pack(side="left")
        self.search_entry = ttk.Entry(self.filter_frame)
        self.search_entry.pack(side="left", padx=(5,5))
        ttk.Button(self.filter_frame, text="Filter", command=self.filter_games).pack(side="left", padx=(5,5))
        ttk.Button(self.filter_frame, text="Clear Filter", command=self.clear_filter).pack(side="left")
        
        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.menu_bar.add_command(label="Add Game", command=self.add_game_popup)
        self.menu_bar.add_command(label="Add Developer", command=self.add_developer_popup)
        self.menu_bar.add_command(label="Manage Developers", command=self.manage_devs)    
        self.menu_bar.add_command(label="About", command=self.about_popup)
        self.menu_bar.add_command(label="Exit", command=self.root.quit)

        # Canva, Scrollbar un Frame
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def open_file(self): # Atver failu izvēlni
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        return file_path
    
    def load_games(self, query=None): # Ielādē visas spēles no datubāzes
        for widget in self.frame.winfo_children():
            widget.destroy()
        games = self.db.get_games(query)
        for idx, (game_id, title, image_path, description,  dev_name) in enumerate(games):
            try:
                img = Image.open(image_path)
                img = img.resize((100, 150))
                img = ImageTk.PhotoImage(img)
            except:
                img = tk.PhotoImage(width=100, height=150)
        
            frame_card = ttk.Frame(self.frame, padding=5, relief="ridge")
            frame_card.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)
            label_img = tk.Label(frame_card, image=img)
            label_img.image = img  # Saglabā attēlu atmiņā
            label_img.pack()
            ttk.Label(frame_card, text=title, font=("Helvetica", 10, "bold")).pack(pady=(5,0))
            if dev_name:
                ttk.Label(frame_card, text = f"Developer: {dev_name}", font=(None, 8, 'italic')).pack()
            ttk.Button(frame_card, text="Apraksts", command=lambda desc=description: self.view_description(desc)).pack(pady=(5))
            ttk.Button(frame_card, text="Remove", command=lambda gid=game_id: self.remove_game(gid)).pack()
            
    def view_description(self, description): # Parāda spēles aprakstu
        popup = tk.Toplevel(self.root)
        popup.title("Spēles apraksts")
        text_widget = tk.Text(popup, wrap="word", width=50, height=10)
        text_widget.insert("1.0", description)
        text_widget.config(state="disabled")
        text_widget.pack(padx=10, pady=10)

    def remove_game(self, game_id):
        self.db.remove_game(game_id)
        self.load_games()

    def add_game_popup(self): # Pievieno spēli
        popup = tk.Toplevel(self.root)
        popup.title("Add Game")
        ttk.Label(popup, text="Game Title:").pack(pady=(10,0))
        entry_title = ttk.Entry(popup)
        entry_title.pack(pady=(0,10))

        ttk.Label(popup, text="Spēles apraksts:").pack(pady=(0,0))
        text_desc = tk.Text(popup, wrap="word", width=50, height=10)
        text_desc.pack(pady=(0,10))

        ttk.Label(popup, text="Izvēlaties izstrādātāju:").pack(pady=(0,0))
        developers = self.db.get_developers()
        dev_options = [dev[1]for dev in developers]
        dev_var = tk.StringVar()
        combo_dev = ttk.Combobox(popup, textvariable=dev_var, values=["None"] + dev_options,state="readonly")
        combo_dev.current(0)
        combo_dev.pack(pady=(0,10))

        def save_game(): # Saglabā spēli
            title = entry_title.get()
            description = text_desc.get("1.0", "end").strip()
            image_path = self.open_file()
            dev_selection = combo_dev.get()
            developer_id = None
            if dev_selection != "None":
                for dev in developers:
                    if dev[1] == dev_selection:
                        developer_id = dev[0]
                        break
            if title and image_path:
                self.db.add_game(title, image_path, description, developer_id)
                popup.destroy()
                self.load_games()
    
        ttk.Button(popup, text="Choose Image & Save", command=save_game).pack()

    def add_developer_popup(self): # Pievieno izstrādātāju
        popup = tk.Toplevel(self.root)
        popup.title("Pievienot izstrādātāju")
        ttk.Label(popup, text="Izstrādātāja nosaukums:").pack(pady=(10,0))
        entry_dev = ttk.Entry(popup)
        entry_dev.pack(pady=(0,10))

        def save_developer():
            name = entry_dev.get()
            if name:
                self.db.add_developer(name)
                popup.destroy()
        ttk.Button(popup, text= "Saglabāt", command=save_developer).pack(pady=(0,10))

    def manage_devs(self):
        popup = tk.Toplevel(self.root)
        popup.title("Pārvaldīt izstrādātājus")
        list_frame = ttk.Frame(popup, padding=10)
        list_frame.pack(fill="both", expand=True)

        developers = self.db.get_developers()
        for dev in developers:
            dev_id, name = dev
            frame_dev = ttk.Frame(list_frame, padding=5, relief="ridge")
            frame_dev.pack(fill="x", pady=5) 
            ttk.Label(frame_dev, text=name).pack(side="left", padx=5)
            ttk.Button(frame_dev, text="Noņemt", command=lambda did=dev_id: self.remove_dev_refresh(did, popup)).pack(side="right", padx=5)

            
    def remove_dev_refresh(self, dev_id, window):
        self.db.remove_developer(dev_id)
        window.destroy()
        self.manage_devs()
        self.load_games()


    def about_popup(self): # Par programmu
        tk.messagebox.showinfo("About", "Datorspēļu kolekcijas pārvaldnieka programmatūra.\nVeidoja Renārs Gricjus, Jēkabs Kūms un Kristiāns Kalniņš, 12.a, ZMGV, 2024./2025.")

    def filter_games(self):
        query = self.search_entry.get()
        self.load_games(query)

    def clear_filter(self):
        self.search_entry.delete(0, tk.END)
        self.load_games()

class TestDatabaseManager(unittest.TestCase):
    """ Testē datubāzes funkcionalitāti """
    def setUp(self):
        self.db = DatabaseManager("test.db")
        self.db.init_db()

    def tearDown(self):
        if os.path.exists("test.db"):
            os.remove("test.db")
    
    def test_add_developer(self):
        self.db.add_developer("Test Developer")
        developers = self.db.get_developers()
        self.assertEqual(len(developers), 1)
        self.assertEqual(developers[0][1], "Test Developer")

    def test_add_game(self):
        self.db.add_developer("Test Developer")
        dev_id = self.db.get_developers()[0][0]
        self.db.add_game("Test Game", "path/to/test_image.png", "Great Game!", dev_id)
        games = self.db.get_games()
        self.assertEqual(games[0][1], "Test Game")
        self.assertEqual(games[0][3], "Great Game!")


if __name__ == "__main__":
    unittest.main(exit=False)
    root = tk.Tk()
    app = GameCollectionApp(root)
    root.mainloop()


