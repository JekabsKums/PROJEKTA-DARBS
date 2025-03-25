import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

# Datubāzes darbības
def init_db():
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS developers ( 
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE)''') # Izstrādātāju tabula
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        image_path TEXT,
                        developer_id INTEGER,
                        FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL)''') # Spēļu tabula
    conn.commit()
    conn.close()

def add_developer(name): # Pievieno izstrādātāju datubāzei
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO developers (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Izstrādātājs jau eksistē
        pass
    conn.close()

def remove_developer(dev_id): # Izdzēš izstrādātāju no datubāzes
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM developers WHERE id = ?", (dev_id,))
    conn.commit()
    conn.close()
    load_games()

def get_developers(): # Atgriež visus izstrādātājus
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor = conn.execute("SELECT id, name FROM developers")
    developers = cursor.fetchall()
    conn.close()
    return developers

def add_game(title, image_path, developer_id): # Pievieno spēli datubāzei
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO games (title, image_path, developer_id) VALUES (?, ?, ?)", (title, image_path, developer_id))
    conn.commit()
    conn.close()
    load_games()

def remove_game(game_id): # Izdzēš spēli no datubāzes
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()
    load_games()

def load_games(query=None): # Ielādē visas spēles no datubāzes
    for widget in frame.winfo_children():
        widget.destroy()
    
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games")
    if query and query.strip():
        cursor.execute("""SELECT games.id, games.title, games.image_path, developers.name
                        FROM games
                        LEFT JOIN developers ON games.developer_id = developer.id
                        WHERE games.title LIKE ?""", (f'%{query.strip()}%',))
    else:
        cursor.execute("""SELECT games.id, games.title, games.image_path, developers.name
                        FROM games
                        LEFT JOIN developers ON games.developer_id = developers.id""")
    games = cursor.fetchall()
    conn.close()
    
    for idx, (game_id, title, image_path, dev_name) in enumerate(games):
        try:
            img = Image.open(image_path)
            img = img.resize((100, 150))
            img = ImageTk.PhotoImage(img)
        except:
            img = tk.PhotoImage(width=100, height=150)
        
        frame_card = ttk.Frame(frame, padding=5, relief="ridge")
        frame_card.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)
        label_img = tk.Label(frame_card, image=img)
        label_img.image = img  # Saglabā attēlu atmiņā
        label_img.pack()
        label_title = tk.Label(frame_card, text=title)
        label_title.pack()
        if dev_name:
            label_dev = tk.Label(frame_card, text = f"Developer: {dev_name}", font=(None, 8, 'italic'))
            label_dev.pack()
        btn_delete = ttk.Button(frame_card, text="Remove", command=lambda gid=game_id: remove_game(gid))
        btn_delete.pack()

def open_file(): # Atver failu izvēlni
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    return file_path

def add_game_popup(): # Pievieno spēli
    popup = tk.Toplevel(root)
    popup.title("Add Game")
    ttk.Label(popup, text="Game Title:").pack(pady=(10,0))
    entry_title = ttk.Entry(popup)
    entry_title.pack(pady=(0,10))

    ttk.Label(popup, text="Izvēlaties izstrādātāju:").pack(pady=(0,0))
    developers = get_developers()
    dev_options = [dev[1]for dev in developers]
    dev_var = tk.StringVar()
    combo_dev = ttk.Combobox(popup, textvariable=dev_var, values=["None"] + dev_options,state="readonly")
    combo_dev.current(0)
    combo_dev.pack(pady=(0,10))

    def save_game(): # Saglabā spēli
        title = entry_title.get()
        image_path = open_file()
        dev_selection = combo_dev.get()
        developer_id = None
        if dev_selection != "None":
            for dev in developers:
                if dev[1] == dev_selection:
                    developer_id = dev[0]
                    break
        if title and image_path:
            add_game(title, image_path, developer_id)
            popup.destroy()
    
    ttk.Button(popup, text="Choose Image & Save", command=save_game).pack()

def add_developer_popup(): # Pievieno izstrādātāju
    popup = tk.Toplevel(root)
    popup.title("Pievienot izstrādātāju")
    ttk.Label(popup, text="Izstrādātāja nosaukums:").pack(pady=(10,0))
    entry_dev = ttk.Entry(popup)
    entry_dev.pack(pady=(0,10))

    def save_developer():
        name = entry_dev.get()
        if name:
            add_developer(name)
            popup.destroy()
    ttk.Button(popup, text= "Saglabāt", command=save_developer).pack(pady=(0,10))

def manage_devs():
    popup = tk.Toplevel(root)
    popup.title("Pārvaldīt izstrādātājus")
    list_frame = ttk.Frame(popup, padding=10)
    list_frame.pack(fill="both", expand=True)

    developers = get_developers()
    for dev in developers:
        dev_id, name = dev
        frame_dev = ttk.Frame(list_frame, padding=5, relief="ridge")
        frame_dev.pack(fill="x", pady=5) 
        ttk.Label(frame_dev, text=name).pack(side="left", padx=5)
        btn_remove = ttk.Button(frame_dev, text="Noņemt", command=lambda did=dev_id: remove_dev_refresh(did, popup))
        btn_remove.pack(side="right", padx=5)

def remove_dev_refresh(dev_id, window):
    remove_developer(dev_id)
    window.destroy()
    manage_devs()


def about_popup(): # Par programmu
    tk.messagebox.showinfo("About", "Datorspēļu kolekcijas pārvaldnieka programmatūra.\nVeidoja Renārs Gricjus, Jēkabs Kūms un Kristiāns Kalniņš, 12.a, ZMGV, 2024./2025.")

def filter_games():
    query = search_entry.get()
    load_games(query)

def clear_filter():
    search_entry.delete(0, tk.END)
    load_games()


# GUI izveide
root = tk.Tk()
root.title("Game Collection")
root.geometry("600x550") # Loga izmērs
root.minsize(400, 300) # Minimālais loga izmērs

# Filtrēšanas rāmītis
filter_frame = ttk.Frame(root, padding=10)
filter_frame.pack(side="top", fill="x")
ttk.Label(filter_frame, text="Filter by Title:").pack(side="left")
search_entry = ttk.Entry(filter_frame)
search_entry.pack(side="left", padx=(5,5))
ttk.Button(filter_frame, text="Filter", command=filter_games).pack(side="left", padx=(5,5))
ttk.Button(filter_frame, text="Clear Filter", command=clear_filter).pack(side="left")


style = ttk.Style()
style.configure("TFrame", background="#f0f0f0")
style.configure("TButton", padding=5)

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)
menu_bar.add_command(label="Add Game", command=add_game_popup)
menu_bar.add_command(label="Add Developer", command=add_developer_popup)
menu_bar.add_command(label="Manage Developers", command=manage_devs)    
menu_bar.add_command(label="About", command=about_popup)
menu_bar.add_command(label="Exit", command=root.quit)


canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
frame = ttk.Frame(canvas)

frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


try:
    init_db()
    load_games()
except Exception as e:
    tk.messagebox.showerror("Error", f"Inicializācija neizdevās {str(e)}")
root.mainloop()
