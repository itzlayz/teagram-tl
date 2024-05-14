import logging
import inspect

from types import FunctionType
from typing import Union

from aiogram import types as aiotypes
from aiogram.types import CallbackQuery, InlineQuery, Message, InlineKeyboardMarkup
from telethon import TelegramClient

from .. import database, types
from .utils import Utils
from .list import List

logger = logging.getLogger()


class Item(Utils, List):
    """
    Base class for items.
    This class provides functionality for checking filters applied to event handlers.
    """

    def __init__(self) -> None:
        """
        Initialize the class.
        """
        self._manager: types.ModulesManager = None
        self._db: database.Database = None
        self._app: TelegramClient = None

    async def _check_filters(
        self,
        func: FunctionType,
        module: types.Module,
        update_type: Union[Message, InlineQuery, CallbackQuery],
    ) -> bool:
        """
        Check filters for an event handler.

        Args:
            func (FunctionType): The event handler function.
            module (types.Module): The module the function belongs to.
            update_type (Union[Message, InlineQuery, CallbackQuery]): The type of update.

        Returns:
            bool: True if the event should be processed, False otherwise.
        """
        if custom_filters := getattr(func, "_filters", None) and module:
            coro = custom_filters(module, update_type)
            if inspect.iscoroutine(coro):
                coro = await coro

            if not coro:
                return False
        elif (
            update_type.from_user.id != self._manager.me.id
            and update_type.from_user.id
            not in self._db.get("teagram.loader", "users", [])
        ):
            if not getattr(func, "inline_everyone", None):
                return False

        return True


class InlineCall(CallbackQuery):
    def __init__(
        self, call: CallbackQuery, manager: "types.bot.BotManager", message=None
    ):
        if message:
            call.message = message

        CallbackQuery.__init__(self)
        self.inline_message_id = None
        self.callback_query = call

        self._bot = manager.bot
        self._client = manager._app

        self.chat = getattr(call.message, "chat", None)
        self.chat_id = getattr(self.chat, "id", None)

        for orig in (
            "id",
            "from_user",
            "message",
            "inline_message_id",
            "chat_instance",
            "data",
        ):
            setattr(self, orig, getattr(call, orig, None))

    async def edit(
        self,
        text: str = None,
        reply_markup: InlineKeyboardMarkup = None,
        photo: str = None,
        gif: str = None,
        file=None,
        spoiler: bool = False,
        inline_message_id: str = None,
    ):
        if not text and not (photo or gif or file):
            logger.warning("InlineCall needs `text` or `media` for edit")
            return

        media = None
        if file or photo or gif:
            from io import BytesIO

            if isinstance(file, BytesIO):
                media = aiotypes.InputMediaDocument(file, caption=text)

            try:
                if photo:
                    media = aiotypes.InputMediaPhoto(
                        photo, text, parse_mode="html", has_spoiler=spoiler
                    )
                if gif:
                    media = aiotypes.InputMediaAnimation(
                        photo, caption=text, parse_mode="html", has_spoiler=spoiler
                    )
            except Exception:
                logger.exception("Can't delete inline call")
                return

        if media:
            return await self._bot.edit_message_media(
                media,
                inline_message_id=inline_message_id or self.inline_message_id,
                reply_markup=reply_markup,
            )
        try:
            return await self._bot.edit_message_text(
                text,
                inline_message_id=inline_message_id or self.inline_message_id,
                reply_markup=reply_markup,
            )
        except Exception:
            logger.exception("Can't edit inline call")

    async def delete(
        self, call: CallbackQuery = None, chat_id: int = None, message_id: int = None
    ):
        try:
            chat_id = getattr(self.message.chat, "id", chat_id)
            message_id = getattr(self.message, "message_id", message_id)

            if chat_id and message_id:
                return await self._bot.delete_message(
                    chat_id=chat_id, message_id=message_id
                )

            return False
        except Exception:
            logger.exception("Can't delete inline call")


class InlineMessage:
    pass
