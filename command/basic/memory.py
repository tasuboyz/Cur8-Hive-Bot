from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    set_repair = State()
    set_ads = State()
    set_username = State()
    set_community = State()
    set_keys = State()
    set_steem_username = State()