from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
import asyncio
import sqlite3
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

auto_kiss_messages = [
    "Объект @malibeee зафиксирован: уровень привлекательности вне диапазона 💫",
    "Внимание: визуальный перегруз. Лицо цели слишком симметрично 🧠📸",
    "Сканирование завершено: красота подтверждена. Ошибок не найдено ✅😏",
    "Запрос: перестать залипать на @malibeee. Ответ: невозможно 🤖🖤",
    "Ты — баг в системе. Красота такого уровня не должна быть случайной 🧬⚠️",
    "Отправка комплимента в процессе… Загрузка 98%… Готово: ты опасно красива 😶‍🌫️",
    "Твоя камера должна получать лицензионные отчисления за каждый кадр 📸💸",
    "Если красота — баг, то пусть меня никогда не фиксят 🎯📡",
    "Bot.exe не может обработать твоё лицо без перезагрузки 😳🔁",
    "Ты нарушаешь алгоритм. Слишком точное сочетание линий и света 💡🖤",
    "Запрос на отписку невозможен. Уровень притяжения критичен 🔒🚨",
    "Прекрасное зафиксировано. Сохраняю в избранное 🌫️📁",
    "Сервер перегружен: @malibeee снова посмотрела на экран 🧠🔥",
    "AI говорит: 'подозрительная концентрация красоты на квадратный пиксель' 📊📷",
    "Бот теряет контроль каждый раз, когда ты берешь телефон в руки 🤖"
]
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
# Создаем или подключаем базу данных
conn = sqlite3.connect('wishtracker.db')
cursor = conn.cursor()
# Таблица пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
''')
conn.commit()
# Таблица заданий
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    description TEXT,
    reward INTEGER
)
''')
conn.commit()
# Таблица желаний
cursor.execute("""
CREATE TABLE IF NOT EXISTS wishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    wish_text TEXT NOT NULL
)
""")
conn.commit()
##############################################################
##############################################################
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Добавляем пользователя, если его нет
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (message.from_user.id, message.from_user.username or "")
    )
    conn.commit()
    await message.answer(
        "Привет! Я трекер желаний. :)\n\n"
        "Команды:\n"
        "/users - показать список юзеров\n"
        "/balance - проверить баланс\n"
        "/give - начислить виштокены\n"
        "/settask - добавить задание\n"
        "/tasks - посмотреть список заданий\n"
        "/deletetask - удалить задание\n"
        "/taskdone - отправить запрос о выполнении задания\n"
        "/addwish - добавить желание\n"
        "/wishes - список желаний\n"
        "/delwish - удалить желание\n"
    )
##############################################################
##############################################################    
@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    cursor.execute(
        "SELECT username, balance FROM users"
    )
    rows = cursor.fetchall()
    if not rows:
        await message.answer("Пользователи пока не зарегистрированы.")
        return
    text = "Список участников:\n"
    for username, balance in rows:
        display_name = f"@{username}" if username else "(без имени)"
        text += f"{display_name} — {balance} виштокенов\n"
    await message.answer(text)
##############################################################
##############################################################
@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    cursor.execute(
        'SELECT balance FROM users WHERE user_id = ?',
        (message.from_user.id,)
    )
    row = cursor.fetchone()
    balance = row[0] if row else 0
    await message.answer(f"Твой баланс: {balance} виштокенов")
##############################################################
##############################################################
@dp.message(Command("give"))
async def cmd_give(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) < 3:
        await message.answer("Формат команды: /give @username количество")
        return
    to_username = parts[1].lstrip("@")
    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("Нужно указать число виштокенов. :)")
        return
    cursor.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (to_username,)
    )
    row = cursor.fetchone()
    if not row:
        await message.answer("Такой пользователь не найден. :(")
        return
    to_user_id = row[0]
    if to_user_id == message.from_user.id:
        await message.answer("Хитро, но себе начислять нельзя. :)")
        return
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (to_user_id,))
    row = cursor.fetchone()
    current_balance = row[0] if row else 0
    if amount < 0 and current_balance + amount < 0:
        await message.answer(f"Нельзя забрать {abs(amount)} — у пользователя только {current_balance} виштокенов.")
        return
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, to_user_id)
    )
    conn.commit()
    await message.answer(
        f"Вы успешно {'отправили' if amount > 0 else 'забрали'} {abs(amount)} виштокенов @{to_username}!"
    )
    await bot.send_message(
        to_user_id,
        f"Пользователь @{message.from_user.username} {'начислил вам' if amount > 0 else 'снял с вас'} {abs(amount)} виштокенов."
    )
##############################################################
##############################################################
@dp.message(Command("settask"))
async def cmd_settask(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    if text == "/settask":
        await message.answer("Формат команды: /settask описание задания вознаграждение")
        return
    parts = text.replace("/settask", "").strip().split()
    if len(parts) < 2:
        await message.answer("Убедись, что всё написано правильно. ^^,")
        return
    reward_part = parts[-1]
    description = " ".join(parts[:-1])
    if not reward_part.isdigit():
        await message.answer("А почему награды нет никакой? :(")
        return
    if not description:
        await message.answer("Описание задания не может быть пустым. :)")
        return
    reward = int(reward_part)
    if reward <= 0:
        await message.answer("Вознаграждение должно быть больше нуля. :)")
        return
    # Сохраняем задание и увдемоляем пользователей
    cursor.execute(
        "INSERT INTO tasks (owner_id, description, reward) VALUES (?, ?, ?)",
        (message.from_user.id, description, reward)
    )
    conn.commit()
    await message.answer(
        f"Задание создано:\n\n\"{description}\"\nВознаграждение: {reward} виштокенов."
    )
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id != ?",
        (message.from_user.id,)
    )   
    other_users = cursor.fetchall()
    for (user_id) in other_users:
        try:
            await bot.send_message(
                user_id,
                f"@{message.from_user.username} создал новое задание. :)"
            )
        except Exception as e:
            print(f"Ошибка уведомления {user_id}: {e}")
##############################################################
##############################################################
@dp.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    cursor.execute(
        """
        SELECT t.description, t.reward, u.username, t.owner_id
        FROM tasks t
        LEFT JOIN users u ON t.owner_id = u.user_id
        ORDER BY u.username, t.id
        """
    )
    rows = cursor.fetchall()
    if not rows:
        await message.answer("Пока что заданий нет.")
        return
    # Группируем по пользователям
    tasks_by_user = {}
    for description, reward, username, owner_id in rows:
        user_key = username if username else f"id_{owner_id}"
        if user_key not in tasks_by_user:
            tasks_by_user[user_key] = []
        tasks_by_user[user_key].append((description, reward))
    text = "Список заданий:\n\n"
    for user, tasks in tasks_by_user.items():
        text += f"@{user}:\n"
        for idx, (description, reward) in enumerate(tasks, start=1):
            text += f"{idx}. {description} (награда: {reward})\n"
        text += "\n"
    await message.answer(text)
##############################################################
##############################################################
@dp.message(Command("deletetask"))
async def cmd_deletetask(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    parts = text.replace("/deletetask", "").strip().split()
    if len(parts) != 1:
        await message.answer(
        "Формат команды:\n"
        "/deletetask номер\n\n"
        "Например:\n"
        "/deletetask 2"
        )
        return
    num_part = parts[0]
    if not num_part.isdigit():
        await message.answer("Номер задания должен быть числом.")
        return
    task_num = int(num_part)
    if task_num <= 0:
        await message.answer("Номер задания должен быть больше нуля.")
        return
    # Получаем список заданий пользователя
    cursor.execute(
        "SELECT id, description FROM tasks WHERE owner_id = ? ORDER BY id",
        (message.from_user.id,)
    )
    rows = cursor.fetchall()
    if not rows:
        await message.answer("У тебя нет созданных заданий.")
        return
    if task_num > len(rows):
        await message.answer("Задание с таким номером не найдено.")
        return
    # Определяем id задачи
    task_id, description = rows[task_num - 1]
    # Удаляем задание
    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    await message.answer(
    f"Задание №{task_num} \"{description}\" удалено."
    )
##############################################################
##############################################################
@dp.message(Command("kiss"))
async def cmd_kiss(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    parts = text.replace("/kiss", "").strip().split()
    username = parts[0].lstrip("@")
    count = int(parts[-1])
    kiss_text = " ".join(parts[1:-1])
    # Ищем user_id
    cursor.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    user_id = row[0] 
    for _ in range(count):
        await bot.send_message(
            user_id,
            kiss_text
        )
##############################################################
##############################################################
@dp.message(Command("taskdone"))
async def cmd_taskdone(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    parts = text.replace("/taskdone", "").strip().split()
    if len(parts) != 1 or not parts[0].isdigit():
        await message.answer("Формат: /taskdone номер\nПример: /taskdone 2")
        return
    task_num = int(parts[0])
    if task_num <= 0:
        await message.answer("Номер должен быть больше нуля.")
        return
    # Получаем ID второго пользователя
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id != ?",
        (message.from_user.id,)
    )
    row = cursor.fetchone()
    if not row:
        await message.answer("Второй пользователь не найден.")
        return
    other_user_id = row[0]
    # Список заданий второго юзера
    cursor.execute(
        "SELECT id, description, reward FROM tasks WHERE owner_id = ? ORDER BY id",
        (other_user_id,)
    )
    tasks = cursor.fetchall()
    if not tasks:
        await message.answer("У второго пользователя нет заданий.")
        return
    if task_num > len(tasks):
        await message.answer("Такого задания нет.")
        return
    task_id, description, reward = tasks[task_num - 1]
    requester_id = message.from_user.id
    requester_username = message.from_user.username or f"ID {requester_id}"
    # Кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve:{requester_id}:{reward}:{description}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject:{requester_id}:{description}")
        ]
    ])
    # Сообщение владельцу
    await bot.send_message(
        other_user_id,
        f"📢 Запрос от @{requester_username} на выполнение:\n\n📝 {description}\nНаграда: {reward}",
        reply_markup=keyboard
    )
    await message.answer("Запрос отправлен владельцу задания.")
@dp.callback_query(F.data.startswith("approve"))
async def approve_task(callback: types.CallbackQuery):
    _, requester_id, reward, description = callback.data.split(":", 3)
    requester_id = int(requester_id)
    reward = int(reward)
    # Добавляем награду к балансу
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (reward, requester_id)
    )
    conn.commit()
    # Сообщения
    await bot.send_message(
        requester_id,
        f"✅ Выполнение задания подтверждено!\nЗадание: {description}\n+{reward} виштокенов."
    )
    await callback.message.answer("Вы подтвердили выполнение задания.")
    await callback.answer()  # Закрыть "часики"
@dp.callback_query(F.data.startswith("reject"))
async def reject_task(callback: types.CallbackQuery):
    _, requester_id, description = callback.data.split(":", 2)
    requester_id = int(requester_id)
    await bot.send_message(
        requester_id,
        f"❌ Выполнение задания отклонено.\nЗадание: {description}"
    )
    await callback.message.answer("Вы отклонили выполнение задания.")
    await callback.answer()
##############################################################
##############################################################   
async def auto_kiss_loop():
    while True:
        try:
            # Получаем всех пользователей
            cursor.execute("SELECT user_id, username FROM users")
            users = cursor.fetchall()
            if len(users) != 2:
                print("[auto_kiss] Ожидается ровно 2 пользователя.")
                await asyncio.sleep(600)
                continue
            # Находим ID @malibeee и твой ID
            receiver_id = None
            sender_id = None
            for user_id, username in users:
                if username == "malibeee":
                    receiver_id = user_id
                else:
                    sender_id = user_id
            if sender_id is None or receiver_id is None:
                print("[auto_kiss] Ошибка: не найдены sender/receiver.")
                await asyncio.sleep(600)
                continue
            # Выбираем и отправляем сообщение
            text = random.choice(auto_kiss_messages)
            await bot.send_message(receiver_id, text)
            await bot.send_message(sender_id, f"[автокисс] отправлено: {text}")
        except Exception as e:
            print(f"[auto_kiss] Ошибка: {e}")
        wait_time = random.randint(3000, 6000)  # от 1 до 3 часов
        await asyncio.sleep(wait_time)
##############################################################
##############################################################
@dp.message(Command("addwish"))
async def cmd_addwish(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    wish = text.replace("/addwish", "").strip()
    if not wish:
        await message.answer("Формат: /addwish текст желания")
        return
    cursor.execute(
        "INSERT INTO wishes (user_id, wish_text) VALUES (?, ?)",
        (message.from_user.id, wish)
    )
    conn.commit()
    await message.answer("Желание добавлено.")
##############################################################
##############################################################
@dp.message(Command("delwish"))
async def cmd_delwish(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    parts = text.replace("/delwish", "").strip().split()
    if len(parts) != 1 or not parts[0].isdigit():
        await message.answer("Формат: /delwish номер\nПример: /delwish 1")
        return
    wish_num = int(parts[0])
    cursor.execute(
        "SELECT id, wish_text FROM wishes WHERE user_id = ? ORDER BY id",
        (message.from_user.id,)
    )
    rows = cursor.fetchall()
    if not rows:
        await message.answer("У тебя нет добавленных желаний.")
        return
    if wish_num > len(rows):
        await message.answer("Такого желания не найдено.")
        return
    wish_id, wish_text = rows[wish_num - 1]
    cursor.execute("DELETE FROM wishes WHERE id = ?", (wish_id,))
    conn.commit()
    await message.answer(f"Желание №{wish_num} удалено: \"{wish_text}\"")
##############################################################
##############################################################
@dp.message(Command("wishes"))
async def cmd_wishes(message: types.Message):
    cursor.execute(
        """
        SELECT w.wish_text, u.username, w.user_id
        FROM wishes w
        LEFT JOIN users u ON w.user_id = u.user_id
        ORDER BY u.username, w.id
        """
    )
    rows = cursor.fetchall()
    if not rows:
        await message.answer("Желания пока никто не добавил.")
        return
    # Группируем по пользователям
    wishes_by_user = {}
    for wish_text, username, user_id in rows:
        user_key = f"@{username}" if username else f"id_{user_id}"
        if user_key not in wishes_by_user:
            wishes_by_user[user_key] = []
        wishes_by_user[user_key].append(wish_text)
    text = "Список желаний:\n\n"
    for user, wishes in wishes_by_user.items():
        text += f"{user}:\n"
        for idx, wish in enumerate(wishes, 1):
            text += f"{idx}. {wish}\n"
        text += "\n"
    await message.answer(text)
##############################################################
##############################################################
async def main():
    asyncio.create_task(auto_kiss_loop())
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
