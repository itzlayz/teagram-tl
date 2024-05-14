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

import telethon
import time

from .. import __version__, loader, utils, validators
from ..types import Config, ConfigValue

from telethon.tl.custom import Message
from datetime import timedelta


@loader.module(name="Info", author="teagram")
class InfoMod(loader.Module):
    """Узнайте что такое юзербот, или информацию о вашем 🍵teagram"""

    strings = {"name": "info"}

    def __init__(self):
        self.boot_time = time.time()
        self.config = Config(
            ConfigValue(
                option="customText",
                default="",
                value=self.db.get("info", "customText", ""),
                validator=validators.String(),
                doc="Ключевые слова: cpu, ram, tele, owner, uptime, version, platform",
            ),
            ConfigValue(
                option="customImage",
                doc="",
                default="",
                value=self.db.get("info", "customImage", ""),
                validator=validators.String(),
            ),
        )

    async def text(self, message: Message) -> str:
        platform = utils.get_platform()
        uptime = timedelta(seconds=round(time.time() - utils._init_time))

        last = utils.git_hash()
        now = str(await utils.bash_exec("git rev-parse HEAD")).strip()
        version = f"v{__version__}" + (
            " " + self.strings("update") if last != now else ""
        )
        git_version = f'<a href="https://github.com/itzlayz/teagram-tl/commit/{last}">{last[:7]}</a>'

        me = self.manager.me.username if message.from_id else "Anonymous"

        default = f"""
<b><emoji document_id=5433758796289685818>👑</emoji> {self.strings('owner')}</b>:  <code>{me}</code>
<b><emoji document_id=5395463497783983254>☕️</emoji> {self.strings('version')}</b>:  <code>{version}</code> ({git_version})

<b>💽 CPU</b>: ~<code>{utils.get_cpu()}%</code>
<b><emoji document_id=5237799019329105246>🧠</emoji> RAM</b>: ~<code>{utils.get_ram()}MB</code>

<b><emoji document_id=5213349767672769194>⏰</emoji> {self.strings('uptime')}</b>:  <code>{uptime}</code>
<b>📱 {self.strings('version')} telethon: <code>{telethon.__version__}</code></b>

<b>{platform}</b>
        """

        custom = self.config.get("customText")

        if custom:
            custom = custom.format(
                owner=me,
                cpu=utils.get_cpu(),
                ram=utils.get_ram(),
                uptime=uptime,
                version=version,
                platform=platform,
                tele=telethon.__version__,
            )

        return custom or default

    async def info_cmd(self, message: Message):
        """Some information about userbot"""
        avatar = self.config.get("customImage")
        davatar = "https://raw.githubusercontent.com/MuRuLOSE/teagram-assets/main/teagram_banner2v1.png"

        text = await self.text(message)
        await utils.answer(
            message, photo=True, response=avatar or davatar, caption=text
        )
