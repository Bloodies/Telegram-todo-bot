[Демонстрация работы](https://github.com/Bloodies/Telegram-todo-bot/blob/Bloodies/docs/onwork.gif)

Предмет: разработка чат бота (telegram) для работы со списком дел

Цели и задачи приложения
1.	Создание для чат-бота CRUD (CREATE, READ, UPDATE, DELETE) системы для собственного тайм-менеджмента.
2.	Создание алгоритма уведомления о сроках выполнения задач

Функциональные задачи приложения
1.	Приложение должно хранить записи о пользователях и их “списках дел” с указанием конкретной даты и времени
2.	Задача должна содержать в себе информацию о создавшем её пользователе, дате и времени “дедлайна”, статусе задачи (план, в работе, выполнена)
3.	Приложение должно позволять создавать, просматривать, обновлять и удалять данные по “спискам дел”
4.	Приложение должно уведомлять пользователя за определённое время до окончания сроков выполнения задачи и по истечению данного срока. Уведомления должны быть логично сопоставлены со статусом задачи 

Нефункциональные задачи
1.	Приложение должно быть удобным в использовании. Не должно быть такого, что пользователю нужно ввести всю информацию о задаче, разделяя записи спец. символом.
2.	Приложение должно адекватно реагировать на некорректный ввод пользователя.

Дополнительный функционал (по усмотрению)
1.	Создание ролей в боте - возможность создания “Админа”, который может просматривать задачи других и добавлять им новые. Пользователь, получивший такую задачу, должен получать уведомление о получении новой задачи

Технические средства реализации
1.	Python3.9/3.10
2.	FastAPI/aiohttp (первый предпочтительнее)
3.	Связь с тг - webhooks
4.	Sqlalchemy для запросов в БД (обязательно асинхронный)
5.	Запросы в БД - чистый SQL/встроенный в SQLAlchemy ORM
6.	БД - на усмотрение пользователя, желательно реляционная
7.	Asyncio для реализации уведомлений
