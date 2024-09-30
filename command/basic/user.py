from aiogram import types, Bot
from .db import Database

class UserInfo:
    def __init__(self, data):
        if isinstance(data, types.Message):
            user = data.from_user
            self.chat_id = data.chat.id
            self.message_id = data.message_id
            self.text= data.text
        elif isinstance(data, types.CallbackQuery):
            user = data.from_user
            self.chat_id = data.message.chat.id # type: ignore
            self.message_id = data.message.message_id # type: ignore
            self.user_data = data.data
            self.text= data.message.text # type: ignore
        else:
            return None

        self.user_id = user.id # type: ignore
        self.first_name = user.first_name # type: ignore
        self.last_name = user.last_name # type: ignore
        self.username = user.username # type: ignore
        self.setting = Database().get_language_code(self.user_id)
        if self.setting == None:
            self.language = user.language_code # type: ignore
        else:
            self.language = self.setting
        
    async def get_user_member(self, user_id, bot: Bot):
        chat_id= "YOUR_CHANNEL"
        user_count = await bot.get_chat_member(chat_id, user_id)
        return user_count.status
