from .basic.user import UserInfo
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, InlineQuery
from aiogram.fsm.context import FSMContext
from .basic.memory import Form
import asyncio
from .basic.logger_config import logger
from datetime import datetime, timedelta
from .basic.db import Database
from .basic.chat_keyboards import Keyboard_Manager
from .basic.hive_request import Blockchain
from .basic.instance import bot
from .basic.config import admin_id, cur8_channel, report_channel, account_creation_channel, domain
from .basic import inline
import json
from aiogram.enums import ParseMode
from .basic.image import FileManager, FileInfo
from .basic.language import Language
from .admin_panel import Admin_Commands
from .basic.limiter import RateLimiter
import os
import re

class User_Commands:
    def __init__(self):
        self.db = Database()
        self.keyboards = Keyboard_Manager()
        self.beem = Blockchain()
        self.image = FileManager()
        self.language = Language()
        self.admin_command = Admin_Commands()
        self.limiter = RateLimiter()

    async def command_start_handler(self, message: Message):
        info = UserInfo(message)
        chat_id = info.chat_id
        user_id = info.user_id
        username = info.username
        language_code = info.language
        first_name = info.first_name
        try:
            welcame_text = self.language.welcome_message(first_name, language_code)
            self.db.insert_user_data(user_id=user_id, username=username)
            keyboard = self.keyboards.create_start_reply_keyboard(message)
            await message.answer(welcame_text, reply_markup=keyboard)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            await message.reply(str(ex))

    async def search_community(self, message: Message, state: FSMContext):        
        # await state.set_state(Form.set_community)
        info = UserInfo(message)
        language_code = info.language
        try:
            filter_text = self.language.click_filter_community(language_code)
            keyboard = self.keyboards.search_community(message)
            await message.reply(filter_text, reply_markup=keyboard)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            await message.reply(str(ex))

    async def view_selected_community(self, message: Message, state: FSMContext):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        await state.clear()
        community = message.text
        await state.set_data(data=[community]) # type: ignore
        result = self.db.get_user_account(user_id)
        if result:
            account = result[0]
            account_sub = self.beem.get_account_sub(account)
        else:
            account_sub = None        
        keyboard = self.keyboards.view_community_post(community, language_code, account_sub)
        await message.send_copy(user_id, reply_markup=keyboard)    

    async def recive_web_data(self, message: Message, state: FSMContext):
        info = UserInfo(message)
        user_id = info.user_id
        message_id = info.message_id 
        chat_id = info.chat_id
        language_code = info.language
        try:
            data = json.loads(message.web_app_data.data) # type: ignore ##get data responce
            if 'title' in data:
                
                result = self.db.get_user_account(user_id)
                
                title = data['title']
                body = data['description']
                tags = data['tag']
                date_time = data['dateTime']
                communityId = data['communityId']
                if result:
                    wif = result[1]
                    author = result[0]
                    if date_time == '':                        
                        result = self.beem.pubblica_post(language_code, title=title, body=body, tags=tags, wif=wif, author=author, community=communityId)
                        await message.answer(result)
                        await asyncio.sleep(20)
                        post_info = self.beem.get_hive_posts(author)
                        link = post_info['result'][0]['url']
                        permlink = post_info['result'][0]['permlink']
                        url = f'{domain}{link}'
                        keyboard = self.keyboards.give_like()
                        send_data = await bot.send_message(f"@{cur8_channel}", url, reply_markup=keyboard)
                        await asyncio.sleep(2)
                        channel_link = f'<a href="https://t.me/{cur8_channel}/{send_data.message_id}">💣</a>'
                        await bot.send_message(user_id, channel_link)
                    else:
                        self.db.insert_program_post_data(user_id, date_time, author, title, body, tags, communityId)
                        post_saved_message_text = self.language.post_saved_message(language_code, date_time)
                        await message.answer(post_saved_message_text)
            elif 'wif' in data:                
                author = data['account']
                wif = data['wif']
                result = self.beem.hive_logging(language_code, user_id, author, wif)
                account_logged_text = self.language.login_successful(language_code)
                if result == account_logged_text:
                    keyboard = self.keyboards.create_start_reply_keyboard(message)
                else:                   
                    keyboard = None
                await message.reply(result, reply_markup=keyboard)
            else:
                choose_community_text = self.language.choose_community(language_code)
                keyboard = self.keyboards.search_community(message)
                await state.set_state(Form.set_community)
                await message.answer(choose_community_text, reply_markup=keyboard)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            await message.answer(str(ex))
            await bot.send_message(admin_id, f"{str(ex)}")
        finally:
            await state.clear()

    async def bot_added(self, chatmember: ChatMemberUpdated):
        new_members = chatmember.new_chat_member
        chat_info = chatmember.chat
        channel_id = chat_info.id
        try:
            result = await bot.get_chat_administrators(channel_id)
            for user in result:
                user_info = user.user
                if not user_info.is_bot:
                    admin_user_id = user.user.id
                    self.db.insert_user_channel(channel_id, admin_user_id)
        except Exception as ex:
            logger.error(ex, exc_info=True)
            await bot.send_message(admin_id, str(ex))

    async def bot_leaved(self, chatmember: ChatMemberUpdated):
        new_members = chatmember.new_chat_member
        chat_info = chatmember.chat
        channel_id = chat_info.id
        self.db.delate_channel_id(channel_id)

    async def inline_query_handler(self, query: InlineQuery, state: FSMContext):
        await asyncio.sleep(2)
        inline_results = []
        user_id = query.from_user.id
        result = query.query
        try:
            if result.startswith('community'):
                result = result.split(':')[1]               
                offset = int(query.offset or "0")
                await state.set_state(Form.set_community)
                inline_results, next_offset = inline.search_community(result.strip(), offset) # type: ignore
                await query.answer(inline_results, next_offset=next_offset)
            elif result.startswith('view post'):
                result = result.split(':')[1]
                offset = int(query.offset or "0")
                inline_results, next_offset = inline.view_communit_post(result.strip(), offset) # type: ignore
                await query.answer(inline_results, next_offset=next_offset)
        except Exception as ex:
            await bot.send_message(admin_id, str(ex))
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)    
    
    async def recive_istruction(self, callback_query: CallbackQuery):
        info = UserInfo(callback_query)
        user_id = info.user_id
        language_code = info.language
        keyboard = self.keyboards.create_post(language_code)       
        send_post_text = self.language.send_post(language_code)
        try:
            await callback_query.message.answer(send_post_text, reply_markup=keyboard) # type: ignore
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def recive_image(self, message: Message):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        try:                       
            if self.limiter.recive_byte_limit(user_id, max_actions=1, period=5):
                wait_sub_unsub_text = self.language.wait_reciving_image(language_code, 5)
                await message.answer(wait_sub_unsub_text)
                return
            result = self.db.get_user_account(user_id)
            if result:
                waiting_text = self.language.waiting(language_code)
                # Inizia a mostrare l'azione "typing"
                typing_task = asyncio.create_task(self.keep_typing(info.chat_id))
                
                download_path, file_name = await self.image.recive_image(message) # type: ignore
                if file_name is None:
                    await message.answer(download_path)
                    return
                file_info = FileInfo(file_name)
                extention = file_info.extention
                account = result[0]
                wif = result[1]
                account = str(account).lower()
                link = self.beem.hive_upload_image(download_path, account, wif)
                image_url = f"{link['url']}.{extention}"
                format = f"<a href='{image_url}'>🔗 link</a> <pre language='c++'>{image_url}</pre>"
                await message.answer(format)              
                
                os.remove(download_path)  # Elimina il file
            else:
                login_to_save_text = self.language.login_for_save_document(language_code)
                await message.reply(login_to_save_text)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, str(ex))
            await message.answer(str(ex))         
        finally:
                typing_task.cancel()

    async def keep_typing(self, chat_id):
        while True:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(5)  # Attendi 5 secondi prima di inviare di nuovo l'azione "typing"

    async def set_language(self, message: Message):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        set_language_text = self.language.language_setting(language_code)
        keyboard = self.keyboards.language_setting()        
        try:
            await message.reply(set_language_text, reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def language_settend(self, callback_query: CallbackQuery):
        info = UserInfo(callback_query)
        user_id = info.user_id
        message_id = info.message_id
        data = info.user_data       
        try:
            language_code = data.split(':')[1].strip() # type: ignore
            self.db.insert_language(user_id, language_code)
            language_choosed = self.language.language_setted(language_code)
            await callback_query.message.edit_text(language_choosed) # type: ignore
            keyboard = self.keyboards.create_start_reply_keyboard(callback_query)
            await callback_query.message.answer("🚀🚀🚀", reply_markup=keyboard) # type: ignore
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def cancel_operation(self, callback_query: CallbackQuery):
        info = UserInfo(callback_query)
        user_id = info.user_id
        language_code = info.language
        try:
            cancel_text = self.language.operation_deleted(language_code)
            await callback_query.message.edit_text(cancel_text) # type: ignore
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def recive_post_link(self, message: Message):
        info = UserInfo(message)
        user_id = info.chat_id
        message_id = message.message_id
        url = message.text
        try:  
            # result = self.extract_username(url)
            # keyboard = self.keyboards.give_like(result)
            keyboard = self.keyboards.post_link(url)
            await bot.delete_message(user_id, message_id)
            await message.send_copy(user_id, reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    def extract_username(self, url):
        match = re.search(r'(@[^/]+/.+)', url)
        if match:
            return match.group(1)
        return None
    
    async def like(self, callback_query: CallbackQuery):
        info = UserInfo(callback_query)
        user_id = info.user_id
        language_code = info.language
        try:    
            data = callback_query.data
            url = callback_query.message.html_text # type: ignore
            permlink = self.beem.get_permlink(url)
            author = self.beem.get_author(url)
            if data is None:
                raise ValueError("Data is None")
            count = data.split(":")[1].strip()
            
            result = self.db.get_user_account(user_id)
            
            if result is None:
                raise ValueError("L'account utente non è stato trovato nel database.")
            
            voter = result[0]
            wif = result[1]
            
            if not voter or not wif:
                raise ValueError("Nome utente o chiave privata non validi.")
            
            vote_power = self.db.get_user_power_vote(user_id)
            if vote_power:
                self.beem.like_post(voter, author, wif, permlink, vote_power)
            else:
                self.beem.like_post(voter, author, wif, permlink)
            self.beem.like_post(voter, author, wif, permlink)
            upvoted = self.language.upvoted(language_code, 100, permlink)
            count = int(count) + 1
            await callback_query.answer(upvoted)
            keyboard = self.keyboards.give_like(count)
            await callback_query.message.edit_reply_markup(reply_markup=keyboard) # type: ignore
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di like: {ex}", exc_info=True)
            await callback_query.answer(f"{ex}")
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def settings_list(self, message: Message):
        info = UserInfo(message)
        user_id = info.chat_id
        language_code = info.language
        keyboard = self.keyboards.setting_list(message)
        choose_text = self.language.choose_option(language_code)      
        try:
            await message.reply(choose_text, reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")   

    async def recive_username(self, message: Message, state: FSMContext):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        await state.set_state(Form.set_username)
        try:
            send_me_username = self.language.send_me_username(language_code)
            await message.answer(send_me_username)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")     

    async def notify_new_account(self, message: Message, state: FSMContext):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        new_account_name = message.text
        new_account_name = new_account_name.lower()
        tg_username = info.username
        wait_for_account_text = self.language.wait_for_account(language_code)
        await state.clear()
        try:
            result = self.beem.create_account(new_account_name)
            if result:
                if 'keys' in result:
                    keys = result['keys']

                    text = (
                    f"{str(result['message'])}\n\n"
                    "Keys:\n"
                    f'Active Key: <code>{keys["active_key"]}</code>\n'
                    f'Master Key: <code>{keys["master_key"]}</code>\n'
                    f'Memo Key: <code>{keys["memo_key"]}</code>\n'
                    f'Owner Key: <code>{keys["owner_key"]}</code>\n'
                    f'Posting Key: <code>{keys["posting_key"]}</code>\n'
                    # f"Status: {result['status']}"
                )
                    self.db.insert_user_account(user_id, new_account_name, keys["posting_key"])
                    await bot.send_message(account_creation_channel, f"@{tg_username} ha creato l'account steem: {new_account_name}")
                else:
                    result = {(result['message'])}
                    text= str(result)
                    await bot.send_message(account_creation_channel, f"@{tg_username} ha tentato di creare l'account steem: {new_account_name}, errore: {text}")
                await message.answer(text)                       
            # await bot.send_message(admin_id, new_account_name, reply_markup=keyboard)
            # await bot.send_message(account_creator, new_account_name, reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")   

    async def back(self, message: Message):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        keyboard = self.keyboards.create_start_reply_keyboard(message)
        back_text = self.language.back(language_code)
        try:
            await message.answer(back_text, reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}") 

    async def send_tutorial(self, message: Message):
        info = UserInfo(message)
        user_id = info.user_id
        language_code = info.language
        url = 'https://telegra.ph/Bot-Tutorial-07-27'
        recive_url_tutorial = 'https://cdn.steemitimages.com/DQme5voqKuhNu9aJGuVRuvZwztgFRniKUcgAJS3EA6ECJNC/image.mp4'
        fromat = f"<a href='{url}'>View tutorial 👨‍🏫</a>"
        video_tutorial = f"<a href='{recive_url_tutorial}'>View tutorial 👨‍🏫</a>"
        keyboard = self.keyboards.open_copilot(language_code)
        try:
            await message.answer(fromat)
            await message.answer(video_tutorial)
            await message.answer("ask to copilot", reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}") 

    async def sub_unsub(self, callback_query: CallbackQuery):
        info = UserInfo(callback_query)
        user_id = info.user_id
        data = callback_query.data
        language_code = info.language
        message_id = info.message_id
        community = callback_query.message.html_text # type: ignore
        try:
            if self.limiter.is_limited(user_id, message_id, max_actions=1, period=60):
                wait_sub_unsub_text = self.language.wait_sub_unsub(language_code)
                await callback_query.answer(wait_sub_unsub_text)
                return         
            result = self.db.get_user_account(user_id)
            if result:
                account = result[0]
                wif = result[1]
                status = data.split(':')[1] # type: ignore
                account_sub = self.beem.get_account_sub(account)
                subscribed_text = self.language.subscribed_message(language_code)
                unsubscribed_text = self.language.unsubscribed_message(language_code)
                if status == 'sub':
                    self.beem.subscribe_community(community, account, wif)
                    await callback_query.answer(subscribed_text)
                    account_sub.append(community)
                elif status == 'unsub':
                    self.beem.unsubscribe_community(community, account, wif)
                    await callback_query.answer(unsubscribed_text)                
                    account_sub.remove(community)
                keyboard = self.keyboards.view_community_post(community, language_code, account_sub)
                await callback_query.message.edit_reply_markup(reply_markup=keyboard) # type: ignore
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def choose_vote_power(self, message: Message):
        info = UserInfo(message)
        user_id = info.user_id
        try:
            keyboard = self.keyboards.set_voting_power()
            await message.answer("Set your voting power", reply_markup=keyboard)
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di like: {ex}", exc_info=True)
            await message.answer(f"{ex}")
            await bot.send_message(admin_id, f"{user_id}:{ex}")

    async def set_voting_power(self, callback_query: CallbackQuery):
        info = UserInfo(callback_query)
        user_id = info.user_id
        data = callback_query.data
        try:
            vote_power = data.split(":")[1] # type: ignore
            self.db.insert_user_power_vote(user_id, vote_power)
            await callback_query.answer(f"Setted to {vote_power}")
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione di like: {ex}", exc_info=True)
            await callback_query.answer(f"{ex}")
            await bot.send_message(admin_id, f"{user_id}:{ex}")
