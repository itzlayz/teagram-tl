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
import logging

from aiogram import types
from ..utils import random_id

logger = logging.getLogger()
Markup = typing.List[typing.Union[typing.List[typing.Dict], typing.Dict]]

class Utils:
    def _generate_markup(
            self, 
            markup: Markup
            ) -> typing.Union[types.InlineKeyboardMarkup, None]:
        """
        Generates markup from list
        :param markup: list with dicts
        :return: `types.InlineKeyboardMarkup` or `None`
        """
        if not markup:
            return None

        keyboard = types.InlineKeyboardMarkup()
        for mark in markup:
            if isinstance(mark, list):
                continue

            btn = mark
            try:
                if btn.get('callback', ''):
                    callback = None

                    if callable(btn['callback']):
                        callback = random_id(20)
                        self._manager.callback_handlers[callback] = btn['callback']

                        if btn.get('args', ''):
                            self.callback_units[callback] = btn['args']

                    keyboard.add(
                        types.InlineKeyboardButton(
                            btn['text'],
                            callback_data=callback or btn['callback']
                        )
                    )
                elif btn.get('input', ''):
                    if btn.get('handler', ''):
                        _id = random_id(5)
                        self.input_handlers[_id] = {
                            'input': btn['input'],
                            'handler': btn['handler'], 
                            'args': btn['args']
                        }

                        keyboard.add(
                            types.InlineKeyboardButton(
                                btn['text'],
                                switch_inline_query_current_chat=f"{_id} ",
                            )
                        )
                    elif btn.get('switch_query'):
                        keyboard.add(
                            types.InlineKeyboardButton(
                                btn['text'],
                                switch_inline_query=btn['switch_query']
                            )
                        )
                    else:
                        keyboard.add(
                            types.InlineKeyboardButton(
                                btn['text'],
                                switch_inline_query_current_chat=btn['input']+" "
                            )
                        )
                elif btn.get('url', ''):
                    keyboard.add(
                        types.InlineKeyboardButton(
                            btn['text'],
                            url=btn['url']
                        )
                    )
                elif btn.get('login_url', ''):
                    keyboard.add(
                        types.InlineKeyboardButton(
                            btn['text'],
                            login_url=btn['login_url']
                        )
                    )
            except KeyError as e:
                logger.debug(f"Can't build button: {e}")

        for row in markup:
            line = []
            if not isinstance(row, list):
                continue

            for button in row:
                try:
                    if button.get('callback', ''):
                        callback = None

                        if callable(button['callback']):
                            callback = random_id(20)
                            self._manager.callback_handlers[callback] = button['callback']

                            if button.get('args', ''):
                                self.callback_units[callback] = button['args']

                        line += [
                            types.InlineKeyboardButton(
                                button['text'],
                                callback_data=callback or button['callback']
                            )
                        ]
                    elif button.get('input', ''):
                        if button.get('handler', ''):
                            _id = random_id(5)
                            self.input_handlers[_id] = {
                                'input': button['input'],
                                'handler': button['handler'],
                                'args': button['args']
                            }

                            line += [
                                types.InlineKeyboardButton(
                                    button['text'],
                                    switch_inline_query_current_chat=_id
                                )
                            ]
                        else:
                            line += [
                                types.InlineKeyboardButton(
                                    button['text'],
                                    switch_inline_query_current_chat=button['input']
                                )
                            ]
                    elif button.get('url', ''):
                        line += [
                            types.InlineKeyboardButton(
                                button['text'],
                                url=button['url']
                            )
                        ]
                    elif button.get('login_url', ''):
                        line += [
                            types.InlineKeyboardButton(
                                button['text'],
                                login_url=button['login_url']
                            )
                        ]
                except KeyError as e:
                    logger.debug(f"Can't build button: {e}")

            keyboard.row(*line)

        return keyboard
