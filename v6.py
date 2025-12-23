import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import mysql.connector
from mysql.connector import Error

# ============ DATABASE CONFIG ============
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "bgsps"
DB_NAME = "words_db"

# ============ DATABASE FUNCTIONS ============

def connect_database():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except Error as e:
        messagebox.showerror("Error", f"Database connection failed: {e}")
        return None

def close_connection(conn, cursor):
    """Close database connections"""
    if cursor:
        cursor.close()
    if conn:
        conn.close()

def get_all_words(search="", pos_filter=""):
    """Get words from database with EXACT search and parts of speech filter"""
    conn = connect_database()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = "SELECT word, meaning, synonyms, antonyms FROM words1000 WHERE 1=1"
        query_params = []
        
        # Add EXACT search condition (match only the word column)
        if search and search.strip():
            sql_query += " AND word = %s"
            query_params = [search.strip()]
        
        sql_query += " ORDER BY word ASC"
        
        cursor.execute(sql_query, query_params)
        words_list = cursor.fetchall()
        
        return words_list
    
    except Error as e:
        messagebox.showerror("Error", f"Error loading words: {e}")
        return []
    finally:
        close_connection(conn, cursor)

def get_statistics():
    """Get word statistics"""
    conn = connect_database()
    if not conn:
        return {}
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM words1000")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as count FROM words1000 WHERE synonyms != 'none'")
        with_syn = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM words1000 WHERE antonyms != 'none'")
        with_ant = cursor.fetchone()['count']
        
        return {"total": total, "synonyms": with_syn, "antonyms": with_ant}
    
    except Error as e:
        messagebox.showerror("Error", f"Error loading statistics: {e}")
        return {}
    finally:
        close_connection(conn, cursor)

def add_word(word, meaning, synonyms, antonyms):
    """Add new word to database"""
    conn = connect_database()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        if not synonyms:
            synonyms = "none"
        if not antonyms:
            antonyms = "none"
        
        sql = "INSERT INTO words1000 (word, meaning, synonyms, antonyms) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (word, meaning, synonyms, antonyms))
        conn.commit()
        
        messagebox.showinfo("Success", "Word added successfully!")
        return True
    
    except Error as e:
        messagebox.showerror("Error", f"Error adding word: {e}")
        return False
    finally:
        close_connection(conn, cursor)

def update_word(old_word, word, meaning, synonyms, antonyms):
    """Update existing word"""
    conn = connect_database()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        if not synonyms:
            synonyms = "none"
        if not antonyms:
            antonyms = "none"
        
        sql = "UPDATE words1000 SET word=%s, meaning=%s, synonyms=%s, antonyms=%s WHERE word=%s"
        cursor.execute(sql, (word, meaning, synonyms, antonyms, old_word))
        conn.commit()
        
        messagebox.showinfo("Success", "Word updated successfully!")
        return True
    
    except Error as e:
        messagebox.showerror("Error", f"Error updating word: {e}")
        return False
    finally:
        close_connection(conn, cursor)

def delete_word(word):
    """Delete word from database"""
    conn = connect_database()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        sql = "DELETE FROM words1000 WHERE word=%s"
        cursor.execute(sql, (word,))
        conn.commit()
        
        messagebox.showinfo("Success", "Word deleted successfully!")
        return True
    
    except Error as e:
        messagebox.showerror("Error", f"Error deleting word: {e}")
        return False
    finally:
        close_connection(conn, cursor)

# ============ GUI CLASS ============

class WordsDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 The Python Thesaurus - Desktop Edition")
        self.root.geometry("1100x800")
        self.root.configure(bg="#f5f5f5")
        
        self.current_words = []
        self.selected_word_index = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Create user interface"""
        
        # ========== HEADER ==========
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame,
            text="📚 The Python Thesaurus",
            font=("Arial", 22, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=12)
        
        # ========== STATISTICS ==========
        stats_frame = tk.Frame(self.root, bg="#ecf0f1")
        stats_frame.pack(fill=tk.X, padx=10, pady=8)
        
        self.total_label = tk.Label(stats_frame, text="📊 Total Words: 0", font=("Arial", 11, "bold"), bg="#ecf0f1", fg="#2c3e50")
        self.total_label.pack(side=tk.LEFT, padx=20, pady=8)
        
        self.syn_label = tk.Label(stats_frame, text="📝 With Synonyms: 0", font=("Arial", 11), bg="#ecf0f1", fg="#2c3e50")
        self.syn_label.pack(side=tk.LEFT, padx=20, pady=8)
        
        self.ant_label = tk.Label(stats_frame, text="🔄 With Antonyms: 0", font=("Arial", 11), bg="#ecf0f1", fg="#2c3e50")
        self.ant_label.pack(side=tk.LEFT, padx=20, pady=8)
        
        # ========== CONTROLS ==========
        control_frame = tk.Frame(self.root, bg="white")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Parts of Speech Filter (PRIMARY)
        tk.Label(control_frame, text="🏷️  Filter by Type:", font=("Arial", 10, "bold"), bg="white").pack(side=tk.LEFT, padx=8)
        self.pos_var = tk.StringVar(value="All")
        pos_combo = ttk.Combobox(
            control_frame,
            textvariable=self.pos_var,
            values=["All", "noun", "verb", "adjective", "adverb", "pronoun", "preposition"],
            state="readonly",
            width=15,
            font=("Arial", 9)
        )
        pos_combo.pack(side=tk.LEFT, padx=5)
        pos_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        
        # Search (exact word match)
        tk.Label(control_frame, text="🔍 Search Exact Word:", font=("Arial", 10, "bold"), bg="white").pack(side=tk.LEFT, padx=8)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=15, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_words())
        
        search_btn = tk.Button(control_frame, text="Search", command=self.search_words, bg="#3498db", fg="white", font=("Arial", 9, "bold"), padx=10)
        search_btn.pack(side=tk.LEFT, padx=3)
        
        # Add button
        add_btn = tk.Button(control_frame, text="➕ Add", command=self.open_add_window, bg="#27ae60", fg="white", font=("Arial", 9, "bold"), padx=12)
        add_btn.pack(side=tk.LEFT, padx=3)
        
        # Refresh button
        refresh_btn = tk.Button(control_frame, text="🔄 Refresh", command=self.load_data, bg="#16a085", fg="white", font=("Arial", 9, "bold"), padx=10)
        refresh_btn.pack(side=tk.LEFT, padx=3)
        
        # ========== MAIN CONTAINER ==========
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== WORD LIST ==========
        list_label = tk.Label(main_frame, text="📖 Words List", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50")
        list_label.pack(anchor=tk.W, padx=5, pady=(5, 3))
        
        list_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.words_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
            height=12,
            bg="#f9f9f9",
            activestyle="none"
        )
        self.words_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.words_listbox.bind("<<ListboxSelect>>", self.on_word_select)
        scrollbar.config(command=self.words_listbox.yview)
        
        # ========== DETAILS PANEL ==========
        detail_label = tk.Label(main_frame, text="ℹ️  Details", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50")
        detail_label.pack(anchor=tk.W, padx=5, pady=(8, 3))
        
        detail_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
        detail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=7, width=130, font=("Courier", 9), bg="#f0f0f0")
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        self.detail_text.config(state=tk.DISABLED)
        
        # ========== ACTION BUTTONS ==========
        button_frame = tk.Frame(self.root, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        edit_btn = tk.Button(button_frame, text="✏️  Edit", command=self.open_edit_window, bg="#f39c12", fg="white", font=("Arial", 10, "bold"), padx=15)
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(button_frame, text="🗑️  Delete", command=self.delete_selected, bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), padx=12)
        delete_btn.pack(side=tk.LEFT, padx=5)
    
    def load_data(self):
        """Load words from database"""
        stats = get_statistics()
        
        self.total_label.config(text=f"📊 Total Words: {stats.get('total', 0)}")
        self.syn_label.config(text=f"📝 With Synonyms: {stats.get('synonyms', 0)}")
        self.ant_label.config(text=f"🔄 With Antonyms: {stats.get('antonyms', 0)}")
        
        pos_filter = self.pos_var.get()
        if pos_filter == "All":
            pos_filter = ""
        self.current_words = get_all_words(pos_filter=pos_filter)
        self.display_words(self.current_words)
    
    def display_words(self, words):
        """Display words in listbox"""
        self.words_listbox.delete(0, tk.END)
        
        if not words:
            self.words_listbox.insert(tk.END, "❌ No words found")
            return
        
        for word in words:
            word_name = word.get('word', '?')
            meaning = word.get('meaning', '')[:40]
            
            display_text = f"• {word_name.upper():20}  {meaning}..."
            self.words_listbox.insert(tk.END, display_text)
    
    def on_word_select(self, event):
        """Show word details when selected"""
        selection = self.words_listbox.curselection()
        if not selection:
            return
        
        self.selected_word_index = selection[0]
        
        if self.selected_word_index >= len(self.current_words):
            return
        
        word_data = self.current_words[self.selected_word_index]
        
        # Get all fields safely
        word_text = word_data.get('word', 'N/A')
        meaning = word_data.get('meaning', 'N/A')
        synonyms = word_data.get('synonyms', 'none')
        antonyms = word_data.get('antonyms', 'none')
        
        detail_text = f"""
╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ WORD DETAILS
╠════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║
║  WORD:            {word_text.upper()}
║  MEANING:         {meaning}
║  SYNONYMS:        {synonyms}
║  ANTONYMS:        {antonyms}
║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
        """
        
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, detail_text)
        self.detail_text.config(state=tk.DISABLED)
    
    def search_words(self):
        """Search for exact word"""
        search_term = self.search_var.get()
        
        words = get_all_words(search=search_term)
        self.current_words = words
        self.display_words(words)
        
        if not words:
            messagebox.showinfo("Search Result", f"Word '{search_term}' not found!")
    
    def apply_filter(self):
        """Apply filter by parts of speech"""
        self.search_var.delete(0, tk.END)
        self.load_data()
    
    def open_add_window(self):
        """Open window to add new word"""
        self.open_edit_window(new=True)
    
    def open_edit_window(self, new=False):
        """Open window to edit word"""
        if not new and self.selected_word_index is None:
            messagebox.showwarning("Warning", "Please select a word first!")
            return
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Add New Word" if new else "Edit Word")
        edit_window.geometry("500x500")
        edit_window.configure(bg="white")
        
        # Title
        title = tk.Label(edit_window, text="Add New Word" if new else "Edit Word", font=("Arial", 14, "bold"), bg="white", fg="#2c3e50")
        title.pack(pady=10)
        
        # Get current data if editing
        current_data = None
        if not new:
            current_data = self.current_words[self.selected_word_index]
        
        # Form fields
        tk.Label(edit_window, text="Word:", font=("Arial", 11, "bold"), bg="white").pack(anchor=tk.W, padx=30, pady=(15, 5))
        word_entry = tk.Entry(edit_window, width=45, font=("Arial", 10), bg="#f9f9f9")
        word_entry.pack(padx=30, pady=5)
        if current_data:
            word_entry.insert(0, current_data.get('word', ''))
            word_entry.config(state=tk.DISABLED)
        
        tk.Label(edit_window, text="Meaning:", font=("Arial", 11, "bold"), bg="white").pack(anchor=tk.W, padx=30, pady=(10, 5))
        meaning_entry = tk.Entry(edit_window, width=45, font=("Arial", 10), bg="#f9f9f9")
        meaning_entry.pack(padx=30, pady=5)
        if current_data:
            meaning_entry.insert(0, current_data.get('meaning', ''))
        
        tk.Label(edit_window, text="Synonyms:", font=("Arial", 11, "bold"), bg="white").pack(anchor=tk.W, padx=30, pady=(10, 5))
        syn_entry = tk.Entry(edit_window, width=45, font=("Arial", 10), bg="#f9f9f9")
        syn_entry.pack(padx=30, pady=5)
        if current_data and current_data.get('synonyms') != 'none':
            syn_entry.insert(0, current_data.get('synonyms', ''))
        
        tk.Label(edit_window, text="Antonyms:", font=("Arial", 11, "bold"), bg="white").pack(anchor=tk.W, padx=30, pady=(10, 5))
        ant_entry = tk.Entry(edit_window, width=45, font=("Arial", 10), bg="#f9f9f9")
        ant_entry.pack(padx=30, pady=5)
        if current_data and current_data.get('antonyms') != 'none':
            ant_entry.insert(0, current_data.get('antonyms', ''))
        
        def save_word():
            word = word_entry.get().strip()
            meaning = meaning_entry.get().strip()
            synonyms = syn_entry.get().strip()
            antonyms = ant_entry.get().strip()
            
            if not word or not meaning:
                messagebox.showwarning("Warning", "Word and Meaning are required!")
                return
            
            if new:
                if add_word(word, meaning, synonyms, antonyms):
                    edit_window.destroy()
                    self.load_data()
            else:
                old_word = current_data.get('word')
                if old_word:
                    if update_word(old_word, word, meaning, synonyms, antonyms):
                        edit_window.destroy()
                        self.load_data()
                else:
                    messagebox.showerror("Error", "Could not find word")
        
        save_btn = tk.Button(edit_window, text="💾 Save Word", command=save_word, bg="#27ae60", fg="white", width=25, font=("Arial", 11, "bold"), padx=15)
        save_btn.pack(pady=25)
    
    def delete_selected(self):
        """Delete selected word"""
        if self.selected_word_index is None:
            messagebox.showwarning("Warning", "Please select a word first!")
            return
        
        word_name = self.current_words[self.selected_word_index].get('word', '?')
        
        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{word_name}'?")
        if confirm:
            if delete_word(word_name):
                self.load_data()

# ============ MAIN ============

if __name__ == "__main__":
    root = tk.Tk()
    app = WordsDatabaseApp(root)
    root.mainloop()
