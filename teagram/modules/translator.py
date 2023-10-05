from .. import loader, utils, validators
from ..types import Config, ConfigValue

from telethon import types
from googletrans import Translator, LANGUAGES
from googletrans.models import Translated

@loader.module('Translator', 'teagram')
class TranslatorMod(loader.Module):
    """Переводчик"""
    strings = {'name': 'translator'}
    
    def __init__(self):
        self.config = Config(
            ConfigValue(
                option='language',
                docstring='Язык',
                default='en',
                value=self.db.get('Translator', 'language', 'en'),
                validator=validators.String()
            )
        )

    @loader.command()
    async def translate(self, message: types.Message, args):
        """Перевод"""
        if not (text := args):
            if not (reply := (await message.get_reply_message())):
                return await utils.answer(
                    message,
                    self.strings['notext']
                )
        
        if (lang := self.config.get('language')) not in LANGUAGES:
            return await utils.answer(
                message,
                self.strings['wronglang'].format(lang)
            )
        
        translated: Translated = Translator().translate((text or reply.raw_text), dest=lang)
        
        await utils.answer(
            message,
            f"👅 <b>{self.strings['lang']} {translated.src} -> {lang}</b>\n"
            f"🗣 <b>{self.strings['pronun']} {translated.pronunciation or '-'}</b>\n"
            f"➡ {self.strings['text']}:\n"
            f"<b>{translated.origin}</b>\n"
            f"➡ {self.strings['trans']}:\n"
            f"<b>{translated.text}</b>"
        )

