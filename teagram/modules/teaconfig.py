#                            ██╗████████╗███████╗██╗░░░░░░█████╗░██╗░░░██╗███████╗
#                            ██║╚══██╔══╝╚════██║██║░░░░░██╔══██╗╚██╗░██╔╝╚════██║
#                            ██║░░░██║░░░░░███╔═╝██║░░░░░███████║░╚████╔╝░░░███╔═╝
#                            ██║░░░██║░░░██╔══╝░░██║░░░░░██╔══██║░░╚██╔╝░░██╔══╝░░
#                            ██║░░░██║░░░███████╗███████╗██║░░██║░░░██║░░░███████╗
#                            ╚═╝░░░╚═╝░░░╚══════╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚══════╝
#                                            https://t.me/itzlayz
#                           
#                                    🔒 Licensed under the GNU AGPLv3
#                                 https://www.gnu.org/licenses/agpl-3.0.html

import typing

from .. import loader, utils
from ..validators import ValidationError
from ..bot.types import InlineCall

from aiogram import Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

@loader.module("TeaConfig", "teagram")
class TeaConfigMod(loader.Module):
    strings = {'name': "teaconfig"}
    def __init__(self):
        self._bot: Bot = self.inline.bot
    
    def keywords(self, config, option: str) -> str:
        if not (validator := getattr(config.config[option], 'validator')):
            return ""

        if not (keywords := getattr(validator.type, 'keywords', '')):
            return ""

        keys = list(keywords.items())
        text = ", ".join(f'<b>{key[0]}</b> - <code>{key[1]}</code>' for key in keys)

        return f"🔎 {text}"

    async def close(self, call: InlineCall):
        self._id = {}
        await call.delete()
    
    async def change(
        self, 
        call: InlineCall,
        module: str,
        option: str, 
        value: typing.Any
    ):
        module = self.lookup(module)
        config = module.config

        config[option] = value
        module.set(option, value)
    
        markup = [
            {
                "text": self.strings("back"), 
                "callback": self.configure,
                "args": (module)
            },
            {
                "text": self.strings("close"),
                "callback": self.close
            }
        ]

        await call.edit(
            self.strings("edit_value"),
            self.inline._generate_markup(markup)
        )

    async def set_default_value(
        self,
        call: InlineCall,
        module: str,
        option: str
    ):
        module = self.lookup(module)
        config = module.config
        value = config.get_default(option)

        config[option] = value
        module.set(option, value)
        markup = [
            {
                "text": self.strings("back"), 
                "callback": self.configure,
                "args": (module)
            },
            {
                "text": self.strings("close"),
                "callback": self.close
            }
        ]

        await call.edit(
            self.strings("edited_default_value").format(option),
            self.inline._generate_markup(markup)
        )
        
    async def set_value_inline_handler(
        self,
        call: InlineQuery
    ):
        if not getattr(self, '_id', {}).get('id', ''):
            return

        option = self._id['option']
        module = self._id['module']
        value = call.query.replace('set_value ', '')

        module = self.lookup(module)
        config = module.config
        markup = [
            {
                "text": self.strings("back"), 
                "callback": self.configure,
                "args": (module)
            },
            {
                "text": self.strings("close"),
                "callback": self.close
            }
        ]

        try:
            config[option] = value
        except ValidationError:
            return await call.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.random_id(),
                        title='Error',
                        input_message_content=InputTextMessageContent(
                            self.strings("keywords_error")),
                        reply_markup=self.inline._generate_markup(markup)
                    )
                ]
            )
        
        return await call.answer(
            [
                InlineQueryResultArticle(
                    id=utils.random_id(),
                    title='Teagram',
                    description='Configuring',
                    input_message_content=InputTextMessageContent(
                        self.strings("sure_change")),
                    reply_markup=self.inline._generate_markup(
                        [
                            {
                                "text": self.strings("change"),
                                "callback": self.change,
                                "args": (self._id['module'], option, value)
                            },
                            markup
                        ]
                    )
                )
            ]
        )   

    async def back_modules(
        self,
        call: InlineCall
    ):
        markup = [
            {
                "text": module.name.title(), 
                'callback': self.configure, 
                'args': (module.name)
            } 
            for module in self.manager.modules
            if getattr(self.lookup(module.name), 'config', '')
        ] + [
            {
                "text": self.strings("close"),
                "callback": self.close
            }
        ]

        await call.edit(
            self.strings("choose_module"),
            reply_markup=self.inline._generate_markup(
                utils.sublist(markup))
        )
        

    async def configure(
        self, 
        call: InlineCall, 
        module: str
    ):
        markup = [
            {
                'text': option,
                'callback': self.configure_value,
                'args': (module, option)
            } for option in self.lookup(module).config
        ] + [
            [
                {
                    "text": self.strings("back"), 
                    "callback": self.back_modules
                },
                {
                    "text": self.strings("close"),
                    "callback": self.close
                }
            ]
        ]

        await call.edit(
            self.strings("choose_value"),
            self.inline._generate_markup(markup)
        )

    async def configure_value(
        self,
        call: InlineCall,
        module: str,
        option: str
    ):
        config = self.lookup(module).config
        docstring = config.get_doc(option)
        default = config.get_default(option)
        value = config[option]

        if callable(docstring):
            docstring = docstring()

        _id = utils.random_id(5)
        self._id = {"id": _id, "module": module.lower(), "option": option}
        
        markup = [
            {
                "text": self.strings("change"),
                "input": "set_value"
            },
            [
                {
                    "text": self.strings("back"), 
                    "callback": self.configure,
                    "args": (module)
                },
                {
                    "text": self.strings("close"),
                    "callback": self.close
                }
            ]
        ]

        await call.edit(
            (
                self.strings("configure_value").format(module, option) +
                f"❔ {docstring}\n\n" +
                self.strings("default_value").format(utils.escape_html(default)) +
                self.strings("current_value").format(utils.escape_html(value)) +
                self.keywords(config, option)
            ),
            self.inline._generate_markup(markup)
        )

    async def opencfg(
        self,
        call: InlineCall
    ):
        await call.edit(
            text=self.strings("choose_module"),
            reply_markup=self.inline._generate_markup(
                utils.sublist(
                    [
                        {
                            "text": module.name.title(), 
                            'callback': self.configure, 
                            'args': (module.name)
                        } 
                        for module in self.manager.modules
                        if getattr(self.lookup(module.name), 'config', '')
                    ]
                )
            )
        )

    @loader.command()
    async def cfgcmd(self, message):
        markup = [
            {
                "text": self.strings('open'),
                "callback": self.opencfg
            }
        ]

        await self.inline.form(
            message=message,
            text=self.strings('open'),
            reply_markup=markup
        )