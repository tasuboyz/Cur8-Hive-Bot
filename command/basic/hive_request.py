from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.community import Communities, Community
import requests
import json
from beem.nodelist import NodeList
from beem.exceptions import WrongMasterPasswordException, AccountExistsException
from beem.imageuploader import ImageUploader
from .db import Database
from .instance import bot
from .config import admin_id
from .language import Language
import aiohttp

class Blockchain:
    def __init__(self, mode='irreversible'):
        self.mode = mode
        #self.hive_node = 'https://api.deathwing.me'
        self.hive_node = 'https://api.c0ff33a.uk'
        #self.hive_node = "https://techcoderx.com"
        self.nodelist = NodeList()
        #self.hive = Hive(node=self.nodelist.get_steem_nodes())
        self.hive = Hive(node=self.hive_node)
        self.community = Communities(blockchain_instance=self.hive)
        self.db = Database()
        self.language = Language()

    def get_profile_info(self, username):  
        data = {
        "jsonrpc": "2.0",
        "method": "condenser_api.get_accounts",
        "params": [[username]],
        "id": 1
        }
        response = requests.post(self.hive_node, data=json.dumps(data))
        if response.status_code == 200:
            data = response.json()
            if len(data['result']) > 0:
                return data
            else:
                raise Exception("user not exist")
        else:
            raise Exception(response.reason)
            
    def get_hive_posts(self, username):
        headers = {'Content-Type': 'application/json'}
        data = {
            "jsonrpc": "2.0",
            "method": "condenser_api.get_discussions_by_blog",
            "params": [{"tag": username, "limit": 1}],
            "id": 1
        }
        response = requests.post(self.hive_node, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(response.reason)    
        
    def get_hive_dynamic_global_properties(self):
        headers = {'Content-Type': 'application/json'}
        data = {
            "jsonrpc": "2.0",
            "method": "condenser_api.get_dynamic_global_properties",
            "params": [],
            "id": 1
        }
        response = requests.post(self.hive_node, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(response.reason)    
        
##################################################################################### Community command
        
    def get_hive_community(self, community_name):
        result = self.community.search_title(community_name)
        return result
    
    def get_hive_community_post(self, community):
        community = Community(community, blockchain_instance=self.hive)
        result = community.get_ranked_posts(limit=100)
        return result
    
    def subscribe_community(self, community, username, wif):   
        hive = Hive(keys=[wif], node=self.hive_node)  
        community = Community(community, blockchain_instance=hive)
        result = community.subscribe(username)
        return True

    def unsubscribe_community(self, community, username, wif):        
        hive = Hive(keys=[wif], node=self.hive_node)  
        community = Community(community, blockchain_instance=hive)
        result = community.unsubscribe(username)
        return True

    def get_account_sub(self, username):
        community = []
        account = Account(username, steem_instance=self.hive)
        results = account.list_all_subscriptions()
        for result in results:
            community.append(result[0])
        return community
    
    def create_account(self, new_account_name: str):
        new_account_name = new_account_name.lower()
        url = "http://imridd.eu.pythonanywhere.com/hive/create_account"
        headers = {
            "Content-Type": "application/json",
            "API-Key": "your_secret_api_key"
        }
        data = {
            "new_account_name": new_account_name
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed to create account. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception("failed to create account")
    
    ##########################################################################################
    ##########################################################################################
    
    def pubblica_post(self, language_code, title="", body="", author="", tags="", community='', wif=''):
        beneficiario = [{"account": "micro.cur8", "weight": 500}]
        result = self.get_profile_info(author)   
        hive = Hive(keys=[wif], node=self.hive_node, rpcuser=author)  
        try:
            account = Account(author, steem_instance=hive)
        except Exception as ex:            
            user_not_exist_text = self.language.username_not_exist(language_code)
            return user_not_exist_text
        try:
            posting_key = hive.wallet.getPostingKeyForAccount(author)   
        except:
            return "Posting key Invalid 🚫"
        successfully_published_text = self.language.successfully_published(language_code, title)
        result = hive.post(title=title, body=body, author=author, tags=tags, community=community, beneficiaries=beneficiario)
        return successfully_published_text
    
    def hive_upload_image(self, file_path, username, wif):
        hive = Hive(keys=[wif], node=self.hive_node, rpcuser=username)            
       
        uploader = ImageUploader(blockchain_instance=hive)
        result = uploader.upload(file_path, username)
        return result
    
    def hive_logging(self, language_code, user_id, username, wif):
        username = str(username).lower()
        try:
            hive = Hive(keys=[wif], node=self.hive_node, rpcuser=username) 
        except:
            return "Posting key Invalid 🚫"
        try:
            account = Account(username, steem_instance=hive)
        except Exception as ex:            
            user_not_exist_text = self.language.username_not_exist(language_code)
            return user_not_exist_text
        try:
            user = hive.wallet.getAccountFromPrivateKey(wif)   
            follow_result = account.follow('cur8', what=['blog'], account=None)
        except Exception as ex:   
            print(ex)
            return "Posting key Invalid 🚫"
        try:
            self.db.insert_user_account(user_id, username, wif)
            login_succesful_text = self.language.login_successful(language_code)
            return login_succesful_text
        except Exception as ex:
            return "Login Failed 🚫"
        
    def verify_identity(self, username, wif):
        hive = Hive(node=self.hive_node, rpcuser=username) 
        try:
            account = Account(username, steem_instance=hive)
        except Exception as ex:            
            return "Username not exist 🚫"
        try:
            key_usaname = hive.wallet.getAccountFromPrivateKey(wif)
        except Exception as ex:            
            return "Key not valid 🚫"
        return
    
    def like_post(self, voter, voted, private_posting_key, permlink, weight=20):

        hive = Hive(keys=[private_posting_key], node=self.hive_node, rpcuser=voter) 
        account = Account(voter, blockchain_instance=hive)
        comment = Comment(authorperm=f"@{voted}/{permlink}", blockchain_instance=hive)
        comment.vote(float(weight), account=account)

    def get_permlink(self, post_url):
        hive = Hive(node=self.hive_node) 
        comment = Comment(post_url, blockchain_instance=hive)
        permlink = comment.permlink
        return permlink
    
    def get_author(self, post_url):
        hive = Hive(node=self.hive_node) 
        comment = Comment(post_url, blockchain_instance=hive)
        author = comment.author
        return author