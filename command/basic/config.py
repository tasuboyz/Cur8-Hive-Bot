import logging

TEST = True

if TEST:
    TOKEN = "6348055484:AAGhOv6sx5B4acQj-XUfRWV3kJz53FvioWs" #TasuAdmin
    log_level = logging.INFO 
    cur8_channel = 'tasu_lessons'
    report_channel = '@tasu_lessons'
else:
    TOKEN = '7247521887:AAH3iQkrzHfHDb7QjwiTYM453vXhNmLuhTk' #token produzione
    log_level = logging.ERROR
    cur8_channel = 'steem_animals'
    report_channel = '@cur8earn'

admin_id = 1026795763

account_creation_channel = -1002247582547

api_base_url = 'http://localhost:8081'  

log_file_path = 'log.txt'  

use_local_api = False  # Set to False if the API is not in local

domain = 'https://peakd.com'