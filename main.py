import random
import re

import wikipedia
import telebot
import config
from telebot import types
import sqlite3

bot = telebot.TeleBot(config.bot)

number = False
game = False
wiki = False
num = False
admins = [5025000923]
clients = []
text = ""
link = ""

# Создали базу данных
conn = sqlite3.connect("users.db", check_same_thread=False)
# объект-курсор для запросов в бд (добавить, удалить)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INT);")
conn.commit()

@bot.message_handler(commands=["start"])
def start_command(message):
    if message.chat.id in admins:
        help(message)
    else:
        info = cur.execute("SELECT * FROM users WHERE id=?", (message.chat.id,)).fetchone()
        if not info:
            cur.execute("INSERT INTO users (id) VALUES (?)", (message.chat.id,))
            conn.commit()
            bot.send_message(message.chat.id, "Теперь вы будете получать рассылку!")

    bot.reply_to(message, "Hello, how are you?")

def help(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Редактировать текст"))
    markup.add(types.KeyboardButton("Редактировать ссылку"))
    markup.add(types.KeyboardButton("Показать текст"))
    markup.add(types.KeyboardButton("Начать рассылку"))
    markup.add(types.KeyboardButton("Помощь"))
    bot.send_message(message.chat.id, "Команды для бота: \n"
                                      "/edit_text - Редактировать текст. \n"
                                      "/edit_link - Редактировать ссылку. \n"
                                      "/show_message - Показать текст. \n"
                                      "/send or /send_message - Начать рассылку. \n"
                                      "/help - Помощь.", reply_markup=markup)

@bot.message_handler(commands=["show_message"])
def show_message(message):
    if message.chat.id in admins:
        bot.send_message(message.chat.id, f"Подготовленные текст для рассылки:\n"
                                          f"{text}\n"
                                          f"{link}")


@bot.message_handler(commands=["edit_text"])
def edit_text(message):
    m = bot.send_message(message.chat.id, "Введите сообщение для рассылки")
    bot.register_next_step_handler(m, save_text)

def save_text(message):
    global text
    if message.text not in ["Изменить текст", "Изменить ссылку"]:
        text = message.text
        bot.send_message(message.chat.id, f"Я сохранил текст: {text}")
    else:
        bot.send_message(message.chat.id, "текст некорректный.")


@bot.message_handler(commands=["edit_link"])
def edit_link(message):
    m = bot.send_message(message.chat.id, "Введите ссылку для рассылки")
    bot.register_next_step_handler(m, save_link)

def save_link(message):
    global link
    regex = re.compile(
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # проверка dot
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # проверка ip 
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if message.text is not None and regex.search(message.text):
        link = message.text
        bot.send_message(message.chat.id, f"Я сохранил link: {link}")
    else:
        m = bot.send_message(message.chat.id, "Ссылка некорректная,введи еще раз")
        bot.register_next_step_handler(m, save_link)


@bot.message_handler(commands=["send", "send_message"])
def send_message(message):
    global text, link
    if message.chat.id in admins:
        if text != "":
            if link != "":
                cur.execute("SELECT id FROM users")
                massive = cur.fetchall()
                print(massive)
                for client in massive:
                    id = client[0]
                    sending(id)
                else:
                    text = ""
                    link = ""
            else:
                bot.send_message(message.chat.id, "Ссылка не приложена!")
        else:
            bot.send_message(message.chat.id, "Текст не приложены!")

def sending(id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Click me", url=link))
    bot.send_message(id, text, reply_markup=markup)




@bot.message_handler(commands=["greet"])
def test(message):
    bot.send_message(message.chat.id, "Bot you send message")

@bot.message_handler(commands=["play"])
def bot_play_games(message):
    markup_inline = types.InlineKeyboardMarkup() # 1- Создать клавиатуру
    btn_y = types.InlineKeyboardButton(text="yes", callback_data="yes") # 2- создать кнопки для клав.
    btn_n = types.InlineKeyboardButton(text="no", callback_data="no")
    markup_inline.add(btn_y, btn_n)
    bot.send_message(message.chat.id, "You want to play games?", reply_markup=markup_inline)

@bot.callback_query_handler(func=lambda call:True)
def callback_buttons(call):
    if call.data == "yes":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Угадайка")
        btn2 = types.KeyboardButton("Википедия")
        markup.add(btn1, btn2)
        bot.send_message(call.message.chat.id, "Выбери, что хочешь?", reply_markup=markup)
    elif call.data == "no":
        pass


@bot.message_handler(content_types=["text"])
def type_text(message):
    global game, wiki
    text = message.text.lower()
    if wiki:
        bot.send_message(message.chat.id, get_wiki(text))
    if text == "привет":
        bot.send_message(message.chat.id, "Hello, how are you?")
    elif text == "угадайка":
        game_random_number(message)
        game = True
    elif text == str(num) and text in ["1", "2", "3"] and game:
        game = False
        bot.send_message(message.chat.id, "Угадал!")
    elif text == "википедия":
        bot.send_message(message.chat.id, "Что тебе найти в википедии?")
        wiki = True
    elif text == "редактировать текст":
        edit_text(message)
    elif text == "редактировать ссылку":
        edit_link(message)

def game_random_number(message):
    global num
    num = random.randint(1, 3)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("1"))
    markup.add(types.KeyboardButton("2"))
    markup.add(types.KeyboardButton("3"))
    bot.send_message(message.chat.id, "Загадал число, угадай.", reply_markup=markup)

wikipedia.set_lang("ru")
def get_wiki(word):
    try:
        w = wikipedia.page(word)
        wikitext = w.content[:1000]
        wikimas = wikitext.split(".")
        wikimas = wikimas[:-1] # Убирает последний элемент из списка

        wiki_result = ""
        for i in wikimas:
            if not ("==" in i):
                wiki_result = wiki_result + i + "."
            else:
                break

        wiki_result = re.sub('\([^()]*\)', '', wiki_result)

        return wiki_result
    except Exception as error:
        return f"Ничего не нашел {error}"

print(get_wiki("Москва"))

bot.infinity_polling() # контролирует когда приходят боту сообщения и позволяет раб.
# коду