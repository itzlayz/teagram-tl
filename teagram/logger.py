import logging
import asyncio

from typing import List
from . import utils

EMOJIS = {
    "NOTSET": "🤷 <b>NOTSET</b>",
    "DEBUG": "🐞 <b>DEBUG</b>",
    "INFO": "❔ <b>INFO</b>",
    "WARNING": "⚠️ <b>WARNING</b>",
    "ERROR": "🚨 <b>ERROR</b>",
    "CRITICAL": "💥 <b>CRITICAL</b>",
}


class TeagramLogs(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        self.buffer = []

        super().__init__(*args, **kwargs)

    @property
    def logs(self):
        """Formatted logs"""
        return [self.format(record) for record in self.dump()]

    @logs.setter
    def logs(self, logs):
        self.logs = logs

    def dump(self):
        """Non-formatted logs"""
        return self.buffer

    def dumps(self, lvl: int = 0) -> List[logging.LogRecord]:
        """Logs with ... level"""
        return [self.format(record) for record in self.dump() if record.levelno >= lvl]

    def emit(self, record: logging.LogRecord):
        self.buffer.append(record)
        super().emit(record)

        with utils.supress(Exception):
            task = asyncio.ensure_future(self.logchat(record))
            utils.disable_task_error(task)

    async def logchat(self, record: logging.LogRecord, info=False):
        """
        :param record: logRecord
        :param info: Pass info (bool)
        """
        if record.levelname == "INFO" and not info:
            return

        if getattr(self, "client", None):
            await self.client.inline_bot.send_message(
                await self.client.logchat,
                f"{EMOJIS[record.levelname]}:\n" f"<code>{self.format(record)}</code>",
                parse_mode="html",
            )


def init_logging():
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    handler = TeagramLogs()
    handler.setLevel(logging.INFO)
    handler.setFormatter(fmt)

    filehandler = logging.FileHandler(
        filename="teagram.log", mode="w", encoding="utf-8"
    )
    filehandler.setFormatter(fmt)

    log = logging.getLogger()
    log.addHandler(handler)
    log.addHandler(filehandler)
    log.setLevel(logging.DEBUG)

    logging.getLogger("git").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
