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

from types import FunctionType
from typing import Any, Dict, List, Union, Callable, Tuple

from telethon import TelegramClient, types

from .validators import Integer, String, Boolean, ValidationError, Validator

from ast import literal_eval
from dataclasses import dataclass, field

from html.parser import HTMLParser

from telethon.helpers import add_surrogate, del_surrogate, strip_text
from telethon.extensions.html import HTMLToTelegramParser, unparse

from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityEmail,
    MessageEntityUrl,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityCustomEmoji,
    TypeMessageEntity,
)


class Module:
    name: str
    author: str
    version: Union[int, float]
    warning: str

    async def on_load(self) -> Any: ...

    async def on_unload(self) -> Any: ...

    async def client_ready(self, client, db): ...

    def get(self, key: str, default: Any = None) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...


class ModulesManager:
    """Manager of modules"""

    def __init__(self, client: TelegramClient, db, me: types.User) -> None:
        self.modules: List[Module]
        self.watcher_handlers: List[FunctionType]

        self.command_handlers: Dict[str, FunctionType]
        self.message_handlers: Dict[str, FunctionType]
        self.inline_handlers: Dict[str, FunctionType]
        self.callback_handlers: Dict[str, FunctionType]
        self.loops: List[FunctionType]

        self._local_modules_path: str = "./teagram/modules"

        self._client: TelegramClient
        self._db
        self.me: types.User
        self.warnings: List[str]

        self.aliases: dict
        self.strings: dict
        self.translator
        self.core_modules: List[str]

        self.dp
        self.inline
        self.bot_manager


class WaitForDefault:
    pass


@dataclass
class ConfigValue:
    option: str
    doc: str = ""
    default: Any = None
    value: Any = field(default_factory=WaitForDefault)
    validator: Union[Integer, String, Boolean] = None

    def __post_init__(self):
        if isinstance(self.value, WaitForDefault) or not self.value:
            self.value = self.default

    def __setattr__(self, key: str, value: Any):
        if self.validator:
            try:
                value = self.validator._valid(value)
            except ValidationError:
                value = self.default
            except TypeError:
                value = self.validator._valid(
                    value, validator=self.validator._validator
                )

        if isinstance(value, (tuple, list, dict)):
            raise ValidationError(
                "Неправильный тип (Проверьте типы валидаторов) / Invalid type (Check validator types)"
            )

        object.__setattr__(self, key, value)


@dataclass(repr=True)
class HikkaValue:
    option: str
    default: Any = None
    doc: Union[Callable[[], str], str] = None
    value: Any = field(default_factory=WaitForDefault)
    validator: Validator = None

    def __post_init__(self):
        if isinstance(self.value, WaitForDefault):
            self.value = self.default

    def set_no_raise(self, value: Any) -> bool:
        """
        Sets the config value w/o ValidationError being raised
        Should not be used uninternally
        """
        return self.__setattr__("value", value, ignore_validation=True)

    def __setattr__(
        self,
        key: str,
        value: Any,
        *,
        ignore_validation: bool = False,
    ):
        if key == "value":
            try:
                value = literal_eval(value)
            except Exception:
                pass

            # Convert value to list if it's tuple just not to mess up
            # with json convertations
            if isinstance(value, (set, tuple)):
                value = list(value)

            if isinstance(value, list):
                value = [
                    item.strip() if isinstance(item, str) else item for item in value
                ]

            if self.validator:
                if value:
                    from . import validators

                    try:
                        value = self.validator._valid(value)
                    except validators.ValidationError as e:
                        if not ignore_validation:
                            raise e

                        value = self.default
                    except TypeError:
                        value = self.validator._valid(
                            value, validator=self.validator._validator
                        )

        object.__setattr__(self, key, value)


class Config(dict):
    def __init__(self, *values: List[ConfigValue]):
        if all(isinstance(value, (ConfigValue, HikkaValue)) for value in values):
            self.config = {config.option: config for config in values}
        else:
            keys, defaults, docstrings = values[::3], values[1::3], values[2::3]

            self.config = {
                key: ConfigValue(option=key, default=default, doc=doc)
                for key, default, doc in zip(keys, defaults, docstrings)
            }

        super().__init__(
            {option: config.value for option, config in self.config.items()}
        )

    def get_default(self, key: str) -> str:
        return self.config[key].default

    def get_doc(self, key: str) -> Union[str, None]:
        return self.config[key].doc

    def __getitem__(self, key: str) -> Any:
        try:
            return self.config[key].value
        except KeyError:
            return None

    def reload(self):
        for key in self.config:
            super().__setitem__(key, self.config[key].value)


class CustomHTMLParser(HTMLToTelegramParser):
    """telethon.extensions.html with premium emojis"""

    def __init__(self, *args):
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self._open_tags.appendleft(tag)
        self._open_tags_meta.appendleft(None)

        attrs = dict(attrs)
        EntityType = None
        args = {}
        if tag == "strong" or tag == "b":
            EntityType = MessageEntityBold
        elif tag == "em" or tag == "i":
            EntityType = MessageEntityItalic
        elif tag == "u":
            EntityType = MessageEntityUnderline
        elif tag == "del" or tag == "s":
            EntityType = MessageEntityStrike
        elif tag == "blockquote":
            EntityType = MessageEntityBlockquote
        elif tag == "code":
            try:
                pre = self._building_entities["pre"]
                try:
                    pre.language = attrs["class"][len("language-") :]
                except KeyError:
                    pass
            except KeyError:
                EntityType = MessageEntityCode
        elif tag == "pre":
            EntityType = MessageEntityPre
            args["language"] = ""
        elif tag == "a":
            try:
                url = attrs["href"]
            except KeyError:
                return
            if url.startswith("mailto:"):
                url = url[len("mailto:") :]
                EntityType = MessageEntityEmail
            else:
                if self.get_starttag_text() == url:
                    EntityType = MessageEntityUrl
                else:
                    EntityType = MessageEntityTextUrl
                    args["url"] = del_surrogate(url)
                    url = None
            self._open_tags_meta.popleft()
            self._open_tags_meta.appendleft(url)
        elif tag == "emoji":
            EntityType = MessageEntityCustomEmoji
            args["document_id"] = int(attrs["document_id"])

        if EntityType and tag not in self._building_entities:
            self._building_entities[tag] = EntityType(
                offset=len(self.text),
                length=0,
                **args,
            )


def parse(html: str) -> Tuple[str, List[TypeMessageEntity]]:
    """
    EDITED `telethon.extensions.html.parse`

    Parses the given HTML message and returns its stripped representation
    plus a list of the MessageEntity's that were found.

    :param html: the message with HTML to be parsed.
    :return: a tuple consisting of (clean message, [message entities]).
    """
    if not html:
        return html, []

    parser = HTMLParser()
    parser.feed(add_surrogate(html))
    text = strip_text(parser.text, parser.entities)
    return del_surrogate(text), parser.entities


HTMLParser = CustomHTMLParser  # noqa: F811

HTMLParser.parse = parse
HTMLParser.unparse = unparse
