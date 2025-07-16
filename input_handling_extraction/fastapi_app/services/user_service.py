import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_persistence import simple_user_system

class UserService:
    def register_user(self, username: str, email: str) -> bool:
        """register a new user"""
        return simple_user_system.register_user(username, email)
    
    def authenticate_user(self, username: str) -> bool:
        """authenticate a user"""
        return simple_user_system.authenticate_user(username) 
    
    def get_users_list(self):
        """get list of all usernames"""
        return simple_user_system.get_users_list() 
    
    def get_users_table(self):
        return simple_user_system.get_users_table() 