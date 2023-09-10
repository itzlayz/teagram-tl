import configparser
import logging
import sys

import asyncio

from getpass import getpass
from typing import NoReturn, Tuple, Union

from telethon.password import compute_check
from telethon import TelegramClient, errors, types
from telethon.tl.functions.account import GetPasswordRequest
from telethon.tl.functions.auth import CheckPasswordRequest
from qrcode.main import QRCode

from . import __version__

class Auth:
    def __init__(self, session_name: str = "/teagram") -> None:
        self._check_api_tokens()

        config = configparser.ConfigParser()
        config.read("./config.ini")

        self.app: TelegramClient = TelegramClient(
            session=session_name, app_version=f"v{__version__}",
            api_id=int(config.get('telethon', 'api_id')),
            api_hash=config.get('telethon', 'api_hash')
        )

    def _check_api_tokens(self) -> bool:
        config = configparser.ConfigParser()
        if not config.read("./config.ini"):
            config["telethon"] = {
                "api_id": input("Enter API id: "),
                "api_hash": input("Enter API hash: ")
            }

            with open("./config.ini", "w") as file:
                config.write(file)
        
        return True

    async def _2fa(self) -> str:
        password = await self.app(GetPasswordRequest()) 
        
        while True:
            twofa = getpass('Enter 2FA password: ')
            try:
                await self.app._on_login(
                    (
                        await self.app(
                            CheckPasswordRequest(
                                compute_check(password, twofa.strip())
                            )
                        )
                    ).user
                )
            except errors.PasswordHashInvalidError:
                logging.error('Wrong password!')
            else:
                return twofa

    async def send_code(self) -> Tuple[str, str]:
        """Enter phone number"""
        while True:
            error_text: str = ""

            try:
                phone = input("Enter phone number: ")
                return phone, (await self.app.send_code_request(phone, _retry_count=5)).phone_code_hash
            except errors.PhoneNumberInvalidError:
                error_text = "Invalid phone number, please try again"
            except errors.PhoneNumberBannedError:
                error_text = "Phone number blocked"
            except errors.PhoneNumberFloodError:
                error_text = "On the phone number floodwait"
            except errors.PhoneNumberUnoccupiedError:
                error_text = "Number not registered"
            except errors.BadRequestError as error:
                error_text = f"An unknown error has occurred: {error}"

            if error_text:
                logging.error(error_text)

    async def enter_code(self, phone: str, phone_code_hash: str) -> types.User:
        """Login in account"""
        
        code = input("Enter confirmation code: ")

        try:
            user = await self.app.sign_in(
                phone,
                code,
                phone_code_hash=phone_code_hash
            )

            return user
        except errors.SessionPasswordNeededError:
            twofa = await self._2fa()

            return await self.app.sign_in(
                phone,
                code,
                password=twofa,
                phone_code_hash=phone_code_hash
            ) 


    async def authorize(self) -> Union[Tuple[types.User, TelegramClient], NoReturn]:
        """Account authorization process"""
        await self.app.connect()

        try:
            me = await self.app.get_me() 
            if not me:
                raise errors.AuthKeyUnregisteredError('?')
        except errors.AuthKeyUnregisteredError:
            qr = input("Login by QR-CODE? y/n ").lower().split()

            if qr[0] == "y":
                tries = 0
                while True:                    
                    try:
                        qrcode = await self.app.qr_login()
                    except errors.UnauthorizedError:                        
                        break

                    if isinstance(qrcode, types.auth.LoginTokenSuccess):
                        break
                    if tries % 30 == 0:
                        print('Settings > Devices > Scan QR Code (or Add device)\n')
                        print('Scan QR code below:' )

                        await qrcode.recreate()
                        qr = QRCode()
                        
                        qr.clear()
                        qr.add_data(qrcode.url)
                        qr.print_ascii()
                    
                    tries += 1
                    await asyncio.sleep(1)
                
                await self._2fa()

                me = await self.app.get_me() 
                    
            else:
                phone, phone_code_hash = await self.send_code() 
                await self.enter_code(phone, phone_code_hash)
                
                me: types.User = await self.app.get_me() 
        except errors.SessionRevokedError:
            logging.error("The session was terminated, delete the session and re-auth")
            self.app.disconnect()

            return sys.exit(64)
        return me, self.app
