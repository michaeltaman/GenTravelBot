import sqlite3
import os

def setup_database():
    # Проверяем, существует ли база данных
    if os.path.exists("database.db"):
        print("База данных уже существует. Пропускаем создание.")
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Создание таблиц
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY,
            destination TEXT,
            price REAL,
            quality TEXT,
            start_date TEXT,
            end_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            tour_id INTEGER,
            customer_name TEXT,
            status TEXT,
            FOREIGN KEY (tour_id) REFERENCES tours (id)
        )
    ''')

    # Добавление начальных данных
    tours_data = [
        ("Switzerland", 1000, "high", "2024-12-15", "2024-12-20"),
        ("France", 800, "medium", "2024-12-10", "2024-12-15"),
        ("Italy", 600, "low", "2024-12-05", "2024-12-10")
    ]
    cursor.executemany(
        "INSERT INTO tours (destination, price, quality, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
        tours_data
    )

    conn.commit()
    conn.close()
    print("База данных создана и инициализирована.")

if __name__ == "__main__":
    setup_database()
