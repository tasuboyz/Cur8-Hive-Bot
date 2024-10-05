from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo

from aiogram import F, Bot, Dispatcher, Router, types

from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, IS_ADMIN
from command.admin_panel import Admin_Commands
from command.user_commands import User_Commands

import asyncio
from datetime import datetime
from command.basic.memory import Form
from command.basic.language import Language
from command.basic.hive_request import HiveNodeTester, Blockchain
from command.basic.instance import hive_node
from command.basic.db import Database
class BOT():
    def __init__(self):
        self.dp = Dispatcher()
        self.admin_command = Admin_Commands()
        self.command = User_Commands()
        self.language = Language()
        self.tester = HiveNodeTester()

        #admin command
        self.dp.message(Command('user'))(self.admin_command.admin_panel_commands)  
        self.dp.callback_query(F.data == "users")(self.admin_command.process_callback_view_users) 
        self.dp.callback_query(F.data == "steem_user")(self.admin_command.process_callback_view_steem_users) 
        self.dp.callback_query(F.data == "clean")(self.admin_command.clean_inactive_users) 
        self.dp.callback_query(F.data == 'save_steem_username')(self.admin_command.send_me_username)
        self.dp.message(Form.set_steem_username)(self.admin_command.save_steem_account)
        self.dp.callback_query(lambda c: c.data == 'ads')(self.admin_command.recive_ads)
        self.dp.message(Form.set_ads)(self.admin_command.send_ads)
        self.dp.message(Form.set_username)(self.command.notify_new_account)

        #command
        self.dp.message(CommandStart())(self.command.command_start_handler)   
        self.dp.message(Command('help'))(self.command.send_tutorial)
        self.dp.callback_query(lambda c: c.data == 'instruction')(self.command.recive_istruction)       
        self.dp.message(F.web_app_data)(self.command.recive_web_data)
        self.dp.message(F.photo | F.animation | F.video)(self.command.recive_image)
        self.dp.callback_query(F.data.startswith('community'))(self.command.sub_unsub)
        self.dp.callback_query(F.data.startswith('❤️'))(self.command.like)
        
        self.dp.callback_query(F.data == 'cancel')(self.command.cancel_operation)
        self.dp.callback_query(F.data.startswith('code'))(self.command.language_settend)
        self.dp.message(F.text.startswith('https://peakd.com/'))(self.command.recive_post_link)
        self.dp.callback_query(F.data.startswith('voting:'))(self.command.set_voting_power)  

        #reply command
        self.dp.message(F.text.in_(self.language.get_language_list()))(self.command.set_language)
        self.dp.message(F.text.in_(self.language.get_setting_list()))(self.command.settings_list)
        self.dp.message(F.text.in_(self.language.get_create_account_list()))(self.command.recive_username)
        self.dp.message(F.text.in_(self.language.get_back_list()))(self.command.back)
        self.dp.message(F.text.in_(self.language.get_vote_weight()))(self.command.choose_vote_power)

        #serch community
        self.dp.inline_query()(self.command.inline_query_handler)
        self.dp.message(F.text.in_(self.language.get_community_search_list()))(self.command.search_community)
        self.dp.message(F.text.startswith('hive'))(self.command.view_selected_community)

        #manage channel
        self.dp.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_ADMIN))(self.command.bot_added)
        self.dp.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))(self.command.bot_leaved)       

    def test_node(self):
        global hive_node
        node = self.tester.find_fastest_node()
        #print(f"The fastest node is: {node}")
        hive_node = node
        hive = Blockchain()
        asyncio.create_task(hive.start_periodic_update())
        return hive_node