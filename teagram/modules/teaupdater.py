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

from .. import loader, utils, validators
from ..types import Config, ConfigValue

import os
import sys
import time
import atexit

from telethon import types
from telethon.tl.functions.messages import (
    UpdateDialogFilterRequest,
    GetDialogFiltersRequest,
)
from subprocess import check_output, run

from aiogram import Bot
from aiogram.utils.exceptions import CantParseEntities, BotBlocked, Unauthorized

no_git = False
try:
    import git
except Exception:
    no_git = True


@loader.module(name="Updater", author="teagram")
class UpdateMod(loader.Module):
    """Get update from github"""

    strings = {"name": "updater"}

    def __init__(self):
        self.config = Config(
            ConfigValue(
                option="sendOnUpdate",
                doc="Оповещать об обновлении",
                default=True,
                value=self.get("sendOnUpdate"),
                validator=validators.Boolean(),
            )
        )

    async def folder(self):
        folders = await self.client(GetDialogFiltersRequest())
        for folder in folders:
            if getattr(folder, "title", "") == "Teagram":
                return

        if len(folders) == 1 and not getattr(folders[0], "id", ""):
            folder_id = 2
        else:
            try:
                folder_id = (
                    max(
                        folders,
                        key=lambda x: x.id,
                    ).id
                    + 1
                )
            except Exception:
                folder_id = 2

        peers = []

        async for dialog in self.client.iter_dialogs(ignore_migrated=True):
            if (
                dialog.is_channel
                and dialog.name in ["teagram-logs"]
                or dialog.entity.id in [1511409614]
            ):
                peers.append((await self.client.get_input_entity(dialog.entity)))

        try:
            await self.client(
                UpdateDialogFilterRequest(
                    folder_id,
                    types.DialogFilter(
                        folder_id,
                        title="Teagram",
                        pinned_peers=peers,
                        include_peers=peers,
                        exclude_peers=[],
                    ),
                )
            )
        except Exception as error:
            self.logger.warning(
                "Error while creating teagram's folder\n"
                + "Send this error to support chat:\n"
                + str(error)
            )

    async def on_load(self):
        await self.folder()
        if not self.get("sendOnUpdate"):
            return

        bot: Bot = self.inline.bot
        me = self.manager.me

        try:
            _me = await bot.get_me()
        except Unauthorized:
            self.db.set("teagram.bot", "token", None)

            def restart() -> None:
                os.execl(sys.executable, sys.executable, "-m", "teagram")

            atexit.register(restart)
            self.logger.error("Bot is unauthorized, restarting.")
            return sys.exit(0)

        last = None

        try:
            last = utils.git_hash()
            diff = git.Repo().rev_parse("HEAD")
            if last != diff:
                version = f"<a href='https://github.com/itzlayz/teagram-tl/commit/{last}'>{last[:6]}...</a>"
                await bot.send_message(me.id, f"{self.strings['hupdate']} ({version})")
        except BotBlocked:
            self.logger.error(f'Updater | {self.strings["nodialog"]} ({_me.username})')
        except CantParseEntities:
            await bot.send_message(
                me.id,
                f"{self.strings['hupdate']} (https://github.com/itzlayz/teagram-tl/commit/{last})",
            )
        except Exception as error:
            await bot.send_message(
                me.id, f'{self.strings["eone"]}\n' f'{self.strings["etwo"]} {error}'
            )

    @loader.command()
    async def update(self, message: types.Message):
        if no_git:
            return await utils.answer(
                message,
                "<emoji document_id=5210952531676504517>❌</emoji> <b>No git</b>",
            )
        try:
            await utils.answer(message, self.strings["updating"])
            try:
                output = check_output("git pull", shell=True).decode()
            except Exception:
                check_output("git stash", shell=True)
                output = check_output("git pull", shell=True).decode()

            if not output or "Already up to date." in output:
                return await utils.answer(message, self.strings["lastver"])

            if "requirements.txt" in output:
                await utils.answer(message, self.strings["downloading"])
                try:
                    run(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                            "--disable-pip-version-check",
                            "--no-warn-script-location",
                            "requirements.txt",
                        ],
                        check=True,
                    )
                except Exception:
                    pass

            def restart() -> None:
                os.execl(sys.executable, sys.executable, "-m", "teagram")

            atexit.register(restart)
            self.db.set(
                "teagram.loader",
                "restart",
                {
                    "msg": f"{utils.get_chat(message)}:{message.id}",
                    "start": time.time(),
                    "type": "update",
                },
            )

            await utils.answer(message, self.strings["update"])
            sys.exit(0)
        except Exception as error:
            await utils.answer(message, self.strings["error"].format(error))
