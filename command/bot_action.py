from .basic.db import Database
from .basic.chat_keyboards import Keyboard_Manager
from .basic.instance import bot
from .basic.config import admin_id, cur8_channel, report_channel, TEST, domain
from .basic.language import Language
from aiogram.enums import ParseMode
import asyncio
from datetime import datetime
from .basic.hive_request import Blockchain
from .basic.logger_config import logger

class BotCommand:
    def __init__(self):
        self.db = Database()
        self.keyboards = Keyboard_Manager()
        self.beem = Blockchain()

    async def send_post_link(self):
        try:
            while True:
                async for steem_username in self.db.steem_usernames():
                    post_info = self.beem.get_hive_posts(steem_username)
                    link = post_info['result'][0]['url']
                    permlink = post_info['result'][0]['permlink']
                    created = post_info['result'][0]['created']
                    created_time = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S")
                    last_post = self.db.get_user_steem_post(steem_username)
                    if last_post != permlink:
                        category = post_info['result'][0]['category']
                        #url = f'https://steemit.com/{category}/@{steem_username}/{permlink}'
                        url = f'{domain}{link}'
                        await bot.send_message(f"@{cur8_channel}", url)
                        self.db.update_steem_post_and_date(steem_username, permlink, created_time)
                await asyncio.sleep(60)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            await bot.send_message(admin_id, str(ex))

    async def post_programmed(self):
        try:
            while True:
                now = datetime.now().strftime("%Y-%m-%dT%H:%M")
                post_info = self.db.get_program_post_data(now)
                result = self.db.get_all()
                if post_info:
                    user_id = post_info[0]
                    steem_info = self.db.get_user_account(user_id)
                    wif = steem_info[1] # type: ignore
                    author = post_info[2]
                    title = post_info[3]
                    body = post_info[4]
                    tags = post_info[5]
                    community = post_info[6]
                    language_code = self.db.get_language_code(user_id)
                    if not TEST:
                        result = self.beem.pubblica_post(language_code, title=title, body=body, tags=tags, wif=wif, author=author, community=community)
                        await bot.send_message(user_id, result)
                        await asyncio.sleep(20)
                        post_info = self.beem.get_hive_posts(author)
                        link = post_info['result'][0]['url']
                        url = f'{domain}{link}'
                        await bot.send_message(f"@{cur8_channel}", url)
                    else:
                        await bot.send_message(user_id, f"title={title}, body={body}, tags={tags}, wif={wif}, author={author}, community={community}")
                    
                self.db.delete_program_post_data(now)
                await asyncio.sleep(30)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            await bot.send_message(admin_id, str(ex))

    