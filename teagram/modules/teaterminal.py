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

from telethon import types
from .. import loader, utils


@loader.module(name="Terminal", author="teagram")
class TerminalMod(loader.Module):
    """Используйте терминал BASH прямо через 🍵teagram!"""

    strings = {"name": "terminal"}

    @loader.command()
    async def terminal(self, message: types.Message, args: str):
        """Use terminal"""
        await utils.answer(message, "☕")

        args = args.strip()
        output = await utils.bash_exec(args)

        await utils.answer(
            message,
            "<emoji document_id=5472111548572900003>⌨️</emoji>"
            f"<b> {self.strings['cmd']}:</b> <pre language='bash'>{args}</pre>\n"
            f"💾 <b>{self.strings['output']}:</b>\n<pre language='bash'>"
            f"{output}"
            "</pre>",
        )
