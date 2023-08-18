import pyrogram
import os
import contextlib
import time

from .terminal import bash_exec
from pyrogram import Client, types
from datetime import timedelta
from .. import __version__, loader, utils


@loader.module(name="UserBot", author='teagram')
class AboutMod(loader.Module):
    """Узнайте что такое юзербот, или информацию о вашем 🍵teagram"""
    boot_time = time.time()
    
    async def info_cmd(self, app: Client, message: types.Message):
        """Информация о вашем 🍵teagram."""
        platform = ""
        IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")
        IS_CODESPACES = "CODESPACES" in os.environ
        IS_DOCKER = "DOCKER" in os.environ
        IS_GOORM = "GOORM" in os.environ
        IS_WIN = "WINDIR" in os.environ
        IS_WSL = False
        with contextlib.suppress(Exception):
            from platform import uname
            if "microsoft-standard" in uname().release:
                IS_WSL = True

        if IS_TERMUX:
            platform = "<emoji id=5407025283456835913>📱</emoji> Termux"
        elif IS_DOCKER:
            platform = "<emoji id=5431815452437257407>🐳</emoji> Docker"
        elif IS_GOORM:
            platform = "<emoji id=5215584860063669771>💚</emoji> Goorm"
        elif IS_WSL:
            platform = "<emoji id=6327609909416298142>🧱</emoji> WSL"
        elif IS_WIN:
            platform = "<emoji id=5309880373126113150>💻</emoji> Windows"
        elif IS_CODESPACES:
            platform = "<emoji id=5467643451145199431>👨‍💻</emoji> Github Codespaces"
        else:
            platform = "🖥️ VDS"
        await utils.answer(message, "☕")
        me: types.User = await app.get_me()
        uptime_raw = round(time.time() - self.boot_time)

        uptime = (timedelta(seconds=uptime_raw))
        
        last = await bash_exec('git log -1').split()[1]
        now = await bash_exec('git rev-parse HEAD')
        version = f'`v{__version__}`' + (' <b>Доступно обновление</b>') if last != now else ""
        
        await utils.answer(
            message,
            f"""
<b><emoji id=5471952986970267163>💎</emoji> Владелец</b>:  `{me.username}`
<b><emoji id=6334741148560524533>🆔</emoji> Версия</b>:  `v{__version__}`

<b><emoji id=5357480765523240961>🧠</emoji> CPU</b>:  `{utils.get_cpu()}%`
<b>💾 RAM</b>:  `{utils.get_ram()}MB`

<b><emoji id=5974081491901091242>🕒</emoji> Аптайм</b>:  `{uptime}`
<b><emoji id=5377399247589088543>🔥</emoji> Версия pyrogram: `{pyrogram.__version__}`</b>

<b>{platform}</b>
""")
        
    async def teagram_cmd(self, app: Client, message: types.Message, args: str):
        """Информация о UserBot"""
        await utils.answer(message, "☕")
        await utils.answer(message, '''<emoji id=5467741625507651028>🤔</emoji> <b>Что такое юзербот?</b>
        
<emoji id=5373098009640836781>📚</emoji> <b>Юзербот это</b> - <b>Сборник разных програм</b> для взаймодeйствия с Telegram API
А с помощью взаймодействия с Telegram API <b>можно написать разныe скрипты</b> для автоматизаций некоторых действий со стороны пользователя такие как: <b>Присоединение к каналам, отправление сообщений, и т.д</b>

<emoji id=6325536273435986182>🤔</emoji> <b>Чем отличается юзербот от обычного бота?</b>

🤭 <b>Юзербот может выполняться на аккаунте обычного пользователя</b>
Например: @paveldurov А бот может выполняться только на специальных бот аккаунтах например: @examplebot
<b>Юзерботы довольно гибкие</b> в плане настройки, у них больше функций.

<emoji id=5467596412663372909>⁉️</emoji> <b>Поддерживаются ли оффициально юзерботы телеграмом?</b>

<emoji id=5462882007451185227>🚫</emoji> <b>Нет.</b> Они оффициально не поддерживаются, но вас не заблокируют за использование юзерботов.
Но <b>могут заблокировать в случае выполнения вредоносного кода или за злоупотребление Telegram API</b> на вашем аккаунте, так что владельцу юзербота надо тщательно проверять что выполняется на вашем аккаунте.''')
