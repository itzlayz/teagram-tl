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

import logging

import os
import re
import sys
import time


import atexit
import requests

from telethon import types
from telethon.tl.custom import Message

from .. import loader, utils

GIT_REGEX = re.compile(
    r"^https?://github\.com((?:/[a-z0-9-]+){2})(?:/tree/([a-z0-9-]+)((?:/[a-z0-9-]+)*))?/?$",
    flags=re.IGNORECASE,
)


async def get_git_raw_link(repo_url: str):
    """Получить raw ссылку на репозиторий"""
    match = GIT_REGEX.search(repo_url)
    if not match:
        return False

    repo_path = match.group(1)
    branch = match.group(2)
    path = match.group(3)

    r = await utils.run_sync(requests.get, f"https://api.github.com/repos{repo_path}")
    if r.status_code != 200:
        return False

    branch = branch or r.json()["default_branch"]

    return f"https://raw.githubusercontent.com{repo_path}/{branch}{path or ''}/"


@loader.module(name="Loader", author="teagram")
class LoaderMod(loader.Module):
    """Загрузчик модулей"""

    strings = {"name": "loader"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "save_module",
                True,
                "Saves module on load",
                validator=loader.validators.Boolean(),
            )
        )

    def prep_docs(self, module: str) -> str:
        module = self.lookup(module)
        prefix = self.get_prefix()[0]
        return "\n".join(
            f"""👉 <code>{prefix + command}</code> {f"- <b>{module.command_handlers[command].__doc__}</b>" or ''}"""
            for command in module.command_handlers
        )

    async def accept_load(self, call, source: str, warning: str):
        empty = self.inline._generate_markup([])

        data = await self.manager.load_module(source)
        module = "_".join(data.lower().split())
        if data is True:
            return await call.edit(self.strings["downdedreq"], empty)

        self.manager.warnings.remove(warning)
        await call.edit(
            (self.strings["loadedmod"].format(data) + "\n" + self.prep_docs(module)),
            empty,
        )

    async def decline_load(self, call):
        await call.edit("✅", self.inline._generate_markup([]))

    @loader.command()
    async def repo(self, message: types.Message, args: str):
        """Установить репозиторий с модулями. Использование: repo <ссылка на репозиторий или reset>"""
        if not args:
            return await utils.answer(message, self.strings["noargs"])

        if args == "reset":
            self.db.set(
                "teagram.loader", "repo", "https://github.com/itzlayz/teagram-modules"
            )
            return await utils.answer(message, self.strings["urlrepo"])

        if not await get_git_raw_link(args):
            return await utils.answer(message, self.strings["wrongurl"])

        self.db.set("teagram.loader", "repo", args)
        return await utils.answer(message, self.strings["yesurl"])

    @loader.command()
    async def dlrepo(self, message: types.Message, args: str):
        """Загрузить модуль по ссылке. Использование: dlrepo <ссылка или all или ничего>"""
        modules_repo = self.db.get(
            "teagram.loader", "repo", "https://github.com/itzlayz/teagram-modules"
        )
        api_result = await get_git_raw_link(modules_repo)
        if not api_result:
            return await utils.answer(message, self.strings["errapi"])

        raw_link = api_result
        modules = await self.get_module_list(raw_link)
        modules_text = "\n".join(map("<code>{}</code>".format, modules))

        if not args:
            text = (
                self.strings["listmods"].format(modules_repo=modules_repo)
                + modules_text
            )
            return await utils.answer(message, text, link_preview=False)

        count, error_text, module_name = await self.load_modules(
            modules, raw_link, args
        )

        if error_text:
            return await utils.answer(message, error_text)

        return await utils.answer(
            message,
            (
                self.strings["loadedmod"].format(module_name)
                if args != "all"
                else self.strings["loaded"].format(count, len(modules))
            )
            + "\n"
            + self.prep_docs(module_name),
        )

    async def get_module_list(self, raw_link):
        modules = await utils.run_sync(requests.get, f"{raw_link}all.txt")
        if modules.status_code != 200:
            modules = await utils.run_sync(requests.get, f"{raw_link}full.txt")
            if modules.status_code != 200:
                return []

        return modules.text.splitlines()

    async def load_modules(self, modules, raw_link, args):
        error_text, module_name = None, None
        count = 0

        if args == "all":
            for module in modules:
                module = raw_link + module + ".py"
                try:
                    r = await utils.run_sync(requests.get, module)
                    if r.status_code != 200:
                        raise requests.exceptions.RequestException
                except requests.exceptions.RequestException:
                    continue

                module_name = await self.manager.load_module(r.text, r.url)
                if not module_name:
                    continue

                self.db.set(
                    "teagram.loader",
                    "modules",
                    list(set(self.db.get("teagram.loader", "modules", []) + [module])),
                )
                count += 1
        else:
            if args in modules:
                args = raw_link + args + ".py"

            try:
                r = await utils.run_sync(requests.get, args)
                if r.status_code != 200:
                    raise requests.exceptions.ConnectionError

                module_name = await self.manager.load_module(r.text, r.url)
                if module_name is True:
                    error_text = self.strings["downdedreq"]

                if not module_name:
                    error_text = self.strings["errmod"]
            except requests.exceptions.MissingSchema:
                error_text = self.strings["wrongurl"]
            except requests.exceptions.ConnectionError:
                error_text = self.strings["modurlerr"]
            except requests.exceptions.RequestException:
                error_text = self.strings["reqerr"]

            if not error_text:
                self.db.set(
                    "teagram.loader",
                    "modules",
                    list(set(self.db.get("teagram.loader", "modules", []) + [args])),
                )

        return count, error_text, module_name

    @loader.command(alias="dlm")
    async def dlmod(self, message: Message, args: str):
        if not args:
            return await utils.answer(message, "❌ Вы не указали ссылку")

        try:
            response = await utils.run_sync(requests.get, args)
            module = await self.manager.load_module(response.text, response.url)

            if isinstance(module, tuple):
                return await self.inline.form(
                    message=message,
                    text=f"⚠️ {module[1]}",
                    reply_markup=[
                        {
                            "text": self.strings["accept"],
                            "callback": self.accept_load,
                            "args": (response.text, module[1]),
                        },
                        {
                            "text": self.strings["decline"],
                            "callback": self.decline_load,
                        },
                    ],
                )

            if module is True:
                return await utils.answer(message, self.strings["downdedreq"])

            if not module:
                return await utils.answer(message, self.strings["errmod"])

            if self.get("save_module", True):
                self.db.set(
                    "teagram.loader",
                    "modules",
                    list(set(self.db.get("teagram.loader", "modules", []) + [args])),
                )

            await utils.answer(
                message,
                self.strings["loadedmod"].format(module)
                + "\n"
                + self.prep_docs(module),
            )

        except requests.exceptions.MissingSchema:
            await utils.answer(message, self.strings["wrongurl"])
        except Exception as error:
            import traceback

            traceback.print_exc()
            await utils.answer(message, f"❌ <code>{error}</code>")

    @loader.command()
    async def loadmod(self, message: Message):
        """Загрузить модуль по файлу. Использование: <реплай на файл>"""
        reply: Message = await message.get_reply_message()
        file = (
            message if message.document else reply if reply and reply.document else None
        )

        if not file:
            return await utils.answer(message, self.strings["noreply"])

        source = await reply.download_media(bytes)
        try:
            source = source.decode()
        except UnicodeDecodeError:
            return await utils.answer(message, self.strings["errunicode"])

        module_name = await self.manager.load_module(source)
        if not module_name:
            return await utils.answer(message, self.strings["noreq"])

        if isinstance(module_name, tuple):
            return await self.inline.form(
                message=message,
                text=f"⚠️ {module_name[1]}",
                reply_markup=[
                    {
                        "text": self.strings["accept"],
                        "callback": self.accept_load,
                        "args": (source, module_name[1]),
                    },
                    {"text": self.strings["decline"], "callback": self.decline_load},
                ],
            )

        if module_name is True:
            return await utils.answer(message, self.strings["downdedreq"])

        module = "_".join(module_name.lower().split())
        if self.get("save_module"):
            with open(
                f"teagram/modules/{module_name}.py", "w", encoding="utf-8"
            ) as file:
                file.write(source)

        await utils.answer(
            message,
            (
                self.strings["loadedmod"].format(module_name)
                + "\n"
                + self.prep_docs(module)
            ),
        )

    @loader.command(alias="ulm")
    async def unloadmod(self, message: types.Message, args: str = ""):
        """Выгрузить модуль. Использование: unloadmod <название модуля>"""
        modules = [
            "config",
            "eval",
            "help",
            "info",
            "terminal",
            "settings",
            "updater",
            "loader",
        ]

        args = args.strip()
        if args in modules:
            return await utils.answer(message, self.strings["cantunload"])

        module_name = self.manager.unload_module(args)
        if not args or not module_name:
            return await utils.answer(message, self.strings["notfound"].format(args))

        return await utils.answer(
            message, self.strings["unloadedmod"].format(module_name)
        )

    @loader.command(alias="reload")
    async def reloadmod(self, message: types.Message, args: str):
        if not args:
            return await utils.answer(message, self.strings["noargs"])

        try:
            module = args.split(maxsplit=1)[0].replace(".py", "")
            if module.lower() == "teaconfig":
                return await utils.answer(message, "❌ Not bad")

            if f"{module}.py" not in os.listdir("teagram/modules"):
                return await utils.answer(
                    message, self.strings["notfound"].format(module)
                )

            unload = self.manager.unload_module(module)
            with open(f"teagram/modules/{module}.py", encoding="utf-8") as file:
                module_source = file.read()

            load = await self.manager.load_module(module_source)

            if not load and not unload:
                return await utils.answer(message, self.strings["reqerr"])
        except Exception as error:
            logging.error(error)
            return await utils.answer(message, self.strings["basicerr"])

        return await utils.answer(message, self.strings["reloaded"].format(module))

    @loader.command("Скинуть модуль из папки модулей", "mlmod")
    async def showmod(self, message: types.Message, args):
        mod = args.split()
        if not mod or f"{mod[0]}.py" not in os.listdir("teagram/modules"):
            return await utils.answer(message, self.strings["wrongmod"])

        await utils.answer(
            message,
            f"teagram/modules/{mod[0]}.py",
            document=True,
            caption=self.strings["replymod"].format(mod[0])
            + "\n"
            + self.strings["replytoload"].format(self.prefix[0]),
        )

    @loader.command()
    async def restart(self, message: types.Message):
        """Перезагрузка юзербота"""

        def _restart() -> None:
            os.execl(sys.executable, sys.executable, "-m", "teagram")

        atexit.register(_restart)
        self.db.set(
            "teagram.loader",
            "restart",
            {
                "msg": f"{utils.get_chat(message)}:{message.id}",
                "start": time.time(),
                "type": "restart",
            },
        )

        await utils.answer(message, self.strings["restarting"])
        sys.exit(0)
