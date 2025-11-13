## Tytuł i Cel:
- Tytuł: Wdrożenie Systemu Rezerwacji Pokoi Pensjonatu (**SRPP**)
- Cel Projektu: Stworzenie jednostanowiskowego systemu informatycznego wspierającego proces rezerwacji telefonicznej i e-mail’em oraz bezpośredni wynajem.
- Główna Metryka Sukcesu: Zwiększenie efektywności i ergonomii obsługi klienta (krótkie rozmowy, szybkie wyszukiwanie).
- Architektura: System na pojedynczym komputerze, obsługa jednego operatora jednocześnie.
## Obecna Skala:
- Ustalenia: Pensjonat liczy obecnie 18 pokoi.
- Wymaganie: System musi być parametryzowalny (umożliwiać łatwą zmianę liczby pokoi i ich dostępności, np. z powodu remontu).
### Rezerwacja:
- Ustalenia: Obsługa telefoniczna i e-mailowa. Wymaga rejestracji statusów: Wstępna (oczekiwanie na zaliczkę) i Obowiązująca (po wpływie zaliczki).
- Wymaganie: Konieczność obsługi cyklu statusów rezerwacji i automatyczne anulowanie rezerwacji wstępnej po przekroczeniu terminu wpłaty zaliczki.
### Wynajem:
- Ustalenia: Możliwy wynajem zarówno z wcześniejszej rezerwacji, jak i *z ulicy*.
- Wymaganie: System musi wspierać pełny cykl życia pokoju: od rezerwacji przez pobyt do zwolnienia.
### Architektura i Użytkownicy
- Ustalenia: System na pojedynczym komputerze, obsługa jednego operatora w danym momencie.
- Wymaganie: Konieczność spełnienia kryterium Wydajności i Ergonomii na jednostanowiskowym środowisku.
## Kluczowe Procesy i Funkcjonalności
System musi wspierać trzy główne procesy:
### Rejestracja i Zarządzanie Klientem (Baza Wiedzy)
-	Rejestracja danych klientów.
-	Identyfikacja Stałych Klientów (osoba, która co najmniej raz wynajmowała pokój).
-	Przechowywanie historii pobytów.
### Obsługa Popytu i Cenotwórstwo
-	Wyszukiwanie wolnych pokoi na podstawie dat i parametrów (liczba osób, widok na morze, piętro).
-	Automatyczne obliczanie ceny (zależne od sezonu i parametrów pokoju).
-	Wsparcie negocjacji (możliwość gwarancji ustalonej ceny).
### Zarządzanie Rezerwacją i Pobytem
-	Statusy rezerwacji: Wstępna (oczekiwanie na zaliczkę), Obowiązująca, Anulowana.
-	Obsługa wpływu zaliczki (potwierdzenie -> zmiana statusu).
-	Obsługa przypadku no-show (pokój zwalniany po jednej dobie).
-	Rejestracja faktycznych pobytów i opłat.
## Czynniki Wpływające na Cenę (Logika Biznesowa)
Cena wynajmu jest dynamiczna i zależy od wielu parametrów. System musi precyzyjnie wspierać logikę wyceny:
#### Termin (Sezonowość):
-	Wpływ: Wyższe ceny w sezonie (ustalone z góry).
-	Implementacja: Wymagany moduł Cennika Sezonowego (definiowanie okresów i bazowych stawek).
#### Parametry Pokoju (Położenie i Rozmiar):
-	Wpływ: Cena zależna od czynników premium, takich jak widok na morze i piętro, a także od liczby miejsc noclegowych.
-	Implementacja: Precyzyjna ewidencja parametrów każdego pokoju i ich zróżnicowany wpływ na cenę bazową.
#### Liczba Osób (Obłożenie):
-	Wpływ: Możliwa zniżka, jeśli wynajmujący jest mniej, niż wynosi nominalna liczba miejsc noclegowych w pokoju.
-	Implementacja: Algorytm korekty ceny oparty na porównaniu deklarowanej liczby osób z pojemnością pokoju.
#### Status Klienta (Lojalność):
-	Wpływ: Zniżka dla stałych klientów (osób, które co najmniej raz wcześniej wynajmowały pokój).
-	Implementacja: Automatyczna weryfikacja historii pobytów klienta w systemie w celu naliczenia zniżki.
#### Negocjacje (Elastyczność):
-	Wpływ: Możliwość negocjacji ceny przez klienta.
-	Implementacja: Pole Cena Gwarantowana z możliwością ręcznej edycji przez operatora, która to cena jest następnie wiążąca dla rezerwacji.
