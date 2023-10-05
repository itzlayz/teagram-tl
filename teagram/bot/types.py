import inspect
from types import FunctionType
from typing import Union

from aiogram.types import CallbackQuery, InlineQuery, Message
from telethon import TelegramClient

from .. import database, types

class Item:
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
        if (custom_filters := getattr(func, "_filters", None)):
            coro = custom_filters(module, update_type)
            if inspect.iscoroutine(coro):
                coro = await coro

            if not coro:
                return False
        elif update_type.from_user.id != self._manager.me.id:
            return False

        return True
