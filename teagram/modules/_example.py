from asyncio import sleep

from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, InlineQuery,
                            InlineQueryResultArticle, InputTextMessageContent
                            )
from telethon import types

from .. import (  # ".." - т.к. модули находятся в папке teagram/modules, то нам нужно на уровень выше
    loader, utils, validators)
from ..types import Config, ConfigValue


# Можно добавить зависимости
# required: Сюда пишите ваши зависимости через пробел

#                 Обязательно   Необязательно   Необязательно
#                  Название        Автор          Версия
@loader.module(name="Example", author="teagram", version=1) 
class ExampleMod(loader.Module):  # Example - название класса модуля
                                  # Mod в конце названия обязательно
    """Описание модуля"""

    def __init__(self):
        self.config = Config(
            ConfigValue(
                'Это тестовый атрибут',        # Название атрибута
                'Дефолтное значение атрибута', # Дефолтное значение
                'Значение атрибута',           # Можно подгрузить из базы данных
                validators.String(),           # Тип значения
                'Это описание'                 # Докстринг/Описание
            )
        )

    async def on_load(self):
        """Вызывается когда модуль загружен"""
        # Сюда можно написать какой нибудь скрипт, например подключение к бд и т.д.
        # Атрибуты: self.db      - база данных
        #           self.manager - менеджер модулей 
        #           self.client  - телеграм клиент
        #           self.bot     - инлайн бот
        # Их можно использовать в любой части кода (В пределах класса)

        # Запустим цикл ниже
        # Это можно делать в команде, например для того чтобы использовать get_me
        self.testloop.start(testarg='Тестовый аргумент')


    # interval - интервал в секундах
    # autostart - True/False (по умолчанию True)
    @loader.loop(5, autostart=False)
    async def testloop(self, testarg): # Цикл должен заканчиваться на loop
        """
        Чтобы задать аргументы циклу, посмотрите на 46 строку       
        """
        print(testarg)

    # _inline_handler на конце функции чтобы обозначить что это инлайн-команда
    # args - аргументы после команды. необязательный аргумент
    async def example_inline_handler(self, inline_query: InlineQuery, args: str):  
        """
        Пример инлайн-команды. Использование: @bot example [аргументы]
        Если вы хотите использовать команду в коде то надо использовать метод, invoke_inline.
        Пример ниже
        """
        await self.new_method(inline_query, args)

    async def new_method(self, inline_query, args):
        await inline_query.answer(
            [
                InlineQueryResultArticle(
                    id=utils.random_id(),
                    title="Тайтл",
                    description="Нажми на меня!" + (
                        f" Аргументы: {args}" if args
                        else ""
                    ),
                    input_message_content=InputTextMessageContent(
                        "Текст после нажатия на кнопку"),
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Текст кнопки", callback_data="example_button_callback"))
                )
            ]
        )
        
    # Сработает только если каллбек дата равняется "example_button_callback"
    # _callback_handler на конце функции чтобы обозначить что это каллбек-хендлер
    @loader.on_bot(lambda self, call: call.data == "example_button_callback")  
    async def example_callback_handler(self, call: CallbackQuery):  
        """Пример каллбека"""
        await call.answer(
            "Ого пример каллбека", show_alert=True)

    # Можно сделать команду без окончания _cmd/cmd
    @loader.command()
    async def example(self, message: types.Message, args: str):
        # args это аргументы команды
        # .example [аргументы]
        await utils.answer(message, ('Это пример команды' + (args or "")))

    # Можно сделать команду с помощью окончания _cmd/cmd
    async def example_cmd(self, message: types.Message):
        await utils.answer(message, 'Это команда которая не использует декоратор')

    # Так же есть вотчеры
    # Их можно создавать до бесконечности, но нужно делать приписку "watcher"
    async def watcher(self, message: types.Message):
        await utils.answer(message, 'Это вотчер теаграма')

        # Тут мы используем инлайн команду нашего бота
        await self.bot.invoke_inline(
            message,
            'example'
        )