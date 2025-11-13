import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta



# --- STAŁE DLA APLIKACJI ---
DATABASE_FILE = "databases/data.db"
DATE_FORMAT = '%Y-%m-%d'

class SystemRezerwacjiPensjonatu:
    def __init__(self, master):
        self.master = master
        master.title("SRPP - System Rezerwacji Pokoi Pensjonatu ")
        master.geometry("1000x650")
        
        # Inicjalizacja połączenia z bazą (BEZ logiki jej tworzenia)
        self.conn = self.utworz_polaczenie()
        if not self.conn:
            messagebox.showerror("Błąd Startu", "Brak połączenia z bazą danych. Uruchom bazę_danych.py.")
            master.destroy()
            return
        
        self.utworz_interfejs()

    def utworz_polaczenie(self,db_file=DATABASE_FILE):
        """Tworzy połączenie z bazą danych lub ją otwiera."""
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwach
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            print(f"Błąd połączenia z bazą danych: {e}")
            return None


    def oblicz_cene(self, pokoj_id, data_start_str, data_koniec_str, liczba_osob):
            """Kalkulacja ceny za cały pobyt, uwzględniająca mnożnik pokoju i sezon (WF.03)."""
            data_start = datetime.strptime(data_start_str, DATE_FORMAT)
            data_koniec = datetime.strptime(data_koniec_str, DATE_FORMAT)
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT Cena_Bazowa_Mnożnik, Liczba_Miejsc_Noclegowych FROM POKOJ WHERE ID_Pokoju=?", (pokoj_id,))
            pokoj = cursor.fetchone()
            
            if not pokoj: return 0.0

            CENA_BAZOWA_DZIEN = 150.0  
            cena_calkowita = 0.0
            
            # 1. Obliczanie ceny dzień po dniu (iteracja po nocach)
            current_date = data_start
            while current_date < data_koniec:
                current_date_str = current_date.strftime(DATE_FORMAT)
                
                # Pobranie mnożnika sezonowego dla aktualnej nocy
                sql_cennik = """
                SELECT Mnożnik_Cenowy FROM CENNIK
                WHERE ? BETWEEN Data_Początkowa_Okresu AND Data_Końcowa_Okresu
                """
                cursor.execute(sql_cennik, (current_date_str,))
                wynik_cennik = cursor.fetchone()
                
                mnoznik_sezonowy = wynik_cennik['Mnożnik_Cenowy'] if wynik_cennik else 1.0
                
                # Cena bazowa * Mnożnik Pokoju * Mnożnik Sezonowy
                cena_za_noc = CENA_BAZOWA_DZIEN * pokoj['Cena_Bazowa_Mnożnik'] * mnoznik_sezonowy
                
                cena_calkowita += cena_za_noc
                current_date += timedelta(days=1)
                
            # 2. Zastosowanie zniżek za obłożenie na całość
            if liczba_osob < pokoj['Liczba_Miejsc_Noclegowych']:
                cena_calkowita *= 0.95 
                
            return round(cena_calkowita, 2)

    def jest_dostepny(self, pokoj_id, data_start_str, data_koniec_str):
            """
            Sprawdza kolizje rezerwacji w bazie.
            Używa formuły, która identyfikuje, kiedy rezerwacja w bazie 
            nakłada się na szukany termin (uwzględniając stykające się daty).
            """
            cursor = self.conn.cursor()
            
            sql = """
            SELECT ID_Rezerwacji 
            FROM REZERWACJA
            WHERE ID_Pokoju = ?
            AND Status IN ('Wstępna', 'Obowiązująca')
            -- Kolizja następuje, gdy rezerwacja w bazie NIE jest ani przed, ani po szukanym terminie.
            AND NOT (
                Data_Końcowa <= ? -- Rezerwacja kończy się w dniu lub przed szukanym startem
                OR 
                Data_Początkowa >= ? -- Rezerwacja zaczyna się w dniu lub po szukanym końcu
            );
            """
        
            cursor.execute(sql, (pokoj_id, data_start_str, data_koniec_str))
            if cursor.fetchone() is None:
                return True

            else:
                return False

    def pobierz_wolne_pokoje(self, data_start, data_koniec, liczba_osob, filtr_widok):
        """Pobiera i filtruje pokoje (WF.02)."""
        dostepne = []
        cursor = self.conn.cursor()
        
        sql = "SELECT * FROM POKOJ WHERE Status_Dostępności_Okresowej = 'Dostępny'"
        
        if liczba_osob:
            sql += f" AND Liczba_Miejsc_Noclegowych >= {liczba_osob}"
        
        if filtr_widok:
            sql += " AND Widok_Na_Morze = 1"
            
        cursor.execute(sql)
        wszystkie_pokoje = cursor.fetchall()

        for pokoj in wszystkie_pokoje:
            if self.jest_dostepny(pokoj['ID_Pokoju'], data_start, data_koniec):
                cena = self.oblicz_cene(pokoj['ID_Pokoju'], data_start, data_koniec, liczba_osob)
                dostepne.append({
                    'ID': pokoj['ID_Pokoju'],
                    'Numer': pokoj['Numer_Pokoju'],
                    'Miejsca': pokoj['Liczba_Miejsc_Noclegowych'],
                    'Piętro': pokoj['Piętro'],
                    'Widok': 'Tak' if pokoj['Widok_Na_Morze'] else 'Nie',
                    'Cena': cena
                })
        return dostepne

    # --- INTERFEJS UŻYTKOWNIKA (WN.01) ---

    def utworz_interfejs(self):
        """Tworzy layout GUI."""
        
        self.panel_wyszukiwania = ttk.LabelFrame(self.master, text="Parametry Wyszukiwania")
        self.panel_wyszukiwania.pack(side=tk.LEFT, padx=10, pady=10, fill='y')

        self.panel_wynikow = ttk.LabelFrame(self.master, text="Dostępne Pokoje (WF.02) i Rezerwacja")
        self.panel_wynikow.pack(side=tk.RIGHT, padx=10, pady=10, fill='both', expand=True)

        self._utworz_filtry(self.panel_wyszukiwania)
        self._utworz_wyniki_i_akcje(self.panel_wynikow)
        
    def _utworz_filtry(self, frame):
        
        tk.Label(frame, text="Data Przyjazdu (YYYY-MM-DD):").grid(row=0, column=0, sticky='w', pady=5)
        self.entry_przyjazd = ttk.Entry(frame)
        self.entry_przyjazd.grid(row=1, column=0, padx=5, pady=2)
        self.entry_przyjazd.insert(0, (datetime.now() + timedelta(days=7)).strftime(DATE_FORMAT))

        tk.Label(frame, text="Data Wyjazdu (YYYY-MM-DD):").grid(row=2, column=0, sticky='w', pady=5)
        self.entry_wyjazd = ttk.Entry(frame)
        self.entry_wyjazd.grid(row=3, column=0, padx=5, pady=2)
        self.entry_wyjazd.insert(0, (datetime.now() + timedelta(days=10)).strftime(DATE_FORMAT))
        
        tk.Label(frame, text="Liczba Osób:").grid(row=4, column=0, sticky='w', pady=5)
        self.liczba_osob = tk.StringVar(value='2')
        ttk.Spinbox(frame, from_=1, to=8, textvariable=self.liczba_osob, width=18).grid(row=5, column=0, padx=5, pady=2)

        tk.Label(frame, text="Filtry:").grid(row=6, column=0, sticky='w', pady=5)
        self.widok_morze = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Widok na Morze", variable=self.widok_morze).grid(row=7, column=0, sticky='w', padx=5, pady=2)

        ttk.Button(frame, text="Wyszukaj Pokoje (WF.02)", command=self.akcja_wyszukaj).grid(row=8, column=0, padx=5, pady=20)

    def _utworz_wyniki_i_akcje(self, frame):
        
        self.tree = ttk.Treeview(frame, columns=("Numer", "Miejsca", "Piętro", "Widok", "Cena"), show='headings')
        self.tree.heading("Numer", text="Numer Pokoju", anchor=tk.W)
        self.tree.heading("Miejsca", text="Miejsca", anchor=tk.W)
        self.tree.heading("Piętro", text="Piętro", anchor=tk.W)
        self.tree.heading("Widok", text="Widok", anchor=tk.W)
        self.tree.heading("Cena", text="Cena Całkowita (WF.03)", anchor=tk.W)
        
        self.tree.column("#0", width=80, stretch=tk.NO) 
        self.tree.column("Numer", width=90, stretch=tk.NO)
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.akcja_wybrano_pokoj)

        self.frame_akcji = ttk.LabelFrame(frame, text="Rejestracja Rezerwacji (WF.05)")
        self.frame_akcji.pack(fill='x', pady=5, padx=5)
        
        tk.Label(self.frame_akcji, text="Cena Gwarantowana (WF.04):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_cena_gwarantowana = ttk.Entry(self.frame_akcji, width=15)
        self.entry_cena_gwarantowana.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        tk.Label(self.frame_akcji, text="Nazwisko Klienta:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entry_nazwisko_klienta = ttk.Entry(self.frame_akcji, width=20)
        self.entry_nazwisko_klienta.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        self.btn_rezerwuj = ttk.Button(self.frame_akcji, text="Zarezerwuj Wstępnie", command=self.akcja_rezerwuj_wstepnie, state=tk.DISABLED)
        self.btn_rezerwuj.grid(row=1, column=2, padx=15, pady=5)

    # --- AKCJE I ZDARZENIA ---

    def waliduj_daty(self, data_str):
        try:
            return datetime.strptime(data_str, DATE_FORMAT).strftime(DATE_FORMAT)
        except ValueError:
            return None

    def akcja_wyszukaj(self):
        
        data_start = self.waliduj_daty(self.entry_przyjazd.get())
        data_koniec = self.waliduj_daty(self.entry_wyjazd.get())
        
        try:
            liczba_osob = int(self.liczba_osob.get())
        except ValueError:
            liczba_osob = 1
        
        if not data_start or not data_koniec or data_start >= data_koniec:
            messagebox.showerror("Błąd Walidacji", "Sprawdź poprawność dat (YYYY-MM-DD) i zakres.")
            return

        for i in self.tree.get_children():
            self.tree.delete(i)
        self.btn_rezerwuj.config(state=tk.DISABLED)
        self.entry_cena_gwarantowana.delete(0, tk.END)

        wolne_pokoje = self.pobierz_wolne_pokoje(data_start, data_koniec, liczba_osob, self.widok_morze.get())

        for pokoj in wolne_pokoje:
            self.tree.insert("", tk.END, text=pokoj['Numer'], values=(
                pokoj['Numer'], 
                pokoj['Miejsca'], 
                pokoj['Piętro'], 
                pokoj['Widok'], 
                f"{pokoj['Cena']} PLN")
                ,tags=(f"id_{pokoj['ID']}",)) # Przechowujemy ID jako TAG
            
        if not wolne_pokoje:
            messagebox.showinfo("Brak Pokoi", "Nie znaleziono dostępnych pokoi spełniających kryteria.")
            
    def akcja_wybrano_pokoj(self, event):
        try:
            selected_item = self.tree.selection()[0]
            values = self.tree.item(selected_item, 'values')
            cena_str = values[4].replace(" PLN", "")
            
            self.entry_cena_gwarantowana.delete(0, tk.END)
            self.entry_cena_gwarantowana.insert(0, cena_str) 
            self.btn_rezerwuj.config(state=tk.NORMAL)
            
        except IndexError:
            self.btn_rezerwuj.config(state=tk.DISABLED)
            self.entry_cena_gwarantowana.delete(0, tk.END)
            
    def akcja_rezerwuj_wstepnie(self):
        
        if not self.conn:
             messagebox.showerror("Błąd", "Brak połączenia z bazą danych.")
             return
             
        try:
            selected_item = self.tree.selection()[0]
            tags = self.tree.item(selected_item, 'tags')
            print(tags)
            id_tag = [tag for tag in tags if tag.startswith('id_')][0]
            pokoj_id = int(id_tag.split('_')[1])
            pokoj_numer = self.tree.item(selected_item, 'text')
            
            data_start = self.entry_przyjazd.get()
            data_koniec = self.entry_wyjazd.get()
            liczba_osob = int(self.liczba_osob.get())
            cena_gwarantowana = float(self.entry_cena_gwarantowana.get()) 
            nazwisko_klienta = self.entry_nazwisko_klienta.get().strip()

            if not nazwisko_klienta:
                messagebox.showerror("Błąd", "Wprowadź nazwisko klienta.")
                return

            cursor = self.conn.cursor()
            
            # Uproszczona obsługa klienta (WF.07)
            cursor.execute("SELECT ID_Klienta FROM KLIENT WHERE Nazwisko=? LIMIT 1", (nazwisko_klienta,))
            klient = cursor.fetchone()
            
            if klient:
                klient_id = klient[0]
            else:
                cursor.execute("INSERT INTO KLIENT (Imię, Nazwisko) VALUES (?, ?)", ("N/A", nazwisko_klienta))
                klient_id = cursor.lastrowid
                
            # Rejestracja rezerwacji (WF.05)
            sql = """
            INSERT INTO REZERWACJA (ID_Pokoju, ID_Klienta, Data_Rezerwacji, Data_Początkowa, Data_Końcowa, Liczba_Osób, Cena_Gwarantowana, Status, Termin_Ważności_Zaliczki) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            data_rezerwacji = datetime.now().strftime(DATE_FORMAT)
            termin_zaliczki = (datetime.now() + timedelta(days=3)).strftime(DATE_FORMAT) 
            
            cursor.execute(sql, (
                pokoj_id, klient_id, data_rezerwacji, data_start, data_koniec, 
                liczba_osob, cena_gwarantowana, 'Wstępna', termin_zaliczki
            ))
            self.conn.commit()
            
            messagebox.showinfo("Rezerwacja Wstępna", 
                                f"Pokój {pokoj_numer} zarezerwowany wstępnie dla {nazwisko_klienta}.\n"
                                f"Cena: {cena_gwarantowana} PLN.\n"
                                f"Termin ważności zaliczki: {termin_zaliczki}.")
            
            self.akcja_wyszukaj()

        except IndexError:
            messagebox.showerror("Błąd", "Wybierz pokój z listy.")
        except ValueError:
            messagebox.showerror("Błąd", "Cena gwarantowana jest niepoprawna.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił nieoczekiwany błąd: {e}")

    def __del__(self):
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = SystemRezerwacjiPensjonatu(root)
    root.mainloop()