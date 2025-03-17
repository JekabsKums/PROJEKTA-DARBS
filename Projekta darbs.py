import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageDraw

# Datubāzes darbības
def init_db():
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        image_path TEXT)''')
    conn.commit()
    conn.close()

def add_game(title, image_path): # Pievieno spēli datubāzei
    conn = sqlite3.connect("games.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO games (title, image_path) VALUES (?, ?)", (title, image_path))
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
        cursor.execute("SELECT * FROM games WHERE title LIKE ?", (f'%{query.strip()}%',))
    else:
        cursor.execute("SELECT * FROM games")
    games = cursor.fetchall()
    conn.close()
    
    for idx, (game_id, title, image_path) in enumerate(games):
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
        btn_delete = ttk.Button(frame_card, text="Remove", command=lambda gid=game_id: remove_game(gid))
        btn_delete.pack()

def open_file(): # Atver failu izvēlni
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    return file_path

def add_game_popup(): # Pievieno spēli
    popup = tk.Toplevel(root)
    popup.title("Add Game")
    ttk.Label(popup, text="Game Title:").pack()
    entry_title = ttk.Entry(popup)
    entry_title.pack()
    
    def save_game(): # Saglabā spēli
        title = entry_title.get()
        image_path = open_file()
        if title and image_path:
            add_game(title, image_path)
            popup.destroy()
    
    ttk.Button(popup, text="Choose Image & Save", command=save_game).pack()

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
root.geometry("600x400")
root.minsize(400, 300) # Minimālais loga izmērs

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
menu_bar.add_command(label="Exit", command=root.quit)
menu_bar.add_command(label="About", command=about_popup)

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
