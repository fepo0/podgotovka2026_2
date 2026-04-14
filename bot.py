import telebot
import modules.config as config
import modules.replykeyboards as ReplyKeyboards
import modules.types as types
import requests, sqlite3
bot=telebot.TeleBot(config.BOT_TOKEN)
startMarkup = ReplyKeyboards.startMarkup()
mode=0#0-toksok,1-kiber
url="http://127.0.0.1:8080/"

# + Федорцова П.С.
WAITING_FOR_TEXT = {}
# - Федорцова П.С.

@bot.message_handler(commands=["start"])
def start(message):
    connection = sqlite3.connect('database/database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM Users WHERE id = ?', (message.from_user.id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO Users (id, username, name, last_name, mode) VALUES (?, ?, ?, ?, ?)", (message.from_user.id,message.from_user.username,message.from_user.first_name,message.from_user.last_name, 0))
    bot.send_message(message.chat.id,"HI",reply_markup=startMarkup)
    # + Федорцова П.С.
    WAITING_FOR_TEXT[message.from_user.id] = False
    # - Федорцова П.С.
    connection.commit()
    connection.close()


@bot.message_handler(func= lambda message: "токсичность" in message.text.lower())
def toksik(message):
    connection = sqlite3.connect('database/database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE Users SET mode = ? WHERE id = ?', (0,message.from_user.id))
    connection.commit()
    connection.close()
    # + Федорцова П.С.
    WAITING_FOR_TEXT[message.from_user.id] = True
    bot.send_message(message.chat.id, "Введите текст для проверки на токсичность.")
    # - Федорцова П.С.

@bot.message_handler(func= lambda message: "кибербуллинг" in message.text.lower())
def cybulb(message):
    connection = sqlite3.connect('database/database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE Users SET mode = ? WHERE id = ?', (1,message.from_user.id))
    connection.commit()
    connection.close()
    # + Федорцова П.С.
    WAITING_FOR_TEXT[message.from_user.id] = True
    bot.send_message(message.chat.id, "Введите текст для проверки на кибербуллинг.")
    # - Федорцова П.С.

@bot.message_handler(func= lambda message: "токсичная кибербулльность" in message.text.lower())
def toksik_cybulb(message):
    connection = sqlite3.connect('database/database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE Users SET mode = ? WHERE id = ?', (2,message.from_user.id))
    connection.commit()
    connection.close()
    # + Федорцова П.С.
    WAITING_FOR_TEXT[message.from_user.id] = True
    bot.send_message(message.chat.id, "Введите текст для совместной проверки моделей.")
    # - Федорцова П.С.

@bot.message_handler(content_types=["text"])
def get_message(message):
    # + Федорцова П.С.
    if message.text.lower() in {
        "токсичность",
        "кибербуллинг",
        "токсичная кибербулльность",
    }:
        return
    if not WAITING_FOR_TEXT.get(message.from_user.id, False):
        bot.send_message(message.chat.id, "Сначала выберите режим кнопкой, затем отправьте текст.")
        return
    # - Федорцова П.С.
    data = {"text": message.text}
    
    connection = sqlite3.connect('database/database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT mode FROM Users WHERE id = ?', (message.from_user.id,))
    mode=cursor.fetchone()[0]
    connection.commit()
    connection.close()
    subdomen=config.SUBDOMEN_DICT[mode]
    # + Федорцова П.С.
    loading_message = bot.send_message(message.chat.id, "Загрузка...")
    try:
        api_response = requests.post(url+subdomen, json=data, timeout=60)
        api_response.raise_for_status()
        response = api_response.json()
    except requests.RequestException:
        bot.edit_message_text("Ошибка обращения к API.", message.chat.id, loading_message.message_id)
        return
    except ValueError:
        bot.edit_message_text("API вернул некорректный ответ.", message.chat.id, loading_message.message_id)
        return
    # - Федорцова П.С.
    result=""
    match mode:
        case 0:
            result=types.Toksik(response)
        case 1:
            result=types.cyber(response)
        case 2:
            result=types.Toksik(response)
            result=types.cyber(response,result)
    # + Федорцова П.С.
    WAITING_FOR_TEXT[message.from_user.id] = False
    bot.edit_message_text(result, message.chat.id, loading_message.message_id)
    # - Федорцова П.С.
    
    
connection = sqlite3.connect('database/database.db')
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY,
username TEXT NOT NULL,
name TEXT,
last_name TEXT,
mode INTEGER NOT NULL
)
''')
connection.commit()
connection.close()
bot.infinity_polling()