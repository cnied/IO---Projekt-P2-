import sqlite3
from sqlite3 import Error

DATABASE_FILE = "data.db"

def utworz_polaczenie(db_file=DATABASE_FILE):
    """Tworzy połączenie z bazą danych lub ją otwiera."""
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwach

        print("dzialam")
        return conn
    except sqlite3.Error as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return None

def wypelnij_dane_poczatkowe(conn):
    """Wypełnia bazę 18 pokojami, jeśli są puste (WF.01)."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM POKOJ")
    if cursor.fetchone()[0] == 0:
        pokoje_dane = []
        for i in range(1, 19):
            nr = i
            miejsca = 2 if i % 3 != 0 else 4
            widok = 1 if i % 4 == 0 else 0
            pietro = (i - 1) // 6 + 1
            mnoznik = 1.0 + (0.2 if widok else 0.0) + (0.1 * (pietro - 1))

            pokoje_dane.append((nr, pietro, widok, miejsca, 'Dostępny', mnoznik))

        sql = "INSERT INTO POKOJ (Numer_Pokoju, Piętro, Widok_Na_Morze, Liczba_Miejsc_Noclegowych, Status_Dostępności_Okresowej, Cena_Bazowa_Mnożnik) VALUES (?, ?, ?, ?, ?, ?)"
        cursor.executemany(sql, pokoje_dane)
        conn.commit()
        print("Wypełniono bazę 18 pokojami.")
 
def uzupelnij_cennik(conn):
    """
    Dodaje przykładowe okresy sezonowe do tabeli CENNIK (WF.03).
    """
    if not conn:
        print("Błąd: Brak aktywnego połączenia z bazą danych.")
        return

    cursor = conn.cursor()
    
    try:
        # Sprawdza, czy tabela nie jest już wypełniona
        cursor.execute("SELECT COUNT(*) FROM CENNIK")
        if cursor.fetchone()[0] > 0:
            print("Tabela CENNIK już zawiera dane. Pomijam wstawianie.")
            return
            
        cennik_dane = [
            ('Sezon Wysoki - Lato', '2026-06-01', '2026-08-31', 1.5),
            ('Sezon Średni - Wiosna', '2026-05-01', '2026-05-31', 1.2),
            ('Sezon Średni - Jesień', '2026-09-01', '2026-09-30', 1.2),
            ('Poza Sezonem - Zima', '2026-01-01', '2026-04-30', 1.0),
            ('Poza Sezonem - Późna Jesień/Zima', '2026-10-01', '2026-12-31', 1.0),
        ]

        sql = """
        INSERT INTO CENNIK (Nazwa_Okresu, Data_Początkowa_Okresu, Data_Końcowa_Okresu, Mnożnik_Cenowy) 
        VALUES (?, ?, ?, ?)
        """
        
        # Użycie executemany do wstawiania wielu wierszy
        cursor.executemany(sql, cennik_dane)
        conn.commit()
        print("Wypełniono tabelę CENNIK danymi sezonowymi.")
        
    except sqlite3.OperationalError as e:
        # Ten błąd wystąpi, jeśli tabela CENNIK nie istnieje
        print(f"Błąd operacyjny SQLite (prawdopodobnie brak tabeli CENNIK): {e}")
        print("Upewnij się, że tabela CENNIK została utworzona w funkcji utworz_strukture_bazy.")
    except Exception as e:
        print(f"Nieznany błąd podczas wypełniania tabeli CENNIK: {e}")
        
        
# Sekcja do uruchomienia tylko raz w celu inicjalizacji bazy
conn = utworz_polaczenie()
if conn:
    wypelnij_dane_poczatkowe(conn)
    uzupelnij_cennik(conn)
    conn.close()