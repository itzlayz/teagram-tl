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

import asyncio
import functools
import random
import requests
import string
import typing
import yaml
import time
import os
import io
import re
import subprocess

from pathlib import Path

import git
import contextlib
from types import FunctionType
from urllib.parse import urlparse
from typing import Any, List, Literal, Tuple, Union
from telethon import (
    TelegramClient, 
    types, 
    events, 
    hints
)
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    InviteToChannelRequest,
    EditAdminRequest,
    EditPhotoRequest
)
from telethon.types import (
    Channel,
    ChatAdminRights,
    InputPeerNotifySettings,
    UpdateNewChannelMessage
)
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl import custom

from . import database, init_time

Message = Union[custom.Message, types.Message]
git_hash = lambda: git.Repo().head.commit.hexsha
_init_time = init_time
BASE_DIR = (
    "/data"
    if "DOCKER" in os.environ
    else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
BASE_PATH = Path(BASE_DIR)

# from hikka
def escape_html(text: str, /) -> str:  # sourcery skip
    """
    Pass all untrusted/potentially corrupt input here
    :param text: Text to escape
    :return: Escaped text
    """
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# from hikka
def escape_quotes(text: str, /) -> str:
    """
    Escape quotes to html quotes
    :param text: Text to escape
    :return: Escaped text
    """
    return escape_html(text).replace('"', "&quot;")


def get_args(message: Message) -> str:
    return get_full_command(message)

def get_args_raw(message: Message) -> str:
    return get_full_command(message)[2]


def get_full_command(message: Message) -> Union[
    Tuple[Literal[""], Literal[""], Literal[""]], Tuple[str, str, str]
]:
    """
    Extract a tuple of prefix, command, and arguments from the message.

    Parameters:
        message (Message): The message.

    Returns:
        Union[
            Tuple[Literal[""], Literal[""], Literal[""]],
            Tuple[str, str, str]
        ]: A tuple containing the prefix, command, and arguments.

    Example:
        message_text = "/command arg1 arg2"
        message = Message(text=message_text)
        result = get_full_command(message)
        #  result also can be if you didn't set prefix: ("", "command", "arg1 arg2")
        # For the example message_text, result will be: ("/", "command", "arg1 arg2")
    """

    message.text = str(message.text)
    prefixes = database.db.get("teagram.loader", "prefixes", ["."])

    for prefix in prefixes:
        if (
            message.text
            and len(message.text) > len(prefix)
            and message.text.startswith(prefix)
        ):
            command, *args = message.text[len(prefix):].split(maxsplit=1)
            break
    else:
        return "", "", ""

    return prefixes[0], command.lower(), args[-1] if args else ""

def sublist(_list: list, row_length: int = 3) -> list:
    """
    Makes sublist in list
    :param _list: `typing.List`
    :return: List with sublist
    """
    return [_list[i:i + row_length] for i in range(0, len(_list), row_length)]

def get_chat(message: Message) -> typing.Optional[int]:
    """
    Get chat id of message
    :param message: Message to get chat of
    :return: int or None if not present
    """
    return (message.chat.id if message.chat else None or message._chat_peer)

def get_chat_id(message: Message) -> typing.Optional[int]:
    """
    Same as get_chat
    """

    return get_chat(message)

def get_topic(message: Message) -> typing.Optional[int]:
    """
    Get topic id of message
    :param message: Message to get topic of
    :return: int or None if not present
    """
    return (
        (message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id)
        if (
            isinstance(message, Message)
            or isinstance(message, types.Message)
            or isinstance(message, events.NewMessage.Event)
            and message.reply_to
            and message.reply_to.forum_topic
        )
        else None
    )

def strtobool(val):
    # distutils.util.strtobool
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))
    
def validate(attribute):
    """Делает валидацию типа из строки (в int, bool)
        Validation type from string (in int, bool)"""
    if isinstance(attribute, str):
        try:
            attribute = int(attribute)
        except:
            try:
                attribute = bool(strtobool(attribute))
            except:
                pass

    return attribute

# https://github.com/hikariatama/Hikka/blob/master/hikka/_internal.py#L16-L17
async def fw_protect():
    await asyncio.sleep(random.randint(1000, 3000) / 1000)

async def create_group(
    app: TelegramClient,
    title: str,
    description: str,
    megagroup: bool = False,
    broadcast: bool = False
):
    await fw_protect()
    return await app(CreateChannelRequest(title, description, megagroup=megagroup, broadcast=broadcast))

async def invite_inline_bot(
    client: TelegramClient,
    peer: hints.EntityLike,
) -> None:
    """
    Invites inline bot to a chat
    :param client: Client to use
    :param peer: Peer to invite bot to
    :return: None
    :raise RuntimeError: If error occurred while inviting bot
    """

    try:
        await client(InviteToChannelRequest(peer, [client.loader.inline.me.username]))
    except Exception as e:
        raise e

    with contextlib.suppress(Exception):
        await client(
            EditAdminRequest(
                channel=peer,
                user_id=client.loader.inline.me.username,
                admin_rights=ChatAdminRights(ban_users=True),
                rank="Teagram",
            )
        )

async def asset_channel(
    client: TelegramClient,
    title: str,
    description: str,
    *,
    channel: bool = False,
    silent: bool = False,
    archive: bool = False,
    invite_bot: bool = False,
    avatar: typing.Optional[str] = None
) -> typing.Tuple[Channel, bool]:
    """
    Create new channel (if needed) and return its entity
    :param client: Telegram client to create channel by
    :param title: Channel title
    :param description: Description
    :param channel: Whether to create a channel or supergroup
    :param silent: Automatically mute channel
    :param archive: Automatically archive channel
    :param invite_bot: Add inline bot and assure it's in chat
    :param avatar: Url to an avatar to set as pfp of created peer
    :return: Peer and bool: is channel new or pre-existent
    """
    if not hasattr(client, "_channels_cache"):
        client._channels_cache = {}

    if (
        title in client._channels_cache
        and client._channels_cache[title]["exp"] > time.time()
    ):
        return client._channels_cache[title]["peer"], False

    async for d in client.iter_dialogs():
        if d.title == title:
            client._channels_cache[title] = {"peer": d.entity, "exp": int(time.time())}
            if invite_bot:
                if all(
                    participant.id != client.loader.inline.bot_id
                    for participant in (
                        await client.get_participants(d.entity, limit=100)
                    )
                ):
                    await fw_protect()
                    await invite_inline_bot(client, d.entity)

            return d.entity, False

    await fw_protect()

    peer = (
        await client(
            CreateChannelRequest(
                title,
                description,
                megagroup=not channel,
            )
        )
    ).chats[0]

    if invite_bot:
        await fw_protect()
        await invite_inline_bot(client, peer)

    if silent:
        await fw_protect()
        await dnd(client, peer, archive)
    elif archive:
        await fw_protect()
        await client.edit_folder(peer, 1)

    if avatar:
        await fw_protect()
        await set_avatar(client, peer, avatar)

    client._channels_cache[title] = {"peer": peer, "exp": int(time.time())}
    return peer, True

async def dnd(
    client: TelegramClient,
    peer: hints.Entity,
    archive: bool = True,
) -> bool:
    """
    Mutes and optionally archives peer
    :param peer: Anything entity-link
    :param archive: Archive peer, or just mute?
    :return: `True` on success, otherwise `False`
    """
    try:
        await client(
            UpdateNotifySettingsRequest(
                peer=peer,
                settings=InputPeerNotifySettings(
                    show_previews=False,
                    silent=True,
                    mute_until=2**31 - 1,
                ),
            )
        )

        if archive:
            await fw_protect()
            await client.edit_folder(peer, 1)
    except Exception:
        return False

    return True

def check_url(url: str) -> bool:
    """
    Statically checks url for validity
    :param url: URL to check
    :return: True if valid, False otherwise
    """
    try:
        return bool(urlparse(url).netloc)
    except Exception:
        return False

async def set_avatar(
    client: TelegramClient,
    peer: hints.Entity,
    avatar: str,
) -> bool:
    """
    Sets an entity avatar
    :param client: Client to use
    :param peer: Peer to set avatar to
    :param avatar: Avatar to set
    :return: True if avatar was set, False otherwise
    """
    if isinstance(avatar, str) and check_url(avatar):
        f = (
            await run_sync(
                requests.get,
                avatar,
            )
        ).content
    elif isinstance(avatar, bytes):
        f = avatar
    else:
        return False

    await fw_protect()
    res = await client(
        EditPhotoRequest(
            channel=peer,
            photo=await client.upload_file(f, file_name="photo.png"),
        )
    )

    await fw_protect()

    with contextlib.suppress(Exception):
        await client.delete_messages(
            peer,
            message_ids=[
                next(
                    update
                    for update in res.updates
                    if isinstance(update, UpdateNewChannelMessage)
                ).message.id
            ],
        )
    return True

async def answer(
    message: Union[Message, List[Message]],
    response: Union[str, Any],
    photo: bool = False,
    document: bool = False,
    topic: bool = False,
    caption: str = '',
    parse_mode: str = 'html',
    **kwargs
) -> List[Message]:
    """
    Send a response to a message, with optional photo or document attachment.

    Parameters:
        message (Union[Message, List[Message]]): The original message or a list of messages to reply to.
        response (Union[str, Any]): The response to send. It can be a text message, a path to a photo/document, or a file-like object.
        photo (bool, optional): If True, a photo will be sent along with the response. Default is False.
        document (bool, optional): If True, a document will be sent along with the response. Default is False.
        caption (str, optional): Caption for the sent photo or document, if applicable.
        parse_mode (str, optional): Parse mode for formatting text. Default is 'html'.
        **kwargs: Additional keyword arguments for sending messages or files.

    Returns:
        List[Message]: A list of sent messages.

    Example:
        response_text = "Thank you for your message!"
        await utils.answer(message, response_text)
        
        response_image_path = "image.jpg"
        await utils.answer(message, response_image_path, photo=True, caption="Here's an image for you.")
    """
    messages: List[Message] = []
    client: TelegramClient = message._client
    chat = get_chat(message)

    if isinstance(message, list):
        message: Message = message[0]

    if isinstance(response, str) and not photo and not document:
        if len(response) > 4096:
            file = io.BytesIO(response.encode())
            file.name = 'response.txt'

            msg = await client.send_file(
                chat, 
                file,
                caption=f'📁 <b>Сообщение отправлено файлом</b> (<code>{len(response)}/4096</code>)',
                parse_mode='HTML',
                reply_to=(get_topic(message) if topic else message.id),
                **kwargs
            )

            if message.out:
                await message.delete()

        else:
            try:
                msg = await client.edit_message(
                    chat,
                    message.id,
                    response,
                    parse_mode=parse_mode,
                    **kwargs
                )
            except: 
                msg = await message.reply(
                    response, 
                    parse_mode=parse_mode, 
                    reply_to=(get_topic(message) if topic else message.id), 
                    **kwargs
                )

        messages.append(msg)

    if photo or document:       
        messages.append(
            await client.send_file(
                chat, 
                response,
                caption=caption,
                parse_mode=parse_mode,
                reply_to=(get_topic(message) if topic else message.id),
                **kwargs
            )
        )

        if message.out:
            await message.delete()

    return messages

async def invoke_inline(
    message: Message,
    bot_username: str,
    inline_id: str
):
    """
    Invoke an inline query to a bot.

    Args:
        message (Union[Message, List[Message]]): The original message or a list of messages to refer to.
        bot_username (str): The username of the bot to invoke the inline query.
        inline_id (str): The unique identifier of the inline query.

    Returns:
        Awaitable: The result of the invoked inline query.
    """
    client: TelegramClient = message._client
    query: custom.InlineResults = await client.inline_query(bot_username, inline_id)

    return await query[0].click(
        get_chat(message),
        reply_to=message.reply_to_msg_id or None
    )

# https://github.com/hikariatama/Hikka/blob/master/hikka/utils.py#L862-L876
def get_link(user: typing.Union[types.User, types.Channel], /) -> str:
    """
    Get telegram permalink to entity
    :param user: User or channel
    :return: Link to entity
    """
    return (
        f"tg://user?id={user.id}"
        if isinstance(user, types.User)
        else (
            f"tg://resolve?domain={user.username}"
            if getattr(user, "username", None)
            else ""
        )
    )

def run_sync(func: FunctionType, *args, **kwargs) -> asyncio.Future:
    """
    Run a non-async function asynchronously.

    Parameters:
        func (FunctionType): The function to run.
        args (list): Arguments for the function.
        kwargs (dict): Keyword arguments for the function.

    Returns:
        asyncio.Future: A Future object representing the result of the function.

    Example:
        def sync_function(x):
            return x * 2

        async def main():
            result = await run_sync(sync_function, 5)
            print(result)  # Output: 10
    """

    return asyncio.get_event_loop().run_in_executor(
        None, functools.partial(
            func, *args, **kwargs)
    )

def get_ram() -> float:
    """
    Get memory usage in megabytes.

    Returns:
        float: Memory usage in megabytes.
    """
    
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem = process.memory_info()[0] / 2.0**20
        for child in process.children(recursive=True):
            mem += child.memory_info()[0] / 2.0**20
        return round(mem, 1)
    except:
        return 0

def get_cpu() -> float:
    """
    Get CPU usage as a percentage.

    Returns:
        float: CPU usage as a percentage.
    """

    try:
        import psutil

        process = psutil.Process(os.getpid())
        cpu = process.cpu_percent()

        for child in process.children(recursive=True):
            cpu += child.cpu_percent()

        return cpu
    except:
        return 0
    
def get_display_name(entity: Union[types.User, types.Chat]) -> str:
    """
    Get display name of user or chat.

    Returns:
        entity: Union[types.User, types.Chat].
    """
    return (
        getattr(entity, "title", None)
        or entity.first_name
        or ("" + (f" {entity.last_name}" if entity.last_name else ""))
    )

def get_platform() -> str:
    """
    Get the platform information.

    Returns:
        str: Platform information.
    """

    IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")
    IS_CODESPACES = "CODESPACES" in os.environ
    IS_DOCKER = "DOCKER" in os.environ
    IS_GOORM = "GOORM" in os.environ
    IS_WIN = "WINDIR" in os.environ
    IS_ZACHOST = 'ZACHEMHOST' in os.environ
    IS_WSL = 'WSL_DISTRO_NAME' in os.environ

    if IS_TERMUX:
        return "📱 Termux"
    elif IS_DOCKER:
        return "🐳 Docker"
    elif IS_GOORM:
        return "💚 Goorm"
    elif IS_WSL:
        return "🧱 WSL"
    elif IS_WIN:
        return "💻 Windows"
    elif IS_CODESPACES:
        return "👨‍💻 Github Codespaces"
    elif IS_ZACHOST:
        return "❔ Zachemhost"
    else:
        return "🖥️ VDS"

def random_id(length: int = 10) -> str:
    """
    Generate a random ID.

    Parameters:
        length (int): Length of the random ID. Default is 10.

    Returns:
        str: Random ID.
    """

    return "".join(
        random.choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )


def get_langpack() -> Any:
    """
    Get the strings.

    Returns:
        Any: The language pack.
    """
    if not (lang := database.db.get('teagram.loader', 'lang', '')):
        database.db.set('teagram.loader', 'lang', 'en')

        get_langpack()
    else:
        with open(f'teagram/langpacks/{lang}.yml', encoding='utf-8') as file:
            pack = yaml.safe_load(file)

        return pack

def get_distro() -> str:
    '''
    Get linux distribution.

    Returns:
        str: Information about linux distro.
    '''

    result = subprocess.run(["lsb_release","-a"], capture_output=True, text=True)
    info = result.stdout

    pattern = r'Description:\s+(.+)'
    if match := re.search(pattern, info):
        return match.group(1)
    else:
        return





