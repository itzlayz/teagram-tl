import logging
import asyncio
import sys
import traceback
import typing

from aiogram import Bot, Dispatcher, exceptions
from aiogram.types import (
    InlineKeyboardMarkup
)

from telethon.types import Message, Photo, Document
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import StartBotRequest
from telethon.tl.functions.contacts import UnblockRequest

from typing import Union, NoReturn

from .events import Events
from .token_manager import TokenManager

from .. import database, __version__, types, utils

logger = logging.getLogger()

class BotManager(Events, TokenManager):
    """
    Bot Manager class.
    Manages the bot's functionalities.
    """

    def __init__(self, app: TelegramClient, db: database.Database, manager: types.ModulesManager) -> None:
        """
        Initialize the Bot Manager.

        Parameters:
            app (TelegramClient): The client instance.
            db (database.Database): The database instance.
            manager (types.ModulesManager): The modules manager.
        """
        self._app = app
        self._db = db
        self._manager = manager

        self._token = self._db.get("teagram.bot", "token", None)
        self.callback_units = {}
        self.input_handlers = {}
        self._units = {}
        self.cfg = {}

    async def load(self) -> Union[bool, NoReturn]:
        """
        Load the bot manager.

        Returns:
            Union[bool, NoReturn]: True if loaded successfully, else exits with an error.
        """
        error_text = "The userbot requires a bot. Resolve the bot creation issue and restart the userbot."

        new = False
        revoke = False

        if not self._token:
            self._token = await self._revoke_token()
            new = True
            revoke = True

        if not self._token:
            new = True


            self._token = await self._create_bot()
        if not self._token:
            logger.error(error_text)
            sys.exit(1)

        try:
            self.bot = Bot(self._token, parse_mode="html")
        except (exceptions.ValidationError, exceptions.Unauthorized):
            logger.error("Invalid token. Attempting to recreate the token.")

            result = await self._revoke_token()
            new = True
            revoke = True

            if not result:
                self._token = await self._create_bot() or logger.error(error_text) or sys.exit(1)
            else:
                self._token = result

        if new:
            name = (await self.bot.get_me()).username
            await self._app(StartBotRequest(name, name, 'start'))

            if revoke:
                async with self._app.conversation("@BotFather") as conv:
                    try:
                        await conv.send_message("/cancel")
                    except errors.UserIsBlockedError:
                        await self._app(UnblockRequest('@BotFather'))

                    await conv.send_message("/setuserpic")
                    await conv.get_response()

                    await conv.send_message(f"@{name}")
                    await conv.get_response()

                    await conv.send_file("assets/teagram_bot.png")
                    await conv.get_response()

                    for message in [
                        "/setinline",
                        f"@{name}",
                        "teagram-command",
                        "/setinlinefeedback",
                        f"@{name}",
                        "Enabled"
                    ]:
                        await conv.send_message(message)
                        await conv.get_response()

                        await asyncio.sleep(1)

                    logger.info("Bot revoked successfully")

        self.me = await self.bot.get_me()
        self.bot_id = self.me.id

        self._db.set('teagram.bot', 'token', self._token)
        self._dp = Dispatcher(self.bot)
        self._register_handlers()

        asyncio.ensure_future(self._dp.start_polling())

        self.bot.manager = self
        return True

    def _register_handlers(self) -> None:
        """
        Register event handlers.
        """
        self._dp.register_message_handler(self._message_handler, lambda _: True, content_types=["any"])
        self._dp.register_inline_handler(self._inline_handler, lambda _: True)
        self._dp.register_callback_query_handler(self._callback_handler, lambda _: True)
        self._dp.register_chosen_inline_handler(self._chosen_inline_handler, lambda _: True)

    #     hikka compatibility
    async def invoke_unit(self, inline_id: str, message: Message) -> Message:
        return await utils.invoke_inline(
            message,
            self.me.username,
            inline_id
        )
    
    async def form(
        self,
        *,
        text: str = 'Teagram',
        message: Message, 
        reply_markup: Union[InlineKeyboardMarkup, list, None] = None,
        callback: typing.Any = None,
        gif: typing.Any = None,
        photo: Photo = None,
        doc: Document = None,
        **kwargs
    ):
        unit_id = callback or utils.random_id()
        self._units[unit_id] = {
            'type': 'form',
            'title': 'Teagram',
            'description': "Teagram's form",
            'text': text,
            'keyboard': reply_markup,
            'reply_markup': reply_markup,
            'callback': callback,
            'message': message,
            'photo': photo,
            'doc': doc,
            'gif': gif,
            'top_msg_id': (
                (message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id) 
                if (message.reply_to if message else None) else None
            ),
            **kwargs
        }

        try:
            await self.invoke_unit(unit_id, message)
        except Exception as error:
            del self._units[unit_id]

            error = "\n".join(traceback.format_exc().splitlines()[1:])

            await utils.answer(
                message,
                f"❌ <code>{error}</code>"
            )   

        return unit_id