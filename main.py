import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from cfg import *

questions = {}

bot = telebot.TeleBot(token, parse_mode="HTML")

def ch_id(message: Message) -> int:
    return message.from_user.id

@bot.message_handler(commands=["start"])
def welcome(message: Message):
    first_name = message.from_user.first_name
    username = message.from_user.last_name

    content = first_name if first_name != "None" else username
    bot.send_message(ch_id(message), f"Привет, {content}! Отправка фото, стикеров, видео, всё кроме текста не работает. Удачи!")

def notify_admins(message: Message, author: str):
    for i in ADMIN_ID:
        if i:
            bot.send_message(i, f"Доступен новый вопрос от @{author}")

def send_you_quest(message: Message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    chat_id = ch_id(message)
    text = str(message.text)

    content = first_name if first_name != "None" else username
    questions[chat_id] = {"Info": content, "id": chat_id, "question": text}
    bot.send_message(ch_id(message), "Ваш вопрос отправлен, скоро на него ответит наш админ")
    notify_admins(message, username)

def all_questions(message: Message):
    content = ""

    for key, value in questions.items():
        content += f"Question ID: {key}\n"
        content += f"Info: {value['Info']}\n"
        content += f"Question: {value['question']}\n\n"

    bot.send_message(ch_id(message), content)

@bot.message_handler(commands=["list_questions"])
def list_questions(message: Message):
    id_ = message.from_user.id

    if id_ in ADMIN_ID:
        all_questions(message)

@bot.message_handler(commands=["help"])
def help(message: Message):
    quest = bot.send_message(ch_id(message), "Отправьте свой вопрос, я отправлю его DIFOON'у")
    bot.register_next_step_handler(quest, send_you_quest)

@bot.message_handler(commands=["id"])
def get_id(message: Message):
    bot.send_message(ch_id(message), f"Ваш id: {ch_id(message)}")

@bot.message_handler(commands=["answer"])
def answer_question(message: Message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")
        return

    if not questions:
        bot.send_message(message.chat.id, "Список вопросов пуст.")
        return

    keyboard = InlineKeyboardMarkup()
    for key, value in questions.items():
        keyboard.add(InlineKeyboardButton(value['question'], callback_data=str(key)))

    bot.send_message(ch_id(message), "Выберите вопрос, на который хотите ответить:", reply_markup=keyboard)

def process_answer(message: Message):
    try:
        question_id = int(message.text)
        if question_id not in questions:
            bot.send_message(message.chat.id, "Неверный ID вопроса.")
            return

        bot.send_message(message.chat.id, "Введите ответ на вопрос:")
        bot.register_next_step_handler(message, send_admin_answer, question_id)
    except ValueError:
        bot.send_message(message.chat.id, "ID вопроса должен быть числом.")

def send_admin_answer(message: Message, question_id: int):
    bot.send_message(questions[question_id]["id"], f"Ответ на ваш вопрос:\n{message.text}")
    del questions[question_id]
    bot.send_message(message.chat.id, "Ответ успешно отправлен и вопрос удален.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.id in ADMIN_ID:
        question_id = int(call.data)
        if question_id in questions:
            bot.send_message(call.message.chat.id, f"Выбранный вопрос: {questions[question_id]['question']}")
            bot.send_message(call.message.chat.id, "Введите ответ на вопрос:")
            bot.register_next_step_handler(call.message, send_admin_answer, question_id)
        else:
            bot.send_message(call.message.chat.id, "Вопрос не найден.")
    else:
        bot.send_message(call.message.chat.id, "Вы не являетесь администратором.")

@bot.message_handler(content_types=["text"])
def handle_text_message(message: Message):
    # Вызываем функцию для обработки текстового сообщения
    send_you_quest(message)

@bot.message_handler(func=lambda message: True)
def handle_non_text_message(message: Message):
    # Отправляем сообщение об ошибке
    bot.send_message(ch_id(message), "Ошибка: принимаются только текстовые сообщения.")

bot.infinity_polling()
