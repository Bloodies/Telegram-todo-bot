from create_connection import create_connection

# connection = create_connection('database.sqlite')
# cursor = connection.cursor()
# cursor.execute("""CREATE TABLE IF NOT EXISTS
#         users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             surname TEXT,
#             telegram_id INTEGER NOT NULL,
#             admin INTEGER NOT NULL
#         )""")
# connection.commit()


async def show_database_users():
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    result = cursor.execute(f"""SELECT * FROM users""")
    connection.commit()
    return result.fetchall()


async def check_user(telegram_id):
    try:
        connection = create_connection('database.sqlite')
        cursor = connection.cursor()
        result = cursor.execute(f"""SELECT * FROM users WHERE telegram_id = {telegram_id}""")
        connection.commit()
        print(f'\033[32m User {telegram_id} found \033[0m')
        return result.fetchall()
    except Exception as e:
        print(f'\033[31m Error\033[0m occurred in \033[33mcheck_user\033[0m: \033[3m\033[31m {e} \033[0m')
        return []


async def find_user_byid(user_id):
    try:
        connection = create_connection('database.sqlite')
        cursor = connection.cursor()
        result = cursor.execute(f"""SELECT * FROM users WHERE id = {user_id}""")
        connection.commit()
        print(f'\033[32m User id {user_id} found \033[0m')
        return result.fetchall()
    except Exception as e:
        print(f'\033[31m Error\033[0m occurred in \033[33mfind_user_byid\033[0m: \033[3m\033[31m {e} \033[0m')
        return []


async def add_user(name, surname, telegram_id, admin):
    try:
        connection = create_connection('database.sqlite')
        cursor = connection.cursor()
        cursor.execute(f"""INSERT INTO users (name, surname, telegram_id, admin) 
                            VALUES ('{name}','{surname}', {telegram_id}, {admin});""")
        connection.commit()
        print(f'\033[32m New user {telegram_id} added \033[0m')
    except Exception as e:
        print(f'\033[31m Error\033[0m occurred in \033[33madd_user\033[0m: \033[3m\033[31m {e} \033[0m')
        pass


async def change_user_info(name, surname, telegram_id):
    try:
        connection = create_connection('database.sqlite')
        cursor = connection.cursor()
        cursor.execute(f"""UPDATE users SET 
                            name = '{name}',
                            surname = '{surname}'
                        WHERE telegram_id = {telegram_id}""")
        connection.commit()
        print(f'\033[32m User {telegram_id} info changed \033[0m')
    except Exception as e:
        print(f'\033[31m Error\033[0m occurred in \033[33mchange_user_info\033[0m: \033[3m\033[31m {e} \033[0m')
        pass


async def set_user_admin(user_id, admin):
    try:
        connection = create_connection('database.sqlite')
        cursor = connection.cursor()
        cursor.execute(f"""UPDATE users SET 
                            admin = {admin}
                        WHERE id = {user_id}""")
        connection.commit()
        print(f'\033[32m User {user_id} setting admin changed \033[0m')
    except Exception as e:
        print(f'\033[31m Error\033[0m occurred in \033[33mset_user_admin\033[0m: \033[3m\033[31m {e} \033[0m')
        pass


async def delete_user(telegram_id):
    try:
        connection = create_connection('database.sqlite')
        cursor = connection.cursor()
        cursor.execute(f"""DELETE FROM users WHERE telegram_id = {telegram_id}""")
        connection.commit()
        print(f'\033[32m User {telegram_id} deleted \033[0m')
    except Exception as e:
        print(f'\033[31m Error\033[0m occurred in \033[33mdelete_user\033[0m: \033[3m\033[31m {e} \033[0m')
        pass


async def exist_user(telegram_id):
    info = await check_user(telegram_id)
    if len(info) == 0:
        return []
    else:
        return info
