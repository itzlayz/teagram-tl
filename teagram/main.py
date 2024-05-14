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

from . import auth, database, loader, web, utils, __version__

from telethon.tl.functions.channels import InviteToChannelRequest, EditAdminRequest
from telethon.tl.functions.messages import StartBotRequest
from telethon.types import ChatAdminRights

from aiogram import Bot

import os
import sys
import time
import logging

logger = logging.getLogger()

teagram = sys.modules["teagram"]
sys.modules["teagram.inline"] = teagram.bot


class Main:
    def __init__(self, args) -> None:
        self.db = database.db
        self.args = args

    async def on_start(self, bot: Bot, db: database.Database, prefix: str, app):
        try:
            await bot.send_message(
                db.cloud.input_chat,
                "☕ <b>Teagram userbot has started!</b>\n"
                f"🤖 <b>Version: {__version__}</b>\n"
                f"❔ <b>Prefix: {prefix}</b>",
            )

            try:
                with open("teagram.log", "r") as log:
                    log = log.read()

                    await bot.send_message(
                        db.cloud.input_chat, f"📁 <b>Logs</b>\n<code>{log}</code>"
                    )
            except Exception:
                pass

            return
        except Exception:
            me = dict(await bot.get_me())
            _id = me["id"]

            admin = ChatAdminRights(
                post_messages=True,
                ban_users=True,
                edit_messages=True,
                delete_messages=True,
            )

        username = me["username"]

        await app(StartBotRequest(username, username, "start"))
        await app(InviteToChannelRequest(db.cloud.input_chat, [_id]))
        await app(EditAdminRequest(db.cloud.input_chat, _id, admin, "Teagram"))

    async def main(self):
        try:
            if os.geteuid() == 0 and "docker" not in utils.get_platform().lower():
                self.log.warning("Please do not use root for userbot")
        except Exception:
            pass

        app = auth.Auth(manual=False).app
        await app.connect()

        if not getattr(self.args, "disable_web", "") and not await app.get_me():
            import socket

            port = getattr(self.args, "port", None)

            def check_port(port: int):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(("localhost", port))

            if port:
                try:
                    check_port(port)
                except OSError as e:
                    if e.errno == 98:
                        logger.error("Port is busy, generating new one")
                        port = None
            else:
                from random import randint

                port = randint(1000, 65535)
                if "windows" not in utils.get_platform().lower():
                    while True:
                        port = randint(1000, 65535)
                        try:
                            check_port(port)

                            break
                        except OSError as e:
                            if e.errno == 98:
                                continue

            web_config = web.Web(port)
            await web_config.server.serve()

            return

        await app.disconnect()

        device = getattr(self.args, "rnd_session", False)

        me, app = await auth.Auth(random_device=device).authorize()
        self.db.init_cloud(app, me)
        await self.db.cloud.get_chat()

        app.logchat = self.db.cloud.input_chat
        logging.getLogger().handlers[0].client = app

        modules = loader.ModulesManager(app, self.db, me)
        bot: Bot = await modules.load(app)

        self.modules = modules

        prefix = self.db.get("teagram.loader", "prefixes", ["."])[0]
        restart = self.db.get("teagram.loader", "restart")

        if not restart:
            print(
                """
▀▀█▀▀  █▀▀▀  █▀▀█  █▀▀█  █▀▀█  █▀▀█  █▀▄▀█ 
  █    █▀▀▀  █▄▄█  █ ▄▄  █▄▄▀  █▄▄█  █ █ █ 
  █    █▄▄▄  █  █  █▄▄█  █  █  █  █  █   █
            """
            )
            logger.info(f'Userbot has started! Prefix "{prefix}"')

        if restart:
            restarted = round(time.time()) - int(restart["start"])
            ru = (
                f"<b>✅ Перезагрузка прошла успешно! ({restarted} сек.)</b>"
                if restart["type"] == "restart"
                else f"<b>✅ Обновление прошло успешно! ({restarted} сек.)</b>"
            )
            en = (
                f"<b>✅ Reboot was successful! ({restarted} seconds.)</b>"
                if restart["type"] == "restart"
                else f"<b>✅ The update was successful! ({restarted} seconds.)</b>"
            )

            lang = self.db.get("teagram.loader", "lang", "")
            # if there was no lang in db
            if not lang:
                lang = "en"
                self.db.set("teagram.loader", "lang", "en")

            restarted_text = ru if lang == "ru" else en

            try:
                _id = list(map(int, restart["msg"].split(":")))
                msg = await app.get_messages(_id[0], ids=_id[1])

                if msg and msg.text != (restarted_text):
                    await app.edit_message(
                        _id[0], _id[1], restarted_text, parse_mode="html"
                    )
            except Exception:
                await self.on_start(bot, self.db, prefix, app)

            self.db.pop("teagram.loader", "restart")
        else:
            await self.on_start(bot, self.db, prefix, app)

        await app.run_until_disconnected()
