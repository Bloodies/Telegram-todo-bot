from create_connection import create_connection

connection = create_connection('database.sqlite')
cursor = connection.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS 
        users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT,
            telegram_id INTEGER NOT NULL,
            admin INTEGER NOT NULL
        )""")
cursor.execute("""CREATE TABLE IF NOT EXISTS 
        tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT,
            creator_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            deadline TEXT,
            status INTEGER NOT NULL,
            FOREIGN KEY (creator_id) REFERENCES users (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )""")

cursor.execute("""INSERT INTO users (name, surname, telegram_id, admin) VALUES ('Елизар', 'Чепоков', 649113905, 1)""")
cursor.execute("""INSERT INTO users (name, surname, telegram_id, admin) VALUES ('Владимир', 'Целиков', 1134652963, 0)""")

cursor.execute("INSERT INTO tasks (task, creator_id, user_id, deadline, status) "
               "VALUES ('Закончить бота', 1, 1, '2022-06-30 12:00:00', 0)")
cursor.execute("INSERT INTO tasks (task, creator_id, user_id, deadline, status) "
               "VALUES ('Собес', 1, 1, '2022-06-30 14:00:00', 0)")
cursor.execute("INSERT INTO tasks (task, creator_id, user_id, deadline, status) "
               "VALUES ('Сходить ****', 1, 2, '2022-06-30 01:00:00', 0)")

connection.commit()
connection.close()

if __name__ == '__main__':
    print(f'Starting input data to db')
