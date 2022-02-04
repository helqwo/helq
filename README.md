# Dokumentacja

## Klasy
1. `BaseModel`
2. `User` 
3. `Tag` 
4. `TaskList` 
5. `Task` 
6. `Plan`
7. `TagTask` 
8. `TaskPlan`

## Architektura systemu
System ma na celu zarządzanie listami zadań użytkownika, pozwalając na organizację ich przy pomocy tagów (kategorii) oraz list zadań, a także na planowanie wykonania zadań na określone terminy.

W celu ułatwienia rozpoczęcia korzystania z systemu, interakcja z nim odbywa się poprzez chat na platformie Telegram. Do komunikacji z Telegramem użyto biblioteki [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI).

Dane zapisywane są w bazie danych używając biblioteki [peewee](http://docs.peewee-orm.com/en/latest/). Podstawowe obiekty - `Tag`, `Plan`, `Task` oraz `TaskList` są reprezentowane przez klasy dziedziczące z `peewee.Model`, co pozwala na przechowywanie ich w bazie danych. Ponadto relacje należenia między wyżej wymienionymi obiektami reprezentowane są przy pomocy tabel pomocniczych zaimplementowanych przy użyciu klas `TagTask` oraz `TaskPlan`.

Bot Telegramowy pozwala użytkownikowi prostymi komendami dodawać nowe zadania, przypisywać do nich tagi (kategorie), umieszczać je na liście zadań, określać planowane daty ich wykonania oraz przeszukiwać już utworzone zadania wg. list, dat oraz tagów.

## Opis klas
1. `BaseModel` - klasa bazowa z której dziedziczą modele obiektów przystosowane do zapisania w bazie danych
2. `User` - reprezentuje pojedynczego użytkownika aplikacji Telegram
    - atrybuty
        - telegram_id -- ID użytkownika Telegrama
3. `Tag` - reprezentuje tag którym można oznaczyć istniejące zadania
    - atrybuty
        - name -- nazwa tagu
        - user -- użytkownik, do którego tag należy
4. `TaskList` - reprezentuje listę zadań, zadanie może należeć do maksymalnie jednej listy zadań
    - atrybuty
        - name -- nazwa listy zadań
        - user -- użytkownik, do którego lista należy
    - metody 
        - add_task(task) -- przypisuje podane zadanie do listy

5. `Task` - reprezentuje pojedyncze zadanie do wykonania
    - atrybuty
        - name -- treść zadania
        - estimated_time -- szacowany czas potrzebny na wykonanie zadania w sekundach
        - tasklist -- lista zadań do której zadanie należy (jeżeli do jakiejś należy)
        - user -- użytkownik, do którego lista należy
    - metody
        - set_est_time(minutes) -- ustawia szacowany czas wykonania zadania (w minutach)
        - add_tag(tag) -- dodaje tag do zadania
        - remove_tag(tag) -- usuwa tag z zadania
6. `Plan` - przechowuje listę zadań zaplanowanych na dany termin
    - atrybuty
        - date -- termin wykonywania zadań
        - user -- właściciel planu
    - metody
        - add_task(task) -- dodaje zadanie do planu
        - remove_task(task) -- usuwa zadanie z planu
7. `TagTask` - reprezentuje powiązanie pomiędzy klasami `Tag` i `Task`
    - atrybuty
        - tag
        - task
8. `TaskPlan` - reprezentuje powiązanie pomiędzy klasami `Task` i `Plan`
    - atrybuty
        - plan
        - task