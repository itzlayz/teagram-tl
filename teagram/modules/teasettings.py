#                            ██╗████████╗███████╗██╗░░░░░░█████╗░██╗░░░██╗███████╗
#                            ██║╚══██╔══╝╚════██║██║░░░░░██╔══██╗╚██╗░██╔╝╚════██║
#                            ██║░░░██║░░░░░███╔═╝██║░░░░░███████║░╚████╔╝░░░███╔═╝
#                            ██║░░░██║░░░██╔══╝░░██║░░░░░██╔══██║░░╚██╔╝░░██╔══╝░░
#                            ██║░░░██║░░░███████╗███████╗██║░░██║░░░██║░░░███████╗
#                            ╚═╝░░░╚═╝░░░╚══════╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚══════╝
#                                            https://t.me/itzlayz
#
#                                    🔒 Licensed under the СС-by-NC
#                                 https://creativecommons.org/licenses/by-nc/4.0/

import time
import io
import os

import logging
import asyncio

from logging import _nameToLevel, _levelToName
from datetime import timedelta
from telethon import types, TelegramClient

from .. import loader, utils
from ..logger import TeagramLogs

log = logging.getLogger()


class TestException(Exception):
    pass


@loader.module(name="Settings", author="teagram")
class SettingsMod(loader.Module):
    """Настройки юзер бота
    Userbot's settings"""

    strings = {"name": "settings"}
    levels = "\n".join(
        f"<code>{k}</code>: <code>{v}</code>" for k, v in _nameToLevel.items()
    )

    async def on_load(self):
        self._logger = None
        for handler in log.handlers:
            if isinstance(handler, TeagramLogs):
                self._logger = handler
                break

        if not self._logger:
            logging.error("Teagram logging handler not found")

    async def logs_cmd(self, message: types.Message, args: str):
        """Отправляет логи. Использование: logs <уровень>"""
        try:
            args = int(args)
        except Exception:
            args = args.strip().upper()

        if not args or (
            (args < 0 or args > 50)
            if isinstance(args, int)
            else (_nameToLevel.get(args, "") and _levelToName.get(args, ""))
        ):
            return await utils.answer(message, self.strings["no_logs"] + self.levels)

        lvl = args
        if isinstance(lvl, str):
            lvl = _nameToLevel.get(lvl)

        if not self._logger.dumps(lvl):
            return await utils.answer(
                message, self.strings["no_logs_at_lvl"].format(lvl=lvl)
            )

        logs = "\n".join(self._logger.dumps(lvl)).encode("utf-8")

        if not logs:
            return await utils.answer(
                message,
                self.strings["no_lvl"].format(lvl=lvl, name=logging.getLevelName(lvl))
                + self.levels,
            )

        logs = io.BytesIO(logs)
        logs.name = "teagram.log"

        return await utils.answer(
            message,
            logs,
            document=True,
            caption=self.strings["logs"].format(
                lvl=lvl, name=logging.getLevelName(lvl)
            ),
        )

    @loader.command()
    async def clearlogs(self, message: types.Message):
        if not getattr(self, "_logger", ""):
            self._logger = log.handlers[0]

        self._logger.flush()
        self._logger.logs = {
            "INFO": [],
            "WARNING": [],
            "ERROR": [],
            "CRITICAL": [],
            "DEBUG": [],
            "NOTSET": [],
        }

        await utils.answer(message, self.strings["flushed"])

    @loader.command()
    async def error(self, message):
        raise TestException("Test exception")

    @loader.command()
    async def setprefix(self, message: types.Message, args: str):
        """Изменить префикс, можно несколько штук разделённые пробелом. Использование: setprefix <префикс> [префикс, ...]"""
        args = args.split()
        if not args:
            return await utils.answer(message, self.strings["wprefix"])

        self.db.set("teagram.loader", "prefixes", list(set(args)))
        prefixes = ", ".join(f"<code>{prefix}</code>" for prefix in args)
        await utils.answer(message, self.strings["prefix"].format(prefixes=prefixes))

    @loader.command()
    async def setlang(self, message: types.Message, args: str):
        """Изменить язык. Использование: setlang <язык>"""
        args = args.split()

        languages = list(
            map(lambda x: x.replace(".yml", ""), os.listdir("teagram/langpacks"))
        )
        langs = f" (<code>{', '.join(languages)}</code>)"

        if not args:
            return await utils.answer(message, self.strings["wlang"] + langs)

        language = args[0]

        if language not in languages:
            langs = " ".join(languages)
            return await utils.answer(
                message, self.strings["elang"].format(langs=langs)
            )

        self.db.set("teagram.loader", "lang", language)
        self.manager.translator.load_translation()

        return await utils.answer(
            message, self.strings["lang"].format(language=language)
        )

    @loader.command()
    async def addalias(self, message: types.Message, args: str):
        """Добавить алиас. Использование: addalias <новый алиас> <команда>"""
        args = args.lower().split(maxsplit=1)
        if not args:
            return await utils.answer(message, self.strings["walias"])

        if len(args) != 2:
            return await utils.answer(message, self.strings["ealias"])

        aliases = self.manager.aliases
        if args[0] in aliases:
            return await utils.answer(message, self.strings["nalias"])

        if not self.manager.command_handlers.get(args[1]):
            return await utils.answer(message, self.strings["calias"])

        aliases[args[0]] = args[1]
        self.db.set("teagram.loader", "aliases", aliases)

        return await utils.answer(
            message, self.strings["alias"].format(alias=args[0], cmd=args[1])
        )

    @loader.command()
    async def delalias(self, message: types.Message, args: str):
        """Удалить алиас. Использование: delalias <алиас>"""
        args = args.split()
        if not args:
            return await utils.answer(message, self.strings["dwalias"])

        aliases = self.manager.aliases
        if args not in aliases:
            return await utils.answer(message, self.strings["dealias"])

        del aliases[args]
        self.db.set("teagram.loader", "aliases", aliases)

        return await utils.answer(message, self.strings["dalias"].format(args))

    @loader.command()
    async def aliases(self, message: types.Message):
        """Показать все алиасы"""
        if aliases := self.manager.aliases:
            return await utils.answer(
                message,
                self.strings["allalias"]
                + "\n".join(
                    f"• <code>{alias}</code> ➜ {command}"
                    for alias, command in aliases.items()
                ),
            )
        else:
            return await utils.answer(message, self.strings["noalias"])

    @loader.command()
    async def ping(self, message: types.Message):
        """🍵 команда для просмотра пинга."""
        start = time.perf_counter_ns()
        client: TelegramClient = message._client
        msg = await client.send_message(
            utils.get_chat(message), "☕", reply_to=utils.get_topic(message)
        )

        ping = round((time.perf_counter_ns() - start) / 10**6, 3)
        uptime = timedelta(seconds=round(time.time() - utils._init_time))

        await utils.answer(
            message,
            f"🕒 {self.strings['ping']}: <code>{ping}ms</code>\n"
            f"❔ {self.strings['uptime']}: <code>{uptime}</code>",
        )

        await msg.delete()

    @loader.command()
    async def addowner(self, message: types.Message):
        reply = await message.message.get_reply_message()
        if not reply:
            return await utils.answer(message, self.strings["noreply"])

        if reply.sender_id == (_id := (await self.client.get_me()).id):
            return await utils.answer(message, self.strings["yourself"])

        if message.message.sender_id != _id:
            return await utils.answer(message, self.strings["owner"])

        user = reply.sender_id
        users = self.db.get("teagram.loader", "users", [])
        self.db.set("teagram.loader", "users", users + [user])

        await utils.answer(message, self.strings["adduser"])

    @loader.command()
    async def rmowner(self, message: types.Message):
        reply = await message.message.get_reply_message()
        if not reply:
            return await utils.answer(message, self.strings["noreply"])

        if reply.sender_id == (_id := (await self.client.get_me()).id):
            return await utils.answer(message, self.strings["yourself"])

        if message.message.sender_id != _id:
            return await utils.answer(message, self.strings["owner"])

        user = reply.sender_id
        users = self.db.get("teagram.loader", "users", [])
        self.db.set("teagram.loader", "users", list(filter(lambda x: x != user, users)))

        await utils.answer(message, self.strings["deluser"])

    @loader.command()
    async def users(self, message: types.Message):
        _users = self.db.get("teagram.loader", "users", [])
        await utils.answer(
            message,
            (
                (
                    f'➡ {self.strings["user"]} <code>'
                    + ", ".join(str(user) for user in _users)
                    + "</code>"
                )
                if _users
                else self.strings["nouser"]
            ),
        )

    @loader.command(alias="ch_token")
    async def inlinetoken(self, message: types.Message):
        self.db.set("teagram.bot", "token", None)
        await utils.answer(
            message, self.strings["chbot"].format(f"{self.prefix}restart")
        )

    @loader.command(alias="ch_name")
    async def inlinename(self, message, args: str = None):
        if not args:
            return await utils.answer(message, self.strings("noargs"))

        async with self.client.conversation("@BotFather") as conv:
            await conv.send_message("/setname")
            await conv.send_message(f"@{self.inline.bot_username}")
            await conv.send_message(args)

            await conv.mark_read()

        self.inline.bot_username = args
        await utils.answer(
            message,
            self.strings("iname_ch").format(last=self.inline.bot_username, cur=args),
        )

    @loader.command(alias="ch_inline_bot")
    async def inlinebot(self, message, args: str):
        if not args:
            return await utils.answer(message, self.strings("noargs"))

        if not args.startswith("@") or not args.lower().endswith("bot"):
            return await utils.answer(
                message,
                self.strings("invalid_bot"),
            )

        async with self.client.conversation("@BotFather") as conv:
            await conv.send_message("/mybots")
            response = await conv.get_response()

            if not response.reply_markup:
                return await utils.answer(
                    message,
                    self.strings("unexpected_error").format(response.text),
                )

            for row in response.reply_markup.rows:
                for button in row.buttons:
                    if button.text == args:
                        break
            else:
                await conv.send_message("/token")
                await asyncio.sleep(1)

                await conv.send_message(args)
                await asyncio.sleep(1)

                from re import search

                response = await conv.get_response()

                token = search(r"\d{1,}:[0-9a-zA-Z_-]{35}", response.text)
                if not token:
                    return await utils.answer(
                        message,
                        self.strings("unexpected_error").format(response.text),
                    )
                else:
                    token = token.group(0)

                self.db.set("teagram.bot", "token", token.strip())
                await utils.answer(message, self.strings("ibot_ch"))

                return

        await utils.answer(message, "wth")
