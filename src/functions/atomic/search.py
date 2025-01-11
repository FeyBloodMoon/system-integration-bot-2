"""Example of implementation of atomic function"""


from typing import List
import sys
import telebot
from telebot import types
from telebot.callback_data import CallbackData
from bot_func_abc import AtomicBotFunctionABC
sys.path.append('/path/to/src')

class AnotherBotFunction(AtomicBotFunctionABC):
    """Example of implementation of atomic function"""
    commands: List[str] = ["another_unique_command"]

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
        """Регистрация всех обработчиков."""
        self.bot = bot

        # Регистрация обработчиков
        self.register_start_handler()
        self.register_category_handler()
        self.register_tag_handler()
        self.register_qr_handler()

    def register_start_handler(self):
        """Регистрируем обработчик команды /start."""
        @self.bot.message_handler(commands=["start"])
        def send_categories(message):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Versatile",
                                                    callback_data="category_versatile"))
            keyboard.add(types.InlineKeyboardButton(text="NSFW", callback_data="category_nsfw"))
            keyboard.add(types.InlineKeyboardButton(text="QR", callback_data="category_qr"))
            self.chat_messages[message.chat.id] = {"previous_category": None}
            self.bot.send_message(chat_id=message.chat.id,
                                  text="Выберите категорию:", reply_markup=keyboard)

    def register_category_handler(self):
        """Регистрируем обработчик выбора категории."""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
        def send_tags_by_category(call):
            category = call.data.split("_")[1]
            self.chat_messages[call.message.chat.id]["previous_category"] = category
            keyboard = types.InlineKeyboardMarkup()

            if category == "versatile":
                self.add_tags_to_keyboard(keyboard, ["maid", "waifu", "marin-kitagawa"])
                self.bot.send_message(chat_id=call.message.chat.id,
                                      text="Выберите тег из Versatile:", reply_markup=keyboard)
            elif category == "nsfw":
                self.add_tags_to_keyboard(keyboard, ["ass", "hentai", "milf"])
                self.bot.send_message(chat_id=call.message.chat.id,
                                      text="Выберите тег из NSFW:", reply_markup=keyboard)
            elif category == "qr":
                self.send_qr_image(call.message.chat.id)

    def register_tag_handler(self):
        """Регистрируем обработчик выбора тега."""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("tag_"))
        def fetch_images(call):
            selected_tag = call.data.split("_")[1]
            self.ask_image_count(call.message.chat.id, selected_tag)

    def add_tags_to_keyboard(self, keyboard, tags: List[str]):
        """Добавляем теги в клавиатуру."""
        for tag in tags:
            keyboard.add(types.InlineKeyboardButton(text=tag, callback_data=f"tag_{tag}"))
        keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="start"))

    def start_keyboard(self):
        """Клавиатура для возврата к началу."""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="start"))
        return keyboard

    def wiggle(self):
        """Функция для вывода версии Python."""
        print(f"{self.name} wiggle around wormily.")
