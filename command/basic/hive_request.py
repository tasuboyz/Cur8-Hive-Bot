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
from .instance import bot, hive_node
from .config import admin_id
from .language import Language
import asyncio

import time
from beem import Hive
from beem.nodelist import NodeList

import time
import requests
from beem import Hive
from beem.nodelist import NodeList
from threading import Thread
from beemgraphenebase.account import PrivateKey

class HiveNodeTester:
    def __init__(self, mode='irreversible'):
        self.mode = mode
        self.nodelist = NodeList()
        self.nodelist.update_nodes()
        self.nodes = self.nodelist.get_hive_nodes()
        self.fastest_node = None

    def test_node(self, node):
        try:
            # Effettua una richiesta GET per verificare se il nodo risponde
            response = requests.get(node, timeout=5)
            if response.status_code != 200:
                raise Exception(f"Node {node} returned status code {response.status_code}")
            
            hive = Hive(node=node)
            start_time = time.time()
            hive.get_config()  # Cambiato da get_block a get_config
            end_time = time.time()
            return end_time - start_time
        except Exception as e:
            print(f"Error testing node {node}: {e}")
            return float('inf')

    def find_fastest_node(self):
        fastest_time = float('inf')
        for node in self.nodes:
            response_time = self.test_node(node)
            if response_time < fastest_time:
                fastest_time = response_time
                self.fastest_node = node       
        return self.fastest_node
    
class Blockchain:
    def __init__(self, mode='irreversible'):
        self.mode = mode
        self.nodelist = NodeList()
        self.tester = HiveNodeTester()
        self.db = Database()
        self.language = Language()
        self.update_interval = 600  # Intervallo di aggiornamento in secondi (es. 1 ora)        

    def update_node(self):
        global hive_node
        new_hive_node = self.tester.find_fastest_node()
        hive = Hive(node=hive_node)
        hive_node = new_hive_node
        #print(f"Updated to the fastest node: {hive_node}")

    async def start_periodic_update(self):
        while True:
            await asyncio.sleep(self.update_interval)
            self.update_node()

    def get_profile_info(self, username):  
        data = {
        "jsonrpc": "2.0",
        "method": "condenser_api.get_accounts",
        "params": [[username]],
        "id": 1
        }
        response = requests.post(hive_node, data=json.dumps(data))
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
        response = requests.post(hive_node, headers=headers, data=json.dumps(data))
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
        response = requests.post(hive_node, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(response.reason)    
        
##################################################################################### Community command
        
    def get_hive_community(self, community_name):
        hive = Hive(node=hive_node)  
        community = Communities(blockchain_instance=hive)
        result = community.search_title(community_name)
        return result
    
    def get_hive_community_post(self, community):
        hive = Hive(node=hive_node)  
        community = Community(community, blockchain_instance=hive)
        result = community.get_ranked_posts(limit=100)
        return result
    
    def subscribe_community(self, community, username, wif):   
        hive = Hive(keys=[wif], node=hive_node)  
        community = Community(community, blockchain_instance=hive)
        result = community.subscribe(username)
        return True

    def unsubscribe_community(self, community, username, wif):     
        hive = Hive(keys=[wif], node=hive_node)  
        community = Community(community, blockchain_instance=hive)
        result = community.unsubscribe(username)
        return True

    def get_account_sub(self, username):
        hive = Hive(node=hive_node)  
        community = []
        account = Account(username, steem_instance=hive)
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
        hive = Hive(keys=[wif], node=hive_node, rpcuser=author)  
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
        #print(f"Actual node is: {hive_node}")
        hive = Hive(keys=[wif], node=hive_node, rpcuser=username)            
       
        uploader = ImageUploader(blockchain_instance=hive)
        result = uploader.upload(file_path, username)
        return result
    
    def hive_logging(self, language_code, user_id, username, wif):
        username = str(username).lower()
        try:
            hive = Hive(keys=[wif], node=hive_node, rpcuser=username) 
        except:
            return "Posting key Invalid 🚫"
        try:
            account = Account(username, steem_instance=hive)
        except Exception as ex:            
            user_not_exist_text = self.language.username_not_exist(language_code)
            return user_not_exist_text
        is_posting_key = self.is_posting_key(wif, username)
        if not is_posting_key:
            return "Key is not posting key🚫"
        try:            
            follow_result = account.follow('cur8', what=['blog'], account=None)
        except Exception as ex:              
            return "Posting key Invalid 🚫"
        try:
            self.db.insert_user_account(user_id, username, wif)
            login_succesful_text = self.language.login_successful(language_code)
            return login_succesful_text
        except Exception as ex:
            return "Login Failed 🚫"
        
    def is_posting_key(self, wif, username):
        try:
            hive = Hive(keys=[wif], node=hive_node)
            account = Account(username, blockchain_instance=hive)
            
            # Ottieni la chiave pubblica di posting dall'account
            posting_key = account['posting']['key_auths'][0][0]
            
            # Confronta la chiave pubblica di posting con la chiave privata fornita
            private_key = PrivateKey(wif)
            if str(private_key.pubkey) == posting_key:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
    
    def like_post(self, voter, voted, private_posting_key, permlink, weight=20):
        hive = Hive(keys=[private_posting_key], node=hive_node, rpcuser=voter) 
        account = Account(voter, blockchain_instance=hive)
        comment = Comment(authorperm=f"@{voted}/{permlink}", blockchain_instance=hive)
        comment.vote(float(weight), account=account)

    def get_permlink(self, post_url):
        hive = Hive(node=hive_node) 
        comment = Comment(post_url, blockchain_instance=hive)
        permlink = comment.permlink
        return permlink
    
    def get_author(self, post_url):
        hive = Hive(node=hive_node) 
        comment = Comment(post_url, blockchain_instance=hive)
        author = comment.author
        return author