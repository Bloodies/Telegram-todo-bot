from requests import session
from sqlalchemy import text
from sqlalchemy.ext.asyncio.session import AsyncSession

from create_connection import create_connection

# cursor.execute("""CREATE TABLE IF NOT EXISTS
#         tasks (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             task TEXT,
#             creator_id INTEGER NOT NULL,
#             user_id INTEGER NOT NULL,
#             deadline TEXT,
#             status INTEGER NOT NULL,
#             FOREIGN KEY (creator_id) REFERENCES users (id),
#             FOREIGN KEY (user_id) REFERENCES users (id)
#         )""")


async def show_database_tasks():
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    result = cursor.execute(f"""SELECT * FROM tasks""")
    connection.commit()
    return result.fetchall()


async def add_task(task, creator_id, user_id, deadline, status):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    cursor.execute(f"""INSERT INTO tasks (task, creator_id, user_id, deadline, status)
                    VALUES ('{task}', {creator_id}, {user_id}, '{deadline}', {status});""")
    connection.commit()
    return True


async def delete_task(task_id):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    cursor.execute(f"""DELETE FROM tasks WHERE id = {task_id}""")
    connection.commit()
    return True


async def change_task(task, task_id):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    cursor.execute(f"""UPDATE tasks SET task = '{task}' WHERE id = {task_id}""")
    connection.commit()
    return True


async def change_deadline_task(deadline, task_id):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    cursor.execute(f"""UPDATE tasks SET deadline = '{deadline}' WHERE id = {task_id}""")
    connection.commit()
    return True


async def change_status_task(status, task_id):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    cursor.execute(f"""UPDATE tasks SET status = {status} WHERE id = {task_id}""")
    connection.commit()
    return True


async def show_tasks(user_id: int):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    result = cursor.execute(f"""SELECT * FROM tasks WHERE  user_id = {user_id}""")
    print(result)
    connection.commit()
    return result.fetchall()


async def show_current_task(task, creator_id, user_id, deadline, status):
    connection = create_connection('database.sqlite')
    cursor = connection.cursor()
    result = cursor.execute(f"""SELECT id FROM tasks WHERE task = '{task}'
                            AND creator_id = {creator_id}
                            AND user_id = {user_id}
                            AND deadline = '{deadline}'
                            AND status = {status}""")
    connection.commit()
    return result.fetchall()
