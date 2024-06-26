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

import typing
import logging

from aiogram import types
from ..utils import random_id

logger = logging.getLogger()
Markup = typing.List[typing.Union[typing.List[typing.Dict], typing.Dict]]
Query = typing.List[typing.Dict]


class Utils:
    def _gen_inline_query(
        self, query: Query
    ) -> typing.Union[types.InlineQueryResult, None]:
        """
        Generates inline query from list
        :param query: list with dicts
        :return: `types.InlineQueryResult` or `None`
        """
        if isinstance(query, dict):
            query = [query]

        queries = []
        for q in query:
            q["text"] = q.get("text", q.get("message", ""))
            if not q["text"] and not q.get("caption", ""):
                logger.warning("Inline query needs text")

            if q.get("reply_markup", ""):
                if isinstance(q["reply_markup"], dict):
                    q["reply_markup"] = self._generate_markup([q["reply_markup"]])
                elif isinstance(q["reply_markup"], list):
                    q["reply_markup"] = self._generate_markup(q["reply_markup"])

            if q.get("photo_url", ""):
                queries.append(
                    types.InlineQueryResultPhoto(
                        id=random_id(),
                        title=q.get("title", None),
                        description=q.get("description", None),
                        thumb_url=q["photo_url"],
                        photo_url=q["photo_url"],
                        photo_height=q.get("photo_height", None),
                        photo_width=q.get("photo_width", None),
                        input_message_content=types.InputMediaPhoto(
                            q["photo_url"],
                            q.get("caption", None),
                            parse_mode=q.get("parse_mode", None),
                        ),
                        caption=q.get("caption", None),
                    )
                )
            elif q.get("doc_url", ""):
                queries.append(
                    types.InlineQueryResultDocument(
                        id=random_id(),
                        title=q.get("title", None),
                        description=q.get("description", None),
                        document_url=q["doc_url"],
                        thumb_url=q.get("thumb_url", None),
                        thumb_height=q.get("thumb_height", None),
                        thumb_width=q.get("thumb_width", None),
                        input_message_content=types.InputMediaDocument(
                            q["doc_url"],
                            q.get("thumb_url", None),
                            q.get("caption", None),
                            parse_mode=q.get("parse_mode", None),
                        ),
                        caption=q.get("caption", None),
                    )
                )
            elif q.get("gif_url", ""):
                queries.append(
                    types.InlineQueryResultGif(
                        id=random_id(),
                        title=q.get("title", None),
                        description=q.get("description", None),
                        gif_url=q.get("gif_url", None),
                        gif_height=q.get("gif_height", None),
                        gif_width=q.get("gif_width", None),
                        gif_duration=q.get("gif_duration", None),
                        input_message_content=types.InputMediaAnimation(
                            q["gif_url"],
                            q.get("thumb_url", None),
                            q.get("caption", None),
                            q.get("gif_width", None),
                            q.get("gif_height", None),
                            q.get("gif_duration", None),
                            has_spoiler=q.get("spoiler", None),
                            parse_mode=q.get("parse_mode", None),
                        ),
                        caption=q.get("caption", None),
                    )
                )
            else:
                queries.append(
                    types.InlineQueryResultArticle(
                        id=random_id(),
                        title=q.get("title", None),
                        description=q.get("description", None),
                        input_message_content=types.InputTextMessageContent(
                            q["text"],
                            parse_mode=q.get("parse_mode", None),
                            disable_web_page_preview=q.get(
                                "disable_web_page_preview", None
                            ),
                        ),
                    )
                )

        return queries

    def _generate_markup(
        self, markup: Markup
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
                if btn.get("callback", ""):
                    callback = None

                    if callable(btn["callback"]):
                        callback = random_id(20)
                        self._manager.callback_handlers[callback] = btn["callback"]

                        if btn.get("args", ""):
                            self.callback_units[callback] = btn["args"]

                    keyboard.add(
                        types.InlineKeyboardButton(
                            btn["text"], callback_data=callback or btn["callback"]
                        )
                    )
                elif btn.get("action", ""):
                    actions = ["answer", "close"]
                    if btn["action"] not in actions:
                        logger.warning(f"Invalid action {btn['action']}")
                        continue

                    data = None
                    if btn["action"] == "close":
                        data = self.action_close()
                    else:
                        if btn.get("answer_text", ""):
                            data = self.action_answer(btn["answer_text"])
                        else:
                            logger.warning("Answer action needs answer_text param")
                            continue

                    keyboard.add(
                        types.InlineKeyboardButton(btn["text"], callback_data=data)
                    )

                elif btn.get("input", ""):
                    if btn.get("handler", ""):
                        _id = random_id(5)
                        self.input_handlers[_id] = {
                            "input": btn["input"],
                            "handler": btn["handler"],
                            "args": btn["args"],
                        }

                        keyboard.add(
                            types.InlineKeyboardButton(
                                btn["text"],
                                switch_inline_query_current_chat=f"{_id} ",
                            )
                        )
                    elif btn.get("switch_query"):
                        keyboard.add(
                            types.InlineKeyboardButton(
                                btn["text"], switch_inline_query=btn["switch_query"]
                            )
                        )
                    else:
                        keyboard.add(
                            types.InlineKeyboardButton(
                                btn["text"],
                                switch_inline_query_current_chat=btn["input"] + " ",
                            )
                        )
                elif btn.get("url", ""):
                    keyboard.add(
                        types.InlineKeyboardButton(btn["text"], url=btn["url"])
                    )
                elif btn.get("login_url", ""):
                    keyboard.add(
                        types.InlineKeyboardButton(
                            btn["text"], login_url=btn["login_url"]
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
                    if button.get("callback", ""):
                        callback = None

                        if callable(button["callback"]):
                            callback = random_id(20)
                            self._manager.callback_handlers[callback] = button[
                                "callback"
                            ]

                            if button.get("args", ""):
                                self.callback_units[callback] = button["args"]

                        line += [
                            types.InlineKeyboardButton(
                                button["text"],
                                callback_data=callback or button["callback"],
                            )
                        ]
                    elif button.get("input", ""):
                        if button.get("handler", ""):
                            _id = random_id(5)
                            self.input_handlers[_id] = {
                                "input": button["input"],
                                "handler": button["handler"],
                                "args": button["args"],
                            }

                            line += [
                                types.InlineKeyboardButton(
                                    button["text"], switch_inline_query_current_chat=_id
                                )
                            ]
                        else:
                            line += [
                                types.InlineKeyboardButton(
                                    button["text"],
                                    switch_inline_query_current_chat=button["input"],
                                )
                            ]
                    elif button.get("url", ""):
                        line += [
                            types.InlineKeyboardButton(
                                button["text"], url=button["url"]
                            )
                        ]
                    elif button.get("login_url", ""):
                        line += [
                            types.InlineKeyboardButton(
                                button["text"], login_url=button["login_url"]
                            )
                        ]
                except KeyError as e:
                    logger.debug(f"Can't build button: {e}")

            keyboard.row(*line)

        return keyboard

    def action_close(self) -> str:
        async def close(_self, call):
            await call.delete()

        callback_data = random_id(20)
        self._manager.callback_handlers[callback_data] = close

        return callback_data

    async def delete_unit_message(self, call=None, unit_id: str = None):
        try:
            chat_id = self._units[unit_id].chat.id
            message_id = self._units[unit_id].message.id

            chat_id = getattr(self.message.chat, "id", chat_id)
            message_id = getattr(self.message, "message_id", message_id)

            if chat_id and message_id:
                return await self._bot.delete_message(
                    chat_id=chat_id, message_id=message_id
                )

            return False
        except Exception:
            logger.exception("Can't delete message")
