import os
import logging
import requests
import telebot
from io import BytesIO
from typing import List
from telebot import types
from bot_func_abc import AtomicBotFunctionABC
from telebot.callback_data import CallbackData

class AtomicExampleBotFunction(AtomicBotFunctionABC):
    """Example of implementation of atomic function"""

    commands: List[str] = ["unique_search", "example_command"]
    authors: List[str] = ["FeyBM"]
    about: str = "Пример функции бота!"
    description: str = """В поле  *description* поместите подробную информацию о работе функции.
    Описание способов использования, логики работы. Примеры вызова функции - /unique_search 
    Возможные параметры функции /example_command """
    state: bool = True

    bot: telebot.TeleBot
    example_keyboard_factory: CallbackData

    def __init__(self):
        super().__init__()
        self.chat_messages = {} 
        self.sent_images = {}    

    def set_handlers(self, bot: telebot.TeleBot):
        self.bot = bot
        self.example_keyboard_factory = CallbackData('t_key_button', prefix=self.commands[0])

        versatile_tags = ["maid", "waifu", "marin-kitagawa", "mori-calliope", "raiden-shogun", "oppai", "selfies", "uniform", "kamisato-ayaka"]
        nsfw_tags = ["ass", "hentai", "milf", "oral", "paizuri", "ecchi", "ero"]

        user_data = {}
        
        @bot.message_handler(commands=["start"])
        def send_categories(message):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Versatile", callback_data="category_versatile"))
            keyboard.add(types.InlineKeyboardButton(text="NSFW", callback_data="category_nsfw"))
            keyboard.add(types.InlineKeyboardButton(text="QR", callback_data="category_qr"))
            user_data[message.chat.id] = {"previous_category": None}
            bot.send_message(chat_id=message.chat.id, text="Выберите категорию:", reply_markup=keyboard)

        @bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
        def send_tags_by_category(call):
            category = call.data.split("_")[1]
            user_data[call.message.chat.id]["previous_category"] = category
            keyboard = types.InlineKeyboardMarkup()

            if category == "versatile":
                for tag in versatile_tags:
                    keyboard.add(types.InlineKeyboardButton(text=tag, callback_data=f"tag_{tag}"))
                keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="start"))
                bot.send_message(chat_id=call.message.chat.id, text="Выберите тег из Versatile:", reply_markup=keyboard)
            elif category == "nsfw":
                for tag in nsfw_tags:
                    keyboard.add(types.InlineKeyboardButton(text=tag, callback_data=f"tag_{tag}"))
                keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="start"))
                bot.send_message(chat_id=call.message.chat.id, text="Выберите тег из NSFW:", reply_markup=keyboard)
            elif category == "qr":
                send_qr_image(call.message.chat.id)

        def send_qr_image(chat_id):
            try:
                file_path = os.path.join(os.path.dirname(__file__), 'assets', 'qr_code.png')

                with open(file_path, 'rb') as image_file:
                    bot.send_photo(chat_id=chat_id, photo=image_file)
                bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=start_keyboard())
            except Exception as e:
                bot.send_message(chat_id=chat_id, text=f"Произошла ошибка при отправке QR-кода: {e}")

        def start_keyboard():
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="start"))
            return keyboard

        @bot.callback_query_handler(func=lambda call: call.data.startswith("tag_")) 
        def fetch_images(call):
            selected_tag = call.data.split("_")[1]

            def ask_image_count():
                msg = bot.send_message(chat_id=call.message.chat.id, text="Сколько изображений вы хотите получить? (от 1 до 10)")
                bot.register_next_step_handler(msg, process_image_count)

            def process_image_count(message):
                try:
                    count = int(message.text)
                    if count < 1 or count > 10:
                        bot.send_message(chat_id=message.chat.id, text="Введите число от 1 до 10.")
                        ask_image_count()
                    else:
                        send_images(count)
                except ValueError:
                    bot.send_message(chat_id=message.chat.id, text="Введите корректное число.")
                    ask_image_count()

            def send_images(count):
                bot.send_message(chat_id=call.message.chat.id, text=f"Получение {count} изображений для тега: {selected_tag}...")
                try:
                    if count == 1:
                        url = f"https://api.waifu.im/search/?included_tags={selected_tag}"
                    else:
                        url = f"https://api.waifu.im/search/?included_tags={selected_tag}&many=true&limit={count}"

                    response = requests.get(url)

                    if response.status_code == 200:
                        data = response.json()

                        if data.get('images'):
                            sent_urls = self.sent_images.get(call.message.chat.id, set())
                            new_images = []

                            for image_data in data['images'][:count]:
                                image_url = image_data['url']
                                if image_url not in sent_urls:
                                    try:
                                        image_response = requests.get(image_url)
                                        if image_response.status_code == 200:
                                            image_size = len(image_response.content)
                                            image_size = int(image_response.headers.get('content-length', 0))
                                            if image_size == 0:
                                                bot.send_message(chat_id=call.message.chat.id, text="Ошибка: файл пустой.")
                                                continue
                                            image = BytesIO(image_response.content)
                                            image.name = f"{selected_tag}.jpg"
                                            if image_size > 1024 * 1024 * 10:  
                                                bot.send_document(chat_id=call.message.chat.id, document=image)
                                            else:
                                                if image_url.endswith(".gif"):
                                                       bot.send_animation(chat_id=call.message.chat.id, animation=image_url)
                                                else:
                                                    image = BytesIO(image_response.content)
                                                    image.name = f"{selected_tag}.jpg"
                                                    bot.send_photo(chat_id=call.message.chat.id, photo=image)
                                                new_images.append(image_url)
                                        else:
                                            bot.send_message(chat_id=call.message.chat.id, text="Не удалось загрузить файл.")
                                    except Exception as e:
                                        bot.send_message(chat_id=call.message.chat.id, text=f"Ошибка при загрузке изображения: {e}")
                                else:
                                    bot.send_message(chat_id=call.message.chat.id, text="Файл уже был отправлен.")

                            if new_images:
                                if call.message.chat.id not in self.sent_images:
                                    self.sent_images[call.message.chat.id] = set()
                                self.sent_images[call.message.chat.id].update(new_images)

                            show_action_buttons(call.message.chat.id, selected_tag)
                        else:
                            bot.send_message(chat_id=call.message.chat.id, text="Файлы не найдены по этому тегу.")
                    else:
                        bot.send_message(chat_id=call.message.chat.id, text=f"Ошибка запроса. Код ошибки: {response.status_code}")
                except Exception as e:
                    bot.send_message(chat_id=call.message.chat.id, text=f"Произошла ошибка: {e}")

            def show_action_buttons(chat_id, tag):
                previous_category = user_data.get(chat_id, {}).get("previous_category", "versatile")
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton(text="Назад", callback_data=f"category_{previous_category}"),
                    types.InlineKeyboardButton(text="Другая категория", callback_data="start")
                )
                bot.send_message(chat_id=chat_id, text="Что хотите сделать дальше?", reply_markup=keyboard)

            ask_image_count()

        @bot.callback_query_handler(func=lambda call: call.data == "start")
        def handle_start(call):
            send_categories(call.message)
