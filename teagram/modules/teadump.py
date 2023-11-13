from .. import loader, utils, __version__
from ..utils import BASE_PATH, BASE_DIR, get_distro
from ..types import Config, ConfigValue

import telethon
import atexit
import logging
import json
import platform

from git import Repo

PATH = f'{BASE_PATH}/dump.json'
REPO = Repo(BASE_DIR)

data = {}
dump = False
logger = logging.getLogger()

def get_token():
    with open(BASE_PATH / "db.json", 'r') as file:
        json_data = json.load(file)
    try:
        if json_data["teagram.bot"]["token"]:
            return True
    except KeyError:
        return False

def get_git_info(commit: bool=False, url: bool=False, branch: bool=False):
    repo = REPO

    if commit:
        return repo.commit()
    if url:
        origin = repo.remotes.origin
        return origin.url
    if branch:
        return repo.active_branch.name
    

@loader.module(name="Dump", author="teagram")
class DumpMod(loader.Module):
    """Makes dump with information"""

    strings = {'name': 'dump'}

    def __init__(self):
        self.config = Config(
            ConfigValue(
                'dump_on_unload',
                'Enables dump on unload',
                False,
                self.get("dump_on_unload"),
                loader.validators.Boolean()
            )
        )

    def gen(self) -> dict:
        ver = ""

        ver = platform.platform() if "windows" in platform.platform() else get_distro()
        return {
            "teagram.token": {
                "token": get_token()
            },
            "teagram.modules": {
                "modules": [mod.name for mod in self.manager.modules]
            },
            "teagram.version": {
                "version":  __version__,
                "telethon": telethon.__version__
            },
            "teagram.platform": {
                "platform": utils.get_platform(),
                "os": ver
            },
            "teagram.git": {
                "url": get_git_info(url=True),
                "commit": str(get_git_info(commit=True)),
                "branch": str(get_git_info(branch=True))
            }
        }  

    async def dump_cmd(self, message):
        result = self.gen()

        with open(PATH, 'w') as f:
            json.dump(result, f, indent=4)

        await utils.answer(
            message,
            PATH,
            document=True,
            caption=self.strings("dumped")
        )
    
    @loader.loop(5, autostart=True)
    async def dumploop(self):
        global data, dump
        result = self.gen()
        data = result 
        dump = self.get("dump_on_unload")
    
    @atexit.register
    def create_dump():
        global data, dump
        
        if dump:
            with open(PATH, 'w') as f:
                json.dump(data, f, indent=4)

            logger.info(f"Dump file created, {PATH}")

