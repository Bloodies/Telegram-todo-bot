import sqlite3
from sqlite3 import Error


def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print(f'Connection to SQLite DB \033[32msuccessful\033[0m')
    except Error as e:
        print(f'The error \033[3m\033[31m"{e}"\033[0m occurred')

    return connection
