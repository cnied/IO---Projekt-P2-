import sqlite3
from sqlite3 import Error

def utworz_polaczenie(db_file):
    """Tworzy połączenie z bazą danych SQLite podanej w db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Pomyślnie połączono z bazą danych: {db_file} (SQLite v{sqlite3.sqlite_version})")
    except Error as e:
        print(f"Wystąpił błąd podczas łączenia z bazą danych: {e}")
    return conn

def utworz_tabele(conn, create_table_sql):
    """Wykonuje skrypt tworzący wszystkie tabele."""
    try:
        cursor = conn.cursor()
        cursor.executescript(create_table_sql)
        conn.commit()
        print("Tabele zostały pomyślnie utworzone.")
    except Error as e:
        print(f"Wystąpił błąd podczas tworzenia tabel: {e}")

# --- Skrypt SQL z definicjami tabel ---
sql_create_tables = """
-- Encja: POKÓJ
CREATE TABLE POKOJ (
    ID_Pokoju INTEGER PRIMARY KEY AUTOINCREMENT,
    Numer_Pokoju TEXT NOT NULL UNIQUE,
    Piętro INTEGER NOT NULL,
    Widok_Na_Morze BOOLEAN NOT NULL DEFAULT 0,
    Liczba_Miejsc_Noclegowych INTEGER NOT NULL,
    Status_Dostępności_Okresowej TEXT NOT NULL DEFAULT 'Dostępny',
    Cena_Bazowa_Mnożnik REAL NOT NULL DEFAULT 1.0
);

-- Encja: KLIENT
CREATE TABLE KLIENT (
    ID_Klienta INTEGER PRIMARY KEY AUTOINCREMENT,
    Imię TEXT NOT NULL,
    Nazwisko TEXT NOT NULL,
    Telefon TEXT,
    Email TEXT UNIQUE,
    Adres TEXT
);

-- Encja: CENNIK
CREATE TABLE CENNIK (
    ID_Cennika INTEGER PRIMARY KEY AUTOINCREMENT,
    Nazwa_Okresu TEXT NOT NULL,
    Data_Początkowa_Okresu DATE NOT NULL,
    Data_Końcowa_Okresu DATE NOT NULL,
    Mnożnik_Cenowy REAL NOT NULL DEFAULT 1.0
);

-- Encja: REZERWACJA
CREATE TABLE REZERWACJA (
    ID_Rezerwacji INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Pokoju INTEGER NOT NULL,
    ID_Klienta INTEGER NOT NULL,
    Data_Rezerwacji DATE NOT NULL,
    Data_Początkowa DATE NOT NULL,
    Data_Końcowa DATE NOT NULL,
    Liczba_Osób INTEGER NOT NULL,
    Cena_Gwarantowana REAL NOT NULL,
    Status TEXT NOT NULL,
    Termin_Ważności_Zaliczki DATE,

    FOREIGN KEY (ID_Pokoju) REFERENCES POKOJ(ID_Pokoju),
    FOREIGN KEY (ID_Klienta) REFERENCES KLIENT(ID_Klienta) ON DELETE CASCADE
);

-- Encja: PŁATNOŚĆ
CREATE TABLE PŁATNOŚĆ (
    ID_Płatności INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Rezerwacji INTEGER,
    Kwota REAL NOT NULL,
    Typ TEXT NOT NULL,
    Data_Wpływu DATE NOT NULL,

    FOREIGN KEY (ID_Rezerwacji) REFERENCES REZERWACJA(ID_Rezerwacji) ON DELETE SET NULL
);

-- Encja: POBYT
CREATE TABLE POBYT (
    ID_Pobytu INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Pokoju INTEGER NOT NULL,
    ID_Klienta INTEGER NOT NULL,
    ID_Rezerwacji INTEGER UNIQUE,
    Data_Przyjazdu_Faktyczna DATE NOT NULL,
    Data_Wyjazdu_Faktyczna DATE NOT NULL,
    Opłata_Całkowita_Pobrana REAL,
    Zrodlo_Rezerwacji TEXT NOT NULL,

    FOREIGN KEY (ID_Pokoju) REFERENCES POKOJ(ID_Pokoju),
    FOREIGN KEY (ID_Klienta) REFERENCES KLIENT(ID_Klienta) ON DELETE CASCADE,
    FOREIGN KEY (ID_Rezerwacji) REFERENCES REZERWACJA(ID_Rezerwacji) ON DELETE SET NULL
);
"""


database_file = "data.db"  # Nazwa pliku bazy danych

# 1. Tworzenie połączenia (jeśli plik .db nie istnieje, zostanie utworzony)
conn = utworz_polaczenie(database_file)

if conn is not None:
    # 2. Tworzenie tabel
    utworz_tabele(conn, sql_create_tables)
    # 3. Zamknięcie połączenia
    conn.close()