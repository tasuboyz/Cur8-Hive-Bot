from bot import BOT

import asyncio
from command.basic.logger_config import logger
from command.basic.ascii import art
from command.basic.db import Database
from command.basic.instance import bot
from command.bot_action import BotCommand
from datetime import datetime

process = True

my_bot = BOT()

async def on_start():
    Database().create_table()
    await bot.delete_webhook()  
    my_bot.test_node()
    
    print(f"{art}")    
    # while process:
    #     with open('log_file.txt', 'w') as f:
    #         now = datetime.now()
    #         f.write(now.strftime('%Y-%m-%d %H:%M:%S'))
    #     await asyncio.sleep(10)

async def on_stop():
    process = False
    print("Bot stoped")

async def main():
    try:               
        command = BotCommand()
        asyncio.create_task(on_start())
        asyncio.create_task(command.post_programmed())
        await my_bot.dp.start_polling(bot)
    except Exception as ex:
        logger.error(f"Errore durante l'esecuzione di handle_set_state: {ex}", exc_info=True)
    except KeyboardInterrupt:
        print("Interrotto dall'utente")
    finally:
        await on_stop()
        
if __name__ == '__main__':   
    asyncio.run(main())
