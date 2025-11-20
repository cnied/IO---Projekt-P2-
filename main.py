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
        master.geometry("1200x650")
        
        # Inicjalizacja połączenia z bazą
        self.conn = self.utworz_polaczenie()
        if not self.conn:
            messagebox.showerror("Błąd Startu", "Brak połączenia z bazą danych. Uruchom bazę_danych.py.")
            master.destroy()
            return
        
        # Słownik do przechowywania ramek dla przełączania widoków
        self.frames = {} 
        
        self._utworz_menu()
        self._utworz_ramki()
        
        # Domyślne wyświetlenie widoku rezerwacji
        self._pokaz_ramke('Rezerwacja')
        
    def utworz_polaczenie(self,db_file=DATABASE_FILE):
        """Tworzy połączenie z bazą danych lub ją otwiera."""
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            print(f"Błąd połączenia z bazą danych: {e}")
            return None

    # --- FUNKCJE MENU I NAWIGACJI  ---
    
    def _utworz_menu(self):
        """Tworzy pasek menu na górze okna."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        operacje_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Operacje", menu=operacje_menu)
        
        # Opcja 1: Rezerwuj
        operacje_menu.add_command(label="Rezerwuj Pokoje", 
                                 command=lambda: self._pokaz_ramke('Rezerwacja'))
                                 
        # Opcja 2: Potwierdź Płatność/Zaliczka
        operacje_menu.add_command(label="Potwierdź Płatność/Zaliczka", 
                                 command=lambda: self._pokaz_ramke('Platnosc'))
        
        # NOWA OPCJA: Klienci
        operacje_menu.add_command(label="Zarządzanie Klientami", 
                                 command=lambda: self._pokaz_ramke('Klienci'))
                                 
        operacje_menu.add_separator()
        operacje_menu.add_command(label="Wyjście", command=self.master.destroy)
        
    def _utworz_ramki(self):
        """Tworzy ramki dla różnych widoków i ustawia kontener."""
        container = ttk.Frame(self.master)
        container.pack(side="top", fill="both", expand=True)

        # 1. Ramka Rezerwacji
        ramka_rezerwacji = ttk.Frame(container)
        ramka_rezerwacji.grid(row=0, column=0, sticky="nsew")
        self.frames['Rezerwacja'] = ramka_rezerwacji
        self._utworz_widok_rezerwacji(ramka_rezerwacji)
        
        # 2. Ramka Płatności
        ramka_platnosci = ttk.Frame(container)
        ramka_platnosci.grid(row=0, column=0, sticky="nsew")
        self.frames['Platnosc'] = ramka_platnosci
        self._utworz_widok_platnosci(ramka_platnosci)
        
        # 3. NOWA RAMKA: Klienci
        ramka_klienci = ttk.Frame(container)
        ramka_klienci.grid(row=0, column=0, sticky="nsew")
        self.frames['Klienci'] = ramka_klienci
        self._utworz_widok_klientow(ramka_klienci) # Wywołanie nowej funkcji
        
    def _pokaz_ramke(self, nazwa_ramki):
        """Podnosi wybraną ramkę na wierzch i odświeża dane."""
        frame = self.frames[nazwa_ramki]
        frame.tkraise()
        
        if nazwa_ramki == 'Platnosc':
            self._zaladuj_rezerwacje_do_potwierdzenia()
        elif nazwa_ramki == 'Klienci': # NOWE
            self._zaladuj_liste_klientow()
            
    # --- WIDOK 1 - RAMKA REZERWACJI ---------------------------------------------------------------------------------------------------
    
    def _utworz_widok_rezerwacji(self, master_frame):
        """Inicjalizuje interfejs rezerwacji (WF.02/WF.05)."""
        
        # Zastępuje Twoją starą funkcję utworz_interfejs(self)
        self.panel_wyszukiwania = ttk.LabelFrame(master_frame, text="Parametry Wyszukiwania")
        self.panel_wyszukiwania.pack(side=tk.LEFT, padx=10, pady=10, fill='y')

        self.panel_wynikow = ttk.LabelFrame(master_frame, text="Dostępne Pokoje (WF.02) i Rezerwacja")
        self.panel_wynikow.pack(side=tk.RIGHT, padx=10, pady=10, fill='both', expand=True)

        self._utworz_filtry(self.panel_wyszukiwania)
        self._utworz_wyniki_i_akcje(self.panel_wynikow)
        
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
        
        current_date = data_start
        while current_date < data_koniec:
            current_date_str = current_date.strftime(DATE_FORMAT)
            
            sql_cennik = """
            SELECT Mnożnik_Cenowy FROM CENNIK
            WHERE ? BETWEEN Data_Początkowa_Okresu AND Data_Końcowa_Okresu
            """
            cursor.execute(sql_cennik, (current_date_str,))
            wynik_cennik = cursor.fetchone()
            
            mnoznik_sezonowy = wynik_cennik['Mnożnik_Cenowy'] if wynik_cennik else 1.0
            
            cena_za_noc = CENA_BAZOWA_DZIEN * pokoj['Cena_Bazowa_Mnożnik'] * mnoznik_sezonowy
            
            cena_calkowita += cena_za_noc
            current_date += timedelta(days=1)
            
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
        AND NOT (
            Data_Końcowa <= ? 
            OR 
            Data_Początkowa >= ?
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
        
    def waliduj_daty(self, data_str):

        try:
            return datetime.strptime(data_str, DATE_FORMAT).strftime(DATE_FORMAT)
        except ValueError:
            return None

    def _utworz_filtry(self, frame):
        """Inicjalizuje i rozmieszcza elementy interfejsu użytkownika
        służące do definiowania kryteriów wyszukiwania dostępnych pokoi."""
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
        """Inicjalizuje główny panel interfejsu odpowiedzialny za wyświetlanie
        wyników wyszukiwania pokoi (WF.02) oraz sekcję formularza do
        rejestracji wstępnej rezerwacji (WF.05)."""
        self.tree = ttk.Treeview(frame, columns=("Numer", "Miejsca", "Piętro", "Widok", "Cena"), show='headings')
        # ... (pozostały kod Treeview pozostaje bez zmian)
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
        
        # --- ZMIANA: Pole na Nazwisko Klienta i Przycisk Wyboru ---
        tk.Label(self.frame_akcji, text="Wybrany Klient:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        # Pole do wyświetlania nazwiska (tylko do odczytu)
        self.entry_nazwisko_klienta = ttk.Entry(self.frame_akcji, width=20, state='readonly') 
        self.entry_nazwisko_klienta.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Zapis ID wybranego klienta
        self.wybrany_klient_id = None 
        
        # Przycisk otwierający okno wyboru klienta
        self.btn_wybierz_klienta = ttk.Button(self.frame_akcji, text="Wybierz Klienta", command=self.akcja_wybierz_klienta)
        self.btn_wybierz_klienta.grid(row=1, column=2, padx=5, pady=5)
        
        # Przycisk Rezerwacji (przeniesiony do wiersza 2)
        self.btn_rezerwuj = ttk.Button(self.frame_akcji, text="Zarezerwuj Wstępnie", command=self.akcja_rezerwuj_wstepnie, state=tk.DISABLED)
        self.btn_rezerwuj.grid(row=2, column=2, padx=15, pady=5)

        
    def akcja_wybierz_klienta(self):
        """Otwiera okno dialogowe wyboru klienta z tabeli KLIENT."""
        
        if not self.conn:
            messagebox.showerror("Błąd", "Brak połączenia z bazą danych.")
            return

        # Tworzenie nowego okna dialogowego
        okno_wyboru = tk.Toplevel(self.master)
        okno_wyboru.title("Wybór Klienta (WF.07)")
        okno_wyboru.transient(self.master) # Ustawia nad oknem głównym
        okno_wyboru.grab_set() # Blokuje interakcję z innymi oknami
        okno_wyboru.geometry("400x300")

        # Wypełnienie listy klientów
        tree_klientow = ttk.Treeview(okno_wyboru, columns=("ID", "Imię", "Nazwisko"), show='headings')
        tree_klientow.heading("ID", text="ID", anchor=tk.W)
        tree_klientow.heading("Imię", text="Imię", anchor=tk.W)
        tree_klientow.heading("Nazwisko", text="Nazwisko", anchor=tk.W)
        tree_klientow.column("ID", width=40, stretch=tk.NO)
        tree_klientow.pack(fill='both', expand=True, padx=5, pady=5)

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ID_Klienta, Imię, Nazwisko FROM KLIENT ORDER BY Nazwisko, Imię")
            klienci = cursor.fetchall()

            for klient in klienci:
                klient_data = tuple(klient) 
                tree_klientow.insert('', tk.END, text='', values=klient_data)

        except Exception as e:
            messagebox.showerror("Błąd Bazy Danych", f"Nie udało się wczytać klientów: {e}")
            okno_wyboru.destroy()
            return
            
        # Przycisk "Wybierz"
        def akcja_wybierz():
            selected_item = tree_klientow.selection()
            if selected_item:
                klient_data = tree_klientow.item(selected_item[0], 'values')
                
                # Ustawienie zmiennych w głównym obiekcie
                self.wybrany_klient_id = klient_data[0]
                nazwisko = klient_data[2]
                
                # Wprowadzenie nazwiska do pola Entry (wymaga tymczasowej zmiany stanu)
                self.entry_nazwisko_klienta.config(state='normal')
                self.entry_nazwisko_klienta.delete(0, tk.END)
                self.entry_nazwisko_klienta.insert(0, nazwisko)
                self.entry_nazwisko_klienta.config(state='readonly')
                
                okno_wyboru.destroy()
            else:
                messagebox.showwarning("Ostrzeżenie", "Wybierz klienta z listy.")

        # Obsługa podwójnego kliknięcia
        tree_klientow.bind('<Double-1>', lambda event: akcja_wybierz())

        btn_wybierz = ttk.Button(okno_wyboru, text="Wybierz", command=akcja_wybierz)
        btn_wybierz.pack(pady=5)
        
        # Czekaj aż okno zostanie zamknięte
        self.master.wait_window(okno_wyboru) 
        
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
            # print(tags) # Usunięto print
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
            
    # ---WIDOK 3 KLIENCI ----------------------------------------------------------------------------------------------------
    
    def _utworz_widok_klientow(self, master_frame):
        """Inicjalizuje interfejs dla zarządzania klientami (WF.07)."""
        
        # Lewy panel: Dodawanie/Wyszukiwanie/Edycja
        panel_kontrolny = ttk.LabelFrame(master_frame, text="Operacje na Klientach")
        panel_kontrolny.pack(side=tk.LEFT, padx=10, pady=10, fill='y')
        
        # Zmienne stanu
        self.edytowany_klient_id = None 
        self.var_lojalny_nowy = tk.IntVar() # NOWA ZMIENNA DLA CHECKBOXA

        # --- A. Wyszukiwanie ---
        # ... (kod wyszukiwania bez zmian) ...
        tk.Label(panel_kontrolny, text="Wyszukaj Nazwisko:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_szukaj_klienta = ttk.Entry(panel_kontrolny, width=25)
        self.entry_szukaj_klienta.grid(row=1, column=0, padx=5, pady=2)
        self.entry_szukaj_klienta.bind('<KeyRelease>', self._akcja_szukaj_klienta)
        
        tk.Label(panel_kontrolny, text="Wpisz, aby filtrować listę. ↑").grid(row=2, column=0, padx=5, pady=1, sticky='w')
        
        ttk.Separator(panel_kontrolny, orient='horizontal').grid(row=3, column=0, sticky='ew', pady=10)

        # --- B. Pola Danych Klienta (Wspólne dla Dodawania i Edycji) ---
        panel_dane = ttk.LabelFrame(panel_kontrolny, text="Dane Klienta (Edytuj / Dodaj)")
        panel_dane.grid(row=4, column=0, padx=5, pady=5, sticky='ew')
        
        # Imię
        tk.Label(panel_dane, text="Imię:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_imie_nowy = ttk.Entry(panel_dane, width=25)
        self.entry_imie_nowy.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Nazwisko
        tk.Label(panel_dane, text="Nazwisko:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entry_nazwisko_nowy = ttk.Entry(panel_dane, width=25)
        self.entry_nazwisko_nowy.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Telefon
        tk.Label(panel_dane, text="Telefon:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.entry_telefon_nowy = ttk.Entry(panel_dane, width=25)
        self.entry_telefon_nowy.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # Email
        tk.Label(panel_dane, text="Email:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.entry_email_nowy = ttk.Entry(panel_dane, width=25)
        self.entry_email_nowy.grid(row=3, column=1, padx=5, pady=5, sticky='w')

        # Adres
        tk.Label(panel_dane, text="Adres:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.entry_adres_nowy = ttk.Entry(panel_dane, width=25)
        self.entry_adres_nowy.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        
        # Stały Klient (NOWE POLE)
        ttk.Checkbutton(panel_dane, 
                        text="Stały Klient (10% zniżki)", 
                        variable=self.var_lojalny_nowy,
                        onvalue=1,
                        offvalue=0).grid(row=5, column=0, columnspan=2, pady=10, sticky='w')
        
        # --- C. Przyciski Akcji ---
        frame_przyciski = ttk.Frame(panel_kontrolny)
        frame_przyciski.grid(row=6, column=0, padx=5, pady=10, sticky='ew') # Zmieniono row na 6
        
        # Przycisk dodawania (funkcja bez zmian)
        ttk.Button(frame_przyciski, text="Dodaj Nowego", command=self._akcja_dodaj_klienta).pack(side=tk.LEFT, expand=True, fill='x')
        
        # Przycisk edycji (NOWY)
        self.btn_edytuj = ttk.Button(frame_przyciski, text="Edytuj Zaznaczonego", command=self._akcja_edytuj_klienta, state=tk.DISABLED)
        self.btn_edytuj.pack(side=tk.RIGHT, expand=True, fill='x')

        # Prawy panel: Lista Klientów
        panel_lista = ttk.LabelFrame(master_frame, text="Lista Klientów (Kliknij, aby edytować)")
        panel_lista.pack(side=tk.RIGHT, padx=10, pady=10, fill='both', expand=True)

        # Treeview (NOWA KOLUMNA 'Lojalny')
        self.tree_klienci = ttk.Treeview(panel_lista, 
                                         columns=("ID_Klienta", "Imię", "Nazwisko", "Telefon", "Email", "Adres", "Lojalny"), 
                                         show='headings')
        
        self.tree_klienci.heading("ID_Klienta", text="ID", anchor=tk.W)
        self.tree_klienci.heading("Imię", text="Imię", anchor=tk.W)
        self.tree_klienci.heading("Nazwisko", text="Nazwisko", anchor=tk.W)
        self.tree_klienci.heading("Telefon", text="Telefon", anchor=tk.W)
        self.tree_klienci.heading("Email", text="Email", anchor=tk.W)
        self.tree_klienci.heading("Adres", text="Adres", anchor=tk.W)
        self.tree_klienci.heading("Lojalny", text="Stały Klient", anchor=tk.W) # NOWY NAGŁÓWEK
        
        self.tree_klienci.column("ID_Klienta", width=40, stretch=tk.NO)
        self.tree_klienci.column("Imię", width=90)
        self.tree_klienci.column("Nazwisko", width=110)
        self.tree_klienci.column("Telefon", width=100)
        self.tree_klienci.column("Email", width=150)
        self.tree_klienci.column("Adres", width=200)
        self.tree_klienci.column("Lojalny", width=80, stretch=tk.NO) # NOWA KOLUMNA
        
        self.tree_klienci.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.tree_klienci.bind('<<TreeviewSelect>>', self._akcja_wybrano_klienta)
        
    def _zaladuj_liste_klientow(self, filtr_nazwisko=""):
        """Ładuje listę klientów do Treeview, opcjonalnie filtrując po nazwisku."""
        
        for i in self.tree_klienci.get_children():
            self.tree_klienci.delete(i)
            
        cursor = self.conn.cursor()
        
        # Zmienione zapytanie SQL - SELECT wszystkich pól, w tym Lojalny
        sql = "SELECT ID_Klienta, Imię, Nazwisko, Telefon, Email, Adres, Lojalny FROM KLIENT"
        params = []
        
        if filtr_nazwisko:
            sql += " WHERE Nazwisko LIKE ?"
            params.append(f"%{filtr_nazwisko}%")
        
        sql += " ORDER BY Nazwisko ASC"
        
        try:
            cursor.execute(sql, tuple(params))
            klienci = cursor.fetchall()

            for k in klienci:
                # Konwersja 0/1 na "Nie"/"Tak" do wyświetlenia
                status_lojalny = "Tak" if k['Lojalny'] == 1 else "Nie"
                
                # Zmienione wstawianie - dodanie nowej kolumny
                self.tree_klienci.insert("", tk.END, values=(
                    k['ID_Klienta'],
                    k['Imię'],
                    k['Nazwisko'],
                    k['Telefon'],
                    k['Email'],
                    k['Adres'],
                    status_lojalny 
                ))

        except Exception as e:
            messagebox.showerror("Błąd Bazy", f"Nie udało się załadować klientów: {e}")
            
    def _akcja_wybrano_klienta(self, event):
        """Ładuje dane wybranego klienta do pól edycji."""
        try:
            selected_item = self.tree_klienci.selection()[0]
            values = self.tree_klienci.item(selected_item, 'values')
            
            self.edytowany_klient_id = int(values[0]) 
            
            # Wyczyść pola
            self.entry_imie_nowy.delete(0, tk.END)
            self.entry_nazwisko_nowy.delete(0, tk.END)
            self.entry_telefon_nowy.delete(0, tk.END)
            self.entry_email_nowy.delete(0, tk.END)
            self.entry_adres_nowy.delete(0, tk.END)
            
            # Wypełnij pola
            self.entry_imie_nowy.insert(0, values[1])
            self.entry_nazwisko_nowy.insert(0, values[2])
            self.entry_telefon_nowy.insert(0, values[3])
            self.entry_email_nowy.insert(0, values[4])
            self.entry_adres_nowy.insert(0, values[5])
            
            # NOWE: Ustawienie stanu Checkbutton na podstawie wartości z listy (6 pozycja)
            status_str = values[6]
            status_int = 1 if status_str == "Tak" else 0
            self.var_lojalny_nowy.set(status_int)

            self.btn_edytuj.config(state=tk.NORMAL)
            
        except IndexError:
            # Nic nie wybrano
            self.edytowany_klient_id = None
            self.btn_edytuj.config(state=tk.DISABLED)
            # Wyczyść również checkbox
            self.var_lojalny_nowy.set(0)
            
    def _akcja_edytuj_klienta(self):
        """Aktualizuje dane klienta w tabeli KLIENT (WF.07)."""
        
        if self.edytowany_klient_id is None:
            messagebox.showerror("Błąd", "Nie wybrano klienta do edycji.")
            return

        imie = self.entry_imie_nowy.get().strip()
        nazwisko = self.entry_nazwisko_nowy.get().strip()
        telefon = self.entry_telefon_nowy.get().strip()
        email = self.entry_email_nowy.get().strip()
        adres = self.entry_adres_nowy.get().strip()
        lojalny = self.var_lojalny_nowy.get() 
        
        if not nazwisko or not imie:
            messagebox.showerror("Błąd", "Imię i nazwisko nie mogą być puste.")
            return

        cursor = self.conn.cursor()
        
        try:
            # Zmienione zapytanie SQL - dodanie Lojalny
            sql = """
            UPDATE KLIENT 
            SET Imię=?, Nazwisko=?, Telefon=?, Email=?, Adres=?, Lojalny=?
            WHERE ID_Klienta=?
            """
            cursor.execute(sql, (imie, nazwisko, telefon, email, adres, lojalny, self.edytowany_klient_id))
            self.conn.commit()
            
            messagebox.showinfo("Sukces Edycji", f"Dane klienta ID {self.edytowany_klient_id} ({nazwisko}) zostały zaktualizowane.")
            
            # Po edycji zresetuj stan i odśwież listę
            self.edytowany_klient_id = None
            self.btn_edytuj.config(state=tk.DISABLED)
            
            self.entry_imie_nowy.delete(0, tk.END)
            self.entry_nazwisko_nowy.delete(0, tk.END)
            self.entry_telefon_nowy.delete(0, tk.END)
            self.entry_email_nowy.delete(0, tk.END)
            self.entry_adres_nowy.delete(0, tk.END)
            self.var_lojalny_nowy.set(0) # NOWE: Wyczyść stan checkboxa
            
            self._zaladuj_liste_klientow() 

        except Exception as e:
            messagebox.showerror("Błąd Edycji", f"Nie udało się zaktualizować klienta: {e}") 
            
    def _akcja_szukaj_klienta(self, event=None):
        """Wywoływana przy wpisywaniu tekstu w polu wyszukiwania."""
        filtr = self.entry_szukaj_klienta.get().strip()
        self._zaladuj_liste_klientow(filtr)

    def _akcja_dodaj_klienta(self):
        """Dodaje nowego klienta do tabeli KLIENT (WF.07) z pełnymi danymi."""
        
        imie = self.entry_imie_nowy.get().strip()
        nazwisko = self.entry_nazwisko_nowy.get().strip()
        telefon = self.entry_telefon_nowy.get().strip() # NOWE
        email = self.entry_email_nowy.get().strip()     # NOWE
        adres = self.entry_adres_nowy.get().strip()     # NOWE
        
        if not nazwisko or not imie:
            messagebox.showerror("Błąd", "Wymagane jest podanie imienia i nazwiska.")
            return

        cursor = self.conn.cursor()
        
        try:

            sql = "INSERT INTO KLIENT (Imię, Nazwisko, Telefon, Email, Adres) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(sql, (imie, nazwisko, telefon, email, adres))
            self.conn.commit()
            
            messagebox.showinfo("Sukces", f"Klient '{imie} {nazwisko}' został dodany. ID: {cursor.lastrowid}")
            
            # Wyczyść wszystkie pola
            self.entry_imie_nowy.delete(0, tk.END)
            self.entry_nazwisko_nowy.delete(0, tk.END)
            self.entry_telefon_nowy.delete(0, tk.END)
            self.entry_email_nowy.delete(0, tk.END)
            self.entry_adres_nowy.delete(0, tk.END)
            
            self._zaladuj_liste_klientow() # Odświeżenie listy

        except Exception as e:
            messagebox.showerror("Błąd Zapisu", f"Nie udało się dodać klienta: {e}")
    
    
        
    # --- WIDOK 2: POTWIERDZENIE PŁATNOŚCI (NOWY WF.06) ------------------------------------------------------------------------------------------------
    def _akcja_anuluj_przeterminowane(self):
        """
        Sprawdza i anuluje rezerwacje ze statusem 'Wstępna', dla których 
        dzisiejsza data jest późniejsza niż Termin_Ważności_Zaliczki.
        """
        if not self.conn:
            messagebox.showerror("Błąd", "Brak połączenia z bazą danych.")
            return

        dzisiaj = datetime.now().strftime(DATE_FORMAT)
        cursor = self.conn.cursor()

        sql_anuluj = """
        UPDATE REZERWACJA
        SET Status = 'Anulowana'
        WHERE Status = 'Wstępna'
        AND Termin_Ważności_Zaliczki < ?;
        """
        
        try:
            cursor.execute(sql_anuluj, (dzisiaj,))
            self.conn.commit()
            
            anulowane_count = cursor.rowcount
            
            if anulowane_count > 0:
                messagebox.showinfo("Anulowanie Sukces", 
                                    f"Pomyślnie anulowano {anulowane_count} przeterminowanych rezerwacji wstępnych.")
            else:
                messagebox.showinfo("Anulowanie", "Nie znaleziono przeterminowanych rezerwacji wstępnych do anulowania.")
                
            self._zaladuj_rezerwacje_do_potwierdzenia() # Odświeżenie listy
            
        except Exception as e:
            messagebox.showerror("Błąd Anulowania", f"Wystąpił błąd podczas anulowania rezerwacji: {e}")
            
    def _utworz_widok_platnosci(self, master_frame):
        """Inicjalizuje interfejs do potwierdzania wpłaty zaliczki."""
        
        tk.Label(master_frame, text="Rezerwacje Wstępne Oczekujące na Płatność (WF.06)", font=('Arial', 14, 'bold')).pack(pady=10)

        # Treeview dla rezerwacji wstępnych
        self.tree_platnosci = ttk.Treeview(master_frame, columns=("ID_Rezerwacji", "Pokój", "Klient", "Okres", "Kwota", "Termin"), show='headings')
        
        self.tree_platnosci.heading("ID_Rezerwacji", text="ID Rezerwacji", anchor=tk.W)
        self.tree_platnosci.heading("Pokój", text="Pokój", anchor=tk.W)
        self.tree_platnosci.heading("Klient", text="Klient", anchor=tk.W)
        self.tree_platnosci.heading("Okres", text="Okres Pobytu", anchor=tk.W)
        self.tree_platnosci.heading("Kwota", text="Cena Gwarantowana (PLN)", anchor=tk.W)
        self.tree_platnosci.heading("Termin", text="Termin Zaliczki", anchor=tk.W)
        
        self.tree_platnosci.column("ID_Rezerwacji", width=100, stretch=tk.NO)
        self.tree_platnosci.column("Pokój", width=80, stretch=tk.NO)
        self.tree_platnosci.column("Termin", width=120, stretch=tk.NO)
        
        self.tree_platnosci.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Ramka na przyciski na dole
        frame_przyciski = ttk.Frame(master_frame)
        frame_przyciski.pack(fill='x', pady=10, padx=10)
        

        frame_przyciski.columnconfigure(0, weight=1)
        frame_przyciski.columnconfigure(1, weight=1)
        frame_przyciski.columnconfigure(2, weight=1)

        # 1. Przycisk Potwierdzenia (Lewy)
        self.btn_potwierdz = ttk.Button(frame_przyciski, text="Potwierdź Wpłatę Zaliczki", 
                                        command=self._akcja_potwierdz_platnosc)
        self.btn_potwierdz.grid(row=0, column=0, padx=5, sticky='w')

        # 2. NOWY PRZYCISK: Anulowanie Wybranej Rezerwacji (Środek)
        self.btn_anuluj_wybrana = ttk.Button(frame_przyciski, 
                                            text="Anuluj Wybraną Rezerwację (Ręcznie)", 
                                            command=self._akcja_anuluj_wybrana_rezerwacje)
        self.btn_anuluj_wybrana.grid(row=0, column=1, padx=5, sticky='ew') # sticky='ew' - rozciągnięcie w poziomie

        # 3. Przycisk Anulowania Przeterminowanych (Prawy)
        self.btn_anuluj_przeterminowane = ttk.Button(frame_przyciski, 
                                                    text="Anuluj Przeterminowane Rezerwacje", 
                                                    command=self._akcja_anuluj_przeterminowane)
        self.btn_anuluj_przeterminowane.grid(row=0, column=2, padx=5, sticky='e')
       

    def _akcja_anuluj_wybrana_rezerwacje(self):
        """
        Anuluje ręcznie rezerwację wybraną w Treeview, zmieniając jej status
        na 'Anulowana', niezależnie od terminu ważności zaliczki.
        """
        if not self.conn:
            messagebox.showerror("Błąd", "Brak połączenia z bazą danych.")
            return

        try:
            # 1. Pobranie ID wybranej rezerwacji
            selected_item = self.tree_platnosci.selection()[0]
            values = self.tree_platnosci.item(selected_item, 'values')
            rezerwacja_id = values[0]
            klient_nazwisko = values[2] # Dla lepszej informacji zwrotnej

            # 2. Potwierdzenie anulowania
            potwierdzenie = messagebox.askyesno(
                "Potwierdź Anulowanie",
                f"Czy na pewno chcesz ręcznie anulować rezerwację ID {rezerwacja_id} dla klienta {klient_nazwisko}?"
            )

            if not potwierdzenie:
                return # Użytkownik zrezygnował

            # 3. Aktualizacja statusu w bazie danych
            cursor = self.conn.cursor()
            sql_update = """
            UPDATE REZERWACJA
            SET Status = 'Anulowana'
            WHERE ID_Rezerwacji = ? AND Status = 'Wstępna';
            """
            cursor.execute(sql_update, (rezerwacja_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                messagebox.showinfo("Sukces Anulowania", f"Rezerwacja ID {rezerwacja_id} została pomyślnie ANULOWANA ręcznie.")
                self._zaladuj_rezerwacje_do_potwierdzenia() # Odświeżenie listy
            else:
                messagebox.showerror("Błąd Anulowania", "Nie udało się anulować rezerwacji (może już nie mieć statusu 'Wstępna').")

        except IndexError:
            messagebox.showerror("Błąd", "Wybierz rezerwację z listy, którą chcesz anulować.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas ręcznego anulowania rezerwacji: {e}")
    def _zaladuj_rezerwacje_do_potwierdzenia(self):
        """Ładuje rezerwacje ze statusem 'Wstępna' do Treeview."""
        
        for i in self.tree_platnosci.get_children():
            self.tree_platnosci.delete(i)
            
        cursor = self.conn.cursor()
        
        sql = """
        SELECT R.ID_Rezerwacji, P.Numer_Pokoju, K.Nazwisko, R.Data_Początkowa, R.Data_Końcowa, R.Cena_Gwarantowana, R.Termin_Ważności_Zaliczki
        FROM REZERWACJA R
        JOIN POKOJ P ON R.ID_Pokoju = P.ID_Pokoju
        JOIN KLIENT K ON R.ID_Klienta = K.ID_Klienta
        WHERE R.Status = 'Wstępna'
        ORDER BY R.Termin_Ważności_Zaliczki ASC;
        """
        
        try:
            cursor.execute(sql)
            rezerwacje = cursor.fetchall()

            for r in rezerwacje:
                okres = f"{r['Data_Początkowa']} do {r['Data_Końcowa']}"
                self.tree_platnosci.insert("", tk.END, values=(
                    r['ID_Rezerwacji'],
                    r['Numer_Pokoju'],
                    r['Nazwisko'],
                    okres,
                    f"{r['Cena_Gwarantowana']:.2f}",
                    r['Termin_Ważności_Zaliczki']
                ))

        except Exception as e:
            messagebox.showerror("Błąd Bazy", f"Nie udało się załadować rezerwacji: {e}")

    def _akcja_potwierdz_platnosc(self):
        """
        Aktualizuje status rezerwacji z 'Wstępna' na 'Obowiązująca' 
        po potwierdzeniu wpłaty zaliczki (WF.06).
        """
        try:
            selected_item = self.tree_platnosci.selection()[0]
            values = self.tree_platnosci.item(selected_item, 'values')
            rezerwacja_id = values[0]
            
            cursor = self.conn.cursor()
            
            sql_update = """
            UPDATE REZERWACJA
            SET Status = 'Obowiązująca'
            WHERE ID_Rezerwacji = ? AND Status = 'Wstępna';
            """
            cursor.execute(sql_update, (rezerwacja_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                messagebox.showinfo("Sukces", f"Rezerwacja ID {rezerwacja_id} została zmieniona na status 'Obowiązująca'.")
                self._zaladuj_rezerwacje_do_potwierdzenia() # Odświeżenie listy
            else:
                messagebox.showerror("Błąd", "Nie udało się zaktualizować statusu rezerwacji (może już nie być 'Wstępna').")
            
        except IndexError:
            messagebox.showerror("Błąd", "Wybierz rezerwację z listy, którą chcesz potwierdzić.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas potwierdzania płatności: {e}")


    

    def __del__(self):

        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = SystemRezerwacjiPensjonatu(root)
    root.mainloop()