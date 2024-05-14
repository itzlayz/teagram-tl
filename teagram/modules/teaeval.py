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

import ast

from .. import loader, utils
from telethon import types


def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])
        if isinstance(body[-1], ast.If):
            insert_returns(body[-1].body)
            insert_returns(body[-1].orelse)
        if isinstance(body[-1], ast.With):
            insert_returns(body[-1].body)


async def execute_python_code(code, env={}):
    try:
        fn_name = "_eval_expr"
        cmd = "\n".join(f" {i}" for i in code.splitlines())
        body = f"async def {fn_name}():\n{cmd}"
        parsed = ast.parse(body)
        body = parsed.body[0].body
        insert_returns(body)
        env = {"__import__": __import__, **env}
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        return await eval(f"{fn_name}()", env)
    except Exception as error:
        return error


@loader.module(name="Eval", author="teagram")
class EvalMod(loader.Module):
    """Используйте eval прямо через 🍵teagram!"""

    async def e_cmd(self, message: types.Message, args: str):
        reply = await message.get_reply_message()
        result = await execute_python_code(
            args,
            {
                "self": self,
                "client": self.client,
                "app": self.client,
                "manager": self.manager,
                "bot": self.bot,
                "db": self.db,
                "utils": utils,
                "loader": loader,
                "telethon": __import__("telethon"),
                "message": message,
                "reply": reply,
                "r": reply,
                "args": args,
                "me": self.manager.me,
                "c": self.client,
            },
        )

        if getattr(result, "stringify", ""):
            try:
                result = str(result.stringify())
            except Exception:
                pass

        await utils.answer(
            message,
            "<b>🐍 Code</b>:\n"
            f"<code>{utils.escape_html(args)}</code>\n"
            "<b>💻 Output</b>:\n"
            f"<code>{utils.escape_html(result)}</code>",
        )
