import aiosqlite
import aiohttp
import asyncio
import datetime
import os
import dotenv
import requests
import sqlite3
import telebot
import time
import uvicorn
from fastapi import FastAPI, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.asyncio import engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from create_connection import create_connection
from db_requests.users_requests import (check_user, add_user, change_user_info, set_user_admin,
                                        delete_user, exist_user, find_user_byid, show_database_users)
from db_requests.true_tasks_requests import (add_task, delete_task, change_task, change_deadline_task,
                                             change_status_task, show_tasks, show_current_task, show_database_tasks)

dotenv.load_dotenv()
API_TOKEN = os.getenv('TOKEN')

# WEBHOOK_HOST = f'todoler-bot.herokuapp.com'
# WEBHOOK_PORT = 8443
# WEBHOOK_LISTEN = '0.0.0.0'
#
# WEBHOOK_SSL_CERT = './webhook_cert.pem'
# WEBHOOK_SSL_PRIV = './webhook_pkey.pem'
#
# WEBHOOK_URL_BASE = f'https://{WEBHOOK_HOST}:{WEBHOOK_PORT}'
# WEBHOOK_URL_PATH = f'/{API_TOKEN}/'

bot = AsyncTeleBot(API_TOKEN)

engine = engine.create_async_engine('sqlite+aiosqlite:///database.sqlite', echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield await session


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(f'/{API_TOKEN}/')
def process_webhook(update: dict):
    if update:
        update = telebot.types.Update.de_json(update)
        bot.process_new_updates([update])
    else:
        return


admin, telegram_id, user_id, keyboard, state, msg_list = None, None, None, None, None, None
name, surname = None, None
year, month, day, h, m, status, msg = None, None, None, None, None, None, None
task_id, task_name = None, None
temp_userid = None

status_format = {0: 'план', 1: 'в работе', 2: 'выполнена'}

keyboard_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_tasks = types.KeyboardButton('Посмотреть задачи')
btn_change_info = types.KeyboardButton('Редактировать профиль')
keyboard_menu.row(btn_tasks, btn_change_info)

keyboard_admin = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_tasks = types.KeyboardButton('Посмотреть задачи')
btn_change_info = types.KeyboardButton('Редактировать профиль')
btn_administration = types.KeyboardButton('Панель администрирования')
keyboard_admin.row(btn_tasks, btn_change_info)
keyboard_admin.row(btn_administration)

tasks_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_add = types.KeyboardButton('Добавить задачу')
btn_back = types.KeyboardButton('Назад')
tasks_keyboard.row(btn_add)
tasks_keyboard.row(btn_back)

administration = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_users = types.KeyboardButton('Список пользователей')
btn_backb = types.KeyboardButton('Назад')
administration.row(btn_users)
administration.row(btn_backb)

year_markup = types.InlineKeyboardMarkup()
y2022 = types.InlineKeyboardButton('2022', callback_data='2022-0')
y2023 = types.InlineKeyboardButton('2023', callback_data='2023-0')
year_markup.row(y2022, y2023)

empty = telebot.types.ReplyKeyboardRemove()


async def task(text, chat_id, syear, smonth, sday, shour, sstatus):
    today = datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')
    deadline = datetime.strftime(f'{syear}-{smonth}-{sday} {shour}:00:00', '%Y-%m-%d %H:%M:%S')
    notify = (deadline - 3600) - today
    if sstatus in (0, 1):
        while True:
            await asyncio.sleep(notify)
            await bot.send_chat_action(chat_id, 'typing')
            await bot.send_message(chat_id, f'Дедлайн по задаче: {text} \nчерез 1 час', reply_markup=tasks_keyboard)
    else:
        pass


@bot.message_handler(commands=['help'])
async def send_welcome(message, session: AsyncSession = Depends(get_session)):
    global admin, keyboard, telegram_id, state
    await bot.send_chat_action(message.chat.id, 'typing')
    await bot.send_message(message.chat.id, f'Приветствую,\n'
                                            f'Бот написан в рамках тестового задания.\n'
                                            f'Данный бот позволяет добавлять и редактировать список задач.\n'
                                            f'Для работы с ботом напиши /start')

    user_info = await exist_user(message.from_user.id)
    if len(user_info) == 0:
        state = 'input_name'
        await bot.send_message(message.chat.id, f'Введите Имя', reply_markup=keyboard)
    else:
        telegram_id = user_info[0][3]
        if user_info[0][4] == 1:
            admin = 1
            keyboard = keyboard_admin
        else:
            keyboard = keyboard_menu


@bot.message_handler(commands=['start'])
async def start(message, session: AsyncSession = Depends(get_session)):
    global admin, keyboard, telegram_id, state
    await bot.send_chat_action(message.chat.id, 'typing')

    user_info = await exist_user(message.from_user.id)
    if len(user_info) == 0:
        state = 'input_name'
        await bot.send_message(message.chat.id, f'Введите Имя', reply_markup=empty)
    else:
        telegram_id = user_info[0][3]
        if user_info[0][4] == 1:
            admin = 1
            keyboard = keyboard_admin
        else:
            keyboard = keyboard_menu

        await bot.send_message(message.chat.id,
                               f'Приветствую {user_info[0][1]} {user_info[0][2]}',
                               reply_markup=keyboard)


@bot.message_handler(func=lambda message: True, content_types=['text'])
async def get_text_messages(message, session: AsyncSession = Depends(get_session)):
    global admin, telegram_id, user_id, keyboard, state, name, surname, task_id, task_name, msg_list, status_format, msg
    await bot.send_chat_action(message.chat.id, 'typing')
    print(await show_database_tasks())

    user_info = await exist_user(message.from_user.id)
    user_id = user_info[0][0]
    telegram_id = user_info[0][3]
    if user_info[0][4] == 1:
        admin = 1
        keyboard = keyboard_admin
    else:
        keyboard = keyboard_menu

    if message.text == 'Посмотреть задачи':
        msg = await bot.send_message(message.chat.id, f'Задачи:', reply_markup=tasks_keyboard)
        items = await show_tasks(user_info[0][0])
        # print(await show_database_users())
        # print(await show_database_tasks())
        # print(items)
        msg_list = []
        for item in items:
            creator_info = await find_user_byid(item[2])
            temp_markup = types.InlineKeyboardMarkup()
            changetask = types.InlineKeyboardButton('Изменить название',
                                                    callback_data=f'changetask-{item[0]}-{msg.message_id}')
            changedeadline = types.InlineKeyboardButton('Изменить дедлайн',
                                                        callback_data=f'changedeadline-{item[0]}-{msg.message_id}')
            changestatus = types.InlineKeyboardButton('Изменить статус',
                                                      callback_data=f'changestatus-{item[0]}-{msg.message_id}')
            delete = types.InlineKeyboardButton('Удалить', callback_data=f'delete-{item[0]}-{msg.message_id}')
            temp_markup.row(changetask, changedeadline)
            temp_markup.row(changestatus, delete)

            msg = await bot.send_message(message.chat.id,
                                         f'Задача: {item[1]}\n'
                                         f'Создатель: {creator_info[0][1]} {creator_info[0][2]}\n'
                                         f'Дедлайн: {item[4]}\n'
                                         f'Статус: {status_format[item[5]]}',
                                         reply_markup=temp_markup)
            msg_list.append(msg)
    elif message.text == 'Добавить задачу':
        await bot.send_message(message.chat.id, f'Введите название задачи', reply_markup=empty)
        state = 'add_task'
    elif message.text == 'Редактировать профиль':
        name, surname = None, None
        state = 'changing_name'
        await bot.send_message(message.chat.id, f'Введите Имя', reply_markup=keyboard)
    elif message.text == 'Панель администрирования':
        await bot.send_message(message.chat.id, f'Панель администрирования', reply_markup=administration)
    elif message.text == 'Список пользователей':
        state = None
        msg = await bot.send_message(message.chat.id, f'Пользователи:', reply_markup=administration)
        items = await show_database_users()
        print(items)
        msg_list = []
        for item in items:
            print(f'{item[1]} {item[2]}')
            # creator_info = await find_user_byid(item[2])
            temp_markup = types.InlineKeyboardMarkup()
            createtask = types.InlineKeyboardButton('Добавить задание',
                                                    callback_data=f'createtask-{item[0]}-{msg.message_id}')
            showtasks = types.InlineKeyboardButton('Просмотреть задания',
                                                   callback_data=f'showtasks-{item[0]}-{msg.message_id}')
            giveadmin = types.InlineKeyboardButton('Назначить администратором',
                                                   callback_data=f'giveadmin-{item[0]}-{msg.message_id}')
            takeadmin = types.InlineKeyboardButton('Снять администрацию',
                                                   callback_data=f'takeadmin-{item[0]}-{msg.message_id}')
            temp_markup.row(createtask, showtasks)
            temp_markup.row(giveadmin)
            temp_markup.row(takeadmin)

            msg = await bot.send_message(message.chat.id,
                                         f'{item[1]} {item[2]}',
                                         reply_markup=temp_markup)
            msg_list.append(msg)
    elif message.text == 'Назад':
        await bot.send_message(message.chat.id, f'Главное меню', reply_markup=keyboard)
    else:
        if state == 'changing_name':
            name = message.text
            await bot.send_message(message.chat.id, f'Введите Фамилию', reply_markup=keyboard)
            state = 'changing_surname'
        elif state == 'changing_surname':
            surname = message.text
            await change_user_info(name, surname, message.chat.id)
            user_info = await exist_user(message.from_user.id)
            await bot.send_message(message.chat.id,
                                   f'Данные сохранены  {user_info[0][1]} {user_info[0][2]}',
                                   reply_markup=keyboard)
            state = None
        elif state == 'changing_task_name':
            task_name = message.text
            await change_task(task_name, task_id)
            for messages in msg_list:
                await bot.delete_message(message.chat.id, messages.message_id)
            msg_list = []
            msg = await bot.send_message(message.chat.id, f'Задачи:', reply_markup=tasks_keyboard)
            items = await show_tasks(user_info[0][0])
            for item in items:
                creator_info = await find_user_byid(item[2])

                temp_markup = types.InlineKeyboardMarkup()
                changetask = types.InlineKeyboardButton('Изменить название',
                                                        callback_data=f'changetask-{item[0]}-{msg.message_id}')
                changedeadline = types.InlineKeyboardButton('Изменить дедлайн',
                                                            callback_data=f'changedeadline-{item[0]}-{msg.message_id}')
                changestatus = types.InlineKeyboardButton('Изменить статус',
                                                          callback_data=f'changestatus-{item[0]}-{msg.message_id}')
                delete = types.InlineKeyboardButton('Удалить', callback_data=f'delete-{item[0]}-{msg.message_id}')
                temp_markup.row(changetask, changedeadline)
                temp_markup.row(changestatus, delete)

                msg = await bot.send_message(message.chat.id,
                                             f'Задача: {item[1]}\n'
                                             f'Создатель: {creator_info[0][1]} {creator_info[0][2]}\n'
                                             f'Дедлайн: {item[4]}\n'
                                             f'Статус: {status_format[item[5]]}',
                                             reply_markup=temp_markup)
                msg_list.append(msg)
            task_name, task_id, state = None, None, None
        elif state == 'add_task':
            task_name = message.text

            msg = await bot.send_message(message.chat.id, f'Выберите год дедлайна', reply_markup=year_markup)
            state = 'add_deadline_m'
        elif state == 'add_task_admin':
            task_name = message.text

            msg = await bot.send_message(message.chat.id, f'Выберите год дедлайна', reply_markup=year_markup)
            state = 'add_deadline_m_admin'
        elif state == 'input_name':
            name = message.text
            await bot.send_message(message.chat.id, f'Введите Фамилию', reply_markup=empty)
            state = 'input_surname'
        elif state == 'input_surname':
            surname = message.text
            await add_user(name, surname, message.chat.id, 0)
            user_info = await exist_user(message.from_user.id)
            if user_info[0][4] == 1:
                admin = 1
                keyboard = keyboard_admin
            else:
                keyboard = keyboard_menu

            await bot.send_message(message.chat.id,
                                   f'Данные сохранены  {user_info[0][1]} {user_info[0][2]}',
                                   reply_markup=keyboard)
            state, name, surname = None, None, None
        else:
            pass


# region Menu
month_markup = types.InlineKeyboardMarkup()
m1 = types.InlineKeyboardButton('Январь', callback_data='1-0')
m2 = types.InlineKeyboardButton('Февраль', callback_data='2-0')
m3 = types.InlineKeyboardButton('Март', callback_data='3-0')
m4 = types.InlineKeyboardButton('Апрель', callback_data='4-0')
m5 = types.InlineKeyboardButton('Май', callback_data='5-0')
m6 = types.InlineKeyboardButton('Июнь', callback_data='6-0')
m7 = types.InlineKeyboardButton('Июль', callback_data='7-0')
m8 = types.InlineKeyboardButton('Август', callback_data='8-0')
m9 = types.InlineKeyboardButton('Сентябрь', callback_data='9-0')
m10 = types.InlineKeyboardButton('Октябрь', callback_data='10-0')
m11 = types.InlineKeyboardButton('Ноябрь', callback_data='11-0')
m12 = types.InlineKeyboardButton('Декабрь', callback_data='12-0')
month_markup.row(m1, m2, m3)
month_markup.row(m4, m5, m6)
month_markup.row(m7, m8, m9)
month_markup.row(m10, m11, m12)

day_markup = types.InlineKeyboardMarkup()
d1 = types.InlineKeyboardButton('1', callback_data='1-0')
d2 = types.InlineKeyboardButton('2', callback_data='2-0')
d3 = types.InlineKeyboardButton('3', callback_data='3-0')
d4 = types.InlineKeyboardButton('4', callback_data='4-0')
d5 = types.InlineKeyboardButton('5', callback_data='5-0')
d6 = types.InlineKeyboardButton('6', callback_data='6-0')
d7 = types.InlineKeyboardButton('7', callback_data='7-0')
d8 = types.InlineKeyboardButton('8', callback_data='8-0')
d9 = types.InlineKeyboardButton('9', callback_data='9-0')
d10 = types.InlineKeyboardButton('10', callback_data='10-0')
d11 = types.InlineKeyboardButton('11', callback_data='11-0')
d12 = types.InlineKeyboardButton('12', callback_data='12-0')
d13 = types.InlineKeyboardButton('13', callback_data='13-0')
d14 = types.InlineKeyboardButton('14', callback_data='14-0')
d15 = types.InlineKeyboardButton('15', callback_data='15-0')
d16 = types.InlineKeyboardButton('16', callback_data='16-0')
d17 = types.InlineKeyboardButton('17', callback_data='17-0')
d18 = types.InlineKeyboardButton('18', callback_data='18-0')
d19 = types.InlineKeyboardButton('19', callback_data='19-0')
d20 = types.InlineKeyboardButton('20', callback_data='20-0')
d21 = types.InlineKeyboardButton('21', callback_data='21-0')
d22 = types.InlineKeyboardButton('22', callback_data='22-0')
d23 = types.InlineKeyboardButton('23', callback_data='23-0')
d24 = types.InlineKeyboardButton('24', callback_data='24-0')
d25 = types.InlineKeyboardButton('25', callback_data='25-0')
d26 = types.InlineKeyboardButton('26', callback_data='26-0')
d27 = types.InlineKeyboardButton('27', callback_data='27-0')
d28 = types.InlineKeyboardButton('28', callback_data='28-0')
if m == 2:
    day_markup.row(d1, d2, d3, d4, d5)
    day_markup.row(d6, d7, d8, d9, d10)
    day_markup.row(d11, d12, d13, d14, d15)
    day_markup.row(d16, d17, d18, d19, d20)
    day_markup.row(d21, d22, d23, d24, d25)
    day_markup.row(d26, d27, d28)
elif m in (4, 6, 9, 11):
    d29 = types.InlineKeyboardButton('29', callback_data='29-0')
    d30 = types.InlineKeyboardButton('30', callback_data='30-0')
    day_markup.row(d1, d2, d3, d4, d5)
    day_markup.row(d6, d7, d8, d9, d10)
    day_markup.row(d11, d12, d13, d14, d15)
    day_markup.row(d16, d17, d18, d19, d20)
    day_markup.row(d21, d22, d23, d24, d25)
    day_markup.row(d26, d27, d28, d29, d30)
else:
    d29 = types.InlineKeyboardButton('29', callback_data='29-0')
    d30 = types.InlineKeyboardButton('30', callback_data='30-0')
    d31 = types.InlineKeyboardButton('31', callback_data='31-0')
    day_markup.row(d1, d2, d3, d4, d5)
    day_markup.row(d6, d7, d8, d9, d10)
    day_markup.row(d11, d12, d13, d14, d15)
    day_markup.row(d16, d17, d18, d19, d20)
    day_markup.row(d21, d22, d23, d24, d25)
    day_markup.row(d26, d27, d28, d29, d30)
    day_markup.row(d31)

hour_markup = types.InlineKeyboardMarkup()
h1 = types.InlineKeyboardButton('1', callback_data='1-0')
h2 = types.InlineKeyboardButton('2', callback_data='2-0')
h3 = types.InlineKeyboardButton('3', callback_data='3-0')
h4 = types.InlineKeyboardButton('4', callback_data='4-0')
h5 = types.InlineKeyboardButton('5', callback_data='5-0')
h6 = types.InlineKeyboardButton('6', callback_data='6-0')
h7 = types.InlineKeyboardButton('7', callback_data='7-0')
h8 = types.InlineKeyboardButton('8', callback_data='8-0')
h9 = types.InlineKeyboardButton('9', callback_data='9-0')
h10 = types.InlineKeyboardButton('10', callback_data='10-0')
h11 = types.InlineKeyboardButton('11', callback_data='1-0')
h12 = types.InlineKeyboardButton('12', callback_data='12-0')
h13 = types.InlineKeyboardButton('13', callback_data='13-0')
h14 = types.InlineKeyboardButton('14', callback_data='14-0')
h15 = types.InlineKeyboardButton('15', callback_data='15-0')
h16 = types.InlineKeyboardButton('16', callback_data='16-0')
h17 = types.InlineKeyboardButton('17', callback_data='17-0')
h18 = types.InlineKeyboardButton('18', callback_data='18-0')
h19 = types.InlineKeyboardButton('19', callback_data='19-0')
h20 = types.InlineKeyboardButton('20', callback_data='20-0')
h21 = types.InlineKeyboardButton('21', callback_data='21-0')
h22 = types.InlineKeyboardButton('22', callback_data='22-0')
h23 = types.InlineKeyboardButton('23', callback_data='23-0')
h24 = types.InlineKeyboardButton('24', callback_data='24-0')
hour_markup.row(h1, h2, h3, h4, h5)
hour_markup.row(h6, h7, h8, h9, h10)
hour_markup.row(h11, h12, h13, h14, h15)
hour_markup.row(h16, h17, h18, h19, h20)
hour_markup.row(h21, h22, h23, h24)


# endregion


@bot.callback_query_handler(lambda call: True)
async def handle(call):
    global admin, telegram_id, user_id, keyboard, state, name, surname, task_id, msg, task_name
    global msg_list, year, month, day, h, m, status, status_format, temp_userid
    await bot.send_chat_action(call.message.chat.id, 'typing')

    user_info = await exist_user(telegram_id)
    if user_info[0][4] == 1:
        admin = 1
        keyboard = keyboard_admin
    else:
        keyboard = keyboard_menu

    data = call.data.split('-')
    if data[0] == 'changetask':
        state = 'changing_task_name'
        task_id = data[1]
        await bot.send_message(call.message.chat.id, f'Введите новое название', reply_markup=keyboard)
        await bot.answer_callback_query(call.id)
    elif data[0] == 'changedeadline':
        task_id = data[1]
        await bot.send_message(call.message.chat.id, f'Изменение дедлайна', reply_markup=empty)
        await bot.answer_callback_query(call.id)
        year, month, day, h, m = None, None, None, None, None
        state = 'changing_task_deadline'

        msg = await bot.send_message(call.message.chat.id, f'Выберите год', reply_markup=year_markup)
        await bot.answer_callback_query(call.id)
        state = 'choosing_month_up'
    elif data[0] == 'changestatus':
        task_id = data[1]
        await bot.send_message(call.message.chat.id, f'Изменение статуса', reply_markup=empty)
        await bot.answer_callback_query(call.id)
        state = 'changing_task_status'

        status_markup = types.InlineKeyboardMarkup()
        st0 = types.InlineKeyboardButton('план', callback_data='0-0')
        st1 = types.InlineKeyboardButton('в работе', callback_data='1-0')
        st2 = types.InlineKeyboardButton('выполнена', callback_data='2-0')

        status_markup.row(st0)
        status_markup.row(st1)
        status_markup.row(st2)
        msg = await bot.send_message(call.message.chat.id, f'Выберите статус', reply_markup=status_markup)
        await bot.answer_callback_query(call.id)
        state = 'updating_task_status'
    elif data[0] == 'delete':
        task_id = data[1]
        await delete_task(task_id)
        await bot.send_message(call.message.chat.id, f'Удалено', reply_markup=tasks_keyboard)
        await bot.answer_callback_query(call.id)

        for messages in msg_list:
            await bot.delete_message(call.message.chat.id, messages.message_id)
        msg_list = []
        msg = await bot.send_message(call.message.chat.id, f'Задачи:', reply_markup=tasks_keyboard)
        items = await show_tasks(user_info[0][0])
        for item in items:
            creator_info = await find_user_byid(item[2])

            temp_markup = types.InlineKeyboardMarkup()
            changetask = types.InlineKeyboardButton('Изменить название',
                                                    callback_data=f'changetask-{item[0]}-{msg.message_id}')
            changedeadline = types.InlineKeyboardButton('Изменить дедлайн',
                                                        callback_data=f'changedeadline-{item[0]}-{msg.message_id}')
            changestatus = types.InlineKeyboardButton('Изменить статус',
                                                      callback_data=f'changestatus-{item[0]}-{msg.message_id}')
            delete = types.InlineKeyboardButton('Удалить', callback_data=f'delete-{item[0]}-{msg.message_id}')
            temp_markup.row(changetask, changedeadline)
            temp_markup.row(changestatus, delete)

            msg = await bot.send_message(call.message.chat.id,
                                         f'Задача: {item[1]}\n'
                                         f'Создатель: {creator_info[0][1]} {creator_info[0][2]}\n'
                                         f'Дедлайн: {item[4]}\n'
                                         f'Статус: {status_format[item[5]]}',
                                         reply_markup=temp_markup)
            await bot.answer_callback_query(call.id)
            msg_list.append(msg)
        task_id = None
    elif data[0] == 'createtask':
        await bot.send_message(call.message.chat.id, f'Введите название задачи', reply_markup=empty)
        temp_userid = data[1]
        state = 'add_task_admin'
    elif data[0] == 'showtasks':
        worker_id = data[1]
        msg = await bot.send_message(call.message.chat.id, f'Задачи:', reply_markup=tasks_keyboard)
        items = await show_tasks(worker_id)
        msg_list = []
        for item in items:
            creator_info = await find_user_byid(item[2])

            msg = await bot.send_message(call.message.chat.id,
                                         f'Задача: {item[1]}\n'
                                         f'Создатель: {creator_info[0][1]} {creator_info[0][2]}\n'
                                         f'Дедлайн: {item[4]}\n'
                                         f'Статус: {status_format[item[5]]}',
                                         reply_markup=administration)
            await bot.answer_callback_query(call.id)
            msg_list.append(msg)
    elif data[0] == 'giveadmin':
        worker_id = data[1]
        await set_user_admin(worker_id, 1)
        await bot.send_message(call.message.chat.id, f'Пользователь назначен администратором',
                               reply_markup=tasks_keyboard)
        await bot.answer_callback_query(call.id)
    elif data[0] == 'takeadmin':
        worker_id = data[1]
        await set_user_admin(worker_id, 1)
        await bot.send_message(call.message.chat.id, f'Пользователь снят с администрации', reply_markup=tasks_keyboard)
        await bot.answer_callback_query(call.id)
    else:
        if state == 'choosing_month_up':
            year = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите месяц', reply_markup=month_markup)
            await bot.answer_callback_query(call.id)
            state = 'choosing_day_up'
        elif state == 'choosing_day_up':
            month = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите день', reply_markup=day_markup)
            await bot.answer_callback_query(call.id)
            state = 'choosing_hour_up'
        elif state == 'choosing_hour_up':
            day = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите час', reply_markup=hour_markup)
            await bot.answer_callback_query(call.id)
            state = 'updating_deadline'
        elif state == 'updating_deadline':
            h = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            await change_deadline_task(f'{year}-{month}-{day} {h}:00:00', task_id)

            msg = await bot.send_message(call.message.chat.id, f'Данные записаны', reply_markup=tasks_keyboard)
            await bot.answer_callback_query(call.id)
            for messages in msg_list:
                await bot.delete_message(call.message.chat.id, messages.message_id)
            msg_list = []
            msg = await bot.send_message(call.message.chat.id, f'Задачи:', reply_markup=tasks_keyboard)
            items = await show_tasks(user_info[0][0])
            for item in items:
                creator_info = await find_user_byid(item[2])

                temp_markup = types.InlineKeyboardMarkup()
                changetask = types.InlineKeyboardButton('Изменить название',
                                                        callback_data=f'changetask-{item[0]}-{msg.message_id}')
                changedeadline = types.InlineKeyboardButton('Изменить дедлайн',
                                                            callback_data=f'changedeadline-{item[0]}-{msg.message_id}')
                changestatus = types.InlineKeyboardButton('Изменить статус',
                                                          callback_data=f'changestatus-{item[0]}-{msg.message_id}')
                delete = types.InlineKeyboardButton('Удалить', callback_data=f'delete-{item[0]}-{msg.message_id}')
                temp_markup.row(changetask, changedeadline)
                temp_markup.row(changestatus, delete)

                msg = await bot.send_message(call.message.chat.id,
                                             f'Задача: {item[1]}\n'
                                             f'Создатель: {creator_info[0][1]} {creator_info[0][2]}\n'
                                             f'Дедлайн: {item[4]}\n'
                                             f'Статус: {status_format[item[5]]}',
                                             reply_markup=temp_markup)
                await bot.answer_callback_query(call.id)
                msg_list.append(msg)
            state, task_id, year, month, day, h = None, None, None, None, None, None
        elif state == 'updating_task_status':
            status = data[0]
            await bot.delete_message(call.message.chat.id, msg.message_id)
            await change_status_task(status, task_id)

            msg = await bot.send_message(call.message.chat.id, f'Данные записаны', reply_markup=tasks_keyboard)
            await bot.answer_callback_query(call.id)
            for messages in msg_list:
                await bot.delete_message(call.message.chat.id, messages.message_id)
            msg_list = []
            msg = await bot.send_message(call.message.chat.id, f'Задачи:', reply_markup=tasks_keyboard)
            items = await show_tasks(user_info[0][0])
            for item in items:
                creator_info = await find_user_byid(item[2])

                temp_markup = types.InlineKeyboardMarkup()
                changetask = types.InlineKeyboardButton('Изменить название',
                                                        callback_data=f'changetask-{item[0]}-{msg.message_id}')
                changedeadline = types.InlineKeyboardButton('Изменить дедлайн',
                                                            callback_data=f'changedeadline-{item[0]}-{msg.message_id}')
                changestatus = types.InlineKeyboardButton('Изменить статус',
                                                          callback_data=f'changestatus-{item[0]}-{msg.message_id}')
                delete = types.InlineKeyboardButton('Удалить', callback_data=f'delete-{item[0]}-{msg.message_id}')
                temp_markup.row(changetask, changedeadline)
                temp_markup.row(changestatus, delete)

                msg = await bot.send_message(call.message.chat.id,
                                             f'Задача: {item[1]}\n'
                                             f'Создатель: {creator_info[0][1]} {creator_info[0][2]}\n'
                                             f'Дедлайн: {item[4]}\n'
                                             f'Статус: {status_format[item[5]]}',
                                             reply_markup=temp_markup)
                await bot.answer_callback_query(call.id)
                msg_list.append(msg)
            state, task_id, status = None, None, None
        elif state == 'add_deadline_m':
            year = data[0]
            temp_userid = user_id

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите месяц', reply_markup=month_markup)
            await bot.answer_callback_query(call.id)
            state = 'add_deadline_d'
        elif state == 'add_deadline_m_admin':
            year = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите месяц', reply_markup=month_markup)
            await bot.answer_callback_query(call.id)
            state = 'add_deadline_d'
        elif state == 'add_deadline_d':
            month = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите день', reply_markup=day_markup)
            await bot.answer_callback_query(call.id)
            state = 'add_deadline_h'
        elif state == 'add_deadline_h':
            day = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            msg = await bot.send_message(call.message.chat.id, f'Выберите час', reply_markup=hour_markup)
            await bot.answer_callback_query(call.id)
            state = 'add_status'
        elif state == 'add_status':
            h = data[0]

            await bot.delete_message(call.message.chat.id, msg.message_id)
            status_markup = types.InlineKeyboardMarkup()
            st0 = types.InlineKeyboardButton('план', callback_data='0-0')
            st1 = types.InlineKeyboardButton('в работе', callback_data='1-0')
            st2 = types.InlineKeyboardButton('выполнена', callback_data='2-0')

            status_markup.row(st0)
            status_markup.row(st1)
            status_markup.row(st2)
            msg = await bot.send_message(call.message.chat.id, f'Выберите статус', reply_markup=status_markup)
            await bot.answer_callback_query(call.id)
            state = 'save_task'
        elif state == 'save_task':
            status = data[0]
            await bot.delete_message(call.message.chat.id, msg.message_id)
            await add_task(task_name, user_id, temp_userid, f'{year}-{month}-{day} {h}:00:00', status)
            loop.create_task(task(task_name, call.message.chat.id, year, month, day, h, status))

            msg = await bot.send_message(call.message.chat.id, f'Данные записаны', reply_markup=tasks_keyboard)
            await bot.answer_callback_query(call.id)
            state, task_id, year, month, day, h, task_name = None, None, None, None, None, None, None
        else:
            pass


# bot.remove_webhook()
# bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'r'))
#
# uvicorn.run(app,
#             host=WEBHOOK_LISTEN,
#             port=WEBHOOK_PORT,
#             ssl_certfile=WEBHOOK_SSL_CERT,
#             ssl_keyfile=WEBHOOK_SSL_PRIV)

while True:
    try:
        loop = asyncio.get_event_loop()
        asyncio.run(bot.polling(none_stop=True, interval=0, timeout=20))
    except Exception as e:
        print(e)
        time.sleep(2)
