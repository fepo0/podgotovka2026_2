from telebot.types import ReplyKeyboardMarkup,KeyboardButton


def startMarkup():
    keyboard=ReplyKeyboardMarkup()
    button1=KeyboardButton("Токсичность")
    button2=KeyboardButton("Кибербуллинг")
    # + Федорцова П.С.
    # button3=KeyboardButton("Токсчиная кибербульность")
    button3=KeyboardButton("Токсичная кибербулльность")
    # - Федорцова П.С.
    keyboard.add(button1,button2,button3)
    return keyboard