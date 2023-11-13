import logging
import inspect
import traceback
from aiogram.types import (
    CallbackQuery, Message, InlineQuery, InlineQueryResultArticle, InlineQueryResultGif,
    InputTextMessageContent, InlineQueryResultPhoto, InlineQueryResultDocument,
    InputMediaPhoto, InputMediaAnimation, InputMediaDocument, ChosenInlineResult,
    InputFile)
from .types import Item, InlineCall
from .. import utils

class Events(Item):
    """
    Event handler class.
    Handles various event types such as messages, callback queries, and inline queries.
    """
    def __init__(self):
        super().__init__()

        self._units: dict
        self.callback_units: dict

    async def _message_handler(self, message: Message) -> Message:
        """
        Message event handler.

        Processes incoming messages by invoking appropriate message handlers.

        Args:
            message (Message): The incoming message.

        Returns:
            Message: The processed message.
        """
        if message.text == '/start':
            return await message.reply_photo(
                photo=InputFile('assets/teagram_banner.png'),
                caption=self._manager.strings['inline_hello'],
                reply_markup=self._generate_markup(
                    [
                        {
                            "text": "🐙 Github",
                            "url": "https://github.com/itzlayz/teagram-tl"
                        }
                    ]
                ),
                parse_mode='html'
            )

        for func in self._manager.message_handlers.values():
            if not await self._check_filters(func, func.__self__, message):
                continue

            try:
                await func(message)
            except Exception as error:
                logging.exception(error)

        return message

    async def _callback_handler(self, call: CallbackQuery) -> CallbackQuery:
        """
        Callback query event handler.

        Processes incoming callback queries by invoking appropriate callback handlers.

        Args:
            call (CallbackQuery): The incoming callback query.

        Returns:
            CallbackQuery: The processed callback query.
        """
        if call.from_user.id != self._manager.me.id:
           return

        call = InlineCall(call, self)
        try:
            if (func := self._units[call.data]):
                if func.get('callback'):
                    try:
                        await func.callback(call)
                    except Exception as error:
                        logging.exception(error)
        except KeyError:
            pass

        try:
            if (func := self._manager.callback_handlers[call.data]):
                args = self.callback_units[call.data]
                try:
                    if args:
                        if isinstance(args, (list, tuple)):
                            await func(call, *args)
                        else:
                            await func(call, args)
                    elif len(inspect.getfullargspec(
                            func
                        ).args) == 2:
                        await func(call)
                except Exception as error:
                    logging.exception(error)

            return call
        except KeyError:
            pass
        except:
            traceback.print_exc()

        try:
            for key, func in self._manager.callback_handlers.items():
                if not await self._check_filters(func, func.__self__, call):
                    continue

                try:
                    if len(inspect.getfullargspec(func).args) == 2: 
                        await func(call)
                    elif (
                            args := self.callback_units.get(key, ())
                        ):
                        await func(call, args)
                except Exception as error:
                    logging.exception(error)
        except RuntimeError:
            pass

        return call

    async def _inline_handler(self, inline_query: InlineQuery) -> InlineQuery:
        """
        Inline query event handler.

        Processes incoming inline queries by invoking appropriate inline handlers.

        Args:
            inline_query (InlineQuery): The incoming inline query.

        Returns:
            InlineQuery: The processed inline query.
        """
        query = inline_query.query
        query_ = query.split()

        cmd = query_[0]
        args = " ".join(query_[1:])
        inline_query.args = args

        func = self._manager.inline_handlers.get(cmd)
        if func:
            if not await self._check_filters(func, func.__self__, inline_query):
                return
            
        if not query_:
            commands = ""
            for command, func in self._manager.inline_handlers.items():
                if func:
                    if await self._check_filters(func, func.__self__, inline_query):
                        commands += f"\n💬 <code>@{self.bot_username} {command}</code>"

            message = InputTextMessageContent(
                f"👇 <b>Available Commands</b>\n"
                f"{commands}"
            )

            return await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.random_id(),
                        title="Available Commands",
                        input_message_content=message
                    )
                ], cache_time=0
            )

        try:
            form = self._units[query]
            text = form.get('text')
            keyboard = None
            
            if isinstance(form['keyboard'], list):
                keyboard = self._generate_markup(form['keyboard'])
            elif isinstance(form['reply_markup'], list):
                keyboard = self._generate_markup(form['reply_markup'])
                
            if form['photo']:
                await inline_query.answer(
                    [
                        InlineQueryResultPhoto(
                            id=utils.random_id(),
                            title=form.get('title'),
                            description=form.get('description'),
                            input_message_content=InputMediaPhoto(
                                form['photo'],
                                form.get('caption', text),
                                'HTML'
                            ),
                            caption=form.get('caption', text),
                            reply_markup=keyboard,
                            photo_url=form['photo'],
                            thumb_url=form['photo']
                        )
                    ]
                )
            elif form['gif']:
                await inline_query.answer(
                    [
                        InlineQueryResultGif(
                            id=utils.random_id(20),
                            title=form.get("title"),
                            caption=form.get('caption', text),
                            parse_mode="HTML",
                            thumb_url=form.get("thumb", form["gif"]),
                            gif_url=form["gif"],
                            reply_markup=keyboard,
                            input_message_content=InputMediaAnimation(
                                form['gif'],
                                form.get('caption', text),
                                'HTML'
                            ),
                        ),
                    ]
                )
            elif form['doc']:
                await inline_query.answer(
                    [
                        InlineQueryResultDocument(
                            id=utils.random_id(),
                            title=form.get('title'),
                            description=form.get('description'),
                            input_message_content=InputMediaDocument(
                                form['doc'],
                                caption=form.get('caption', text),
                                parse_mode='HTML'
                            ),
                            reply_markup=keyboard,
                            document_url=form['doc'],
                            caption=form.get('caption', text)
                        )
                    ]
                )
            else:
                await inline_query.answer(
                    [
                        InlineQueryResultArticle(
                            id=utils.random_id(),
                            title=form.get('title'),
                            description=form.get('description'),
                            input_message_content=InputTextMessageContent(
                                text,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            ),
                            reply_markup=keyboard
                        )
                    ]
                )
            return
        except KeyError:
            pass
        except Exception as error:
            traceback.print_exc()
        
        if not func:
            return await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.random_id(),
                        title="Error",
                        input_message_content=InputTextMessageContent(
                            "❌ <b>No such inline command</b>")
                    )
                ], cache_time=0
            )

        try:
            if (
                len(vars_ := inspect.getfullargspec(func).args) > 3
                and vars_[3] == "args"
            ):
                await func(inline_query, args)
            else:
                await func(inline_query)
        except Exception as error:
            logging.exception(error)

        return inline_query

    async def _chosen_inline_handler(self, chosen_inline_query: ChosenInlineResult):
        query = chosen_inline_query.query
        
        if (input_handler := self.input_handlers.get(query, '')):
            try:
                await input_handler['handler'](
                    InlineCall(chosen_inline_query, self),
                    query,
                    *input_handler.get("args", [])
                )
            except Exception:
                logging.exception("Chosen inline handler error")
                