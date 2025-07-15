import os
import csv

USERS_CSV = os.path.join(os.path.dirname(__file__), 'users.csv')

# make sure the users.csv file exists with headers
if not os.path.exists(USERS_CSV):
    with open(USERS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'email'])

def register_user(username: str, email: str) -> bool:
    """register a new user. returns True if successful, false if user exists."""
    with open(USERS_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                return False  # user already exists
    with open(USERS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username, email])
    return True

def authenticate_user(username: str) -> bool:
    """authenticate a user by username only. returns True if user exists."""
    with open(USERS_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                return True
    return False

def get_users_list():
    users = []
    with open(USERS_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row['username'])
    return users

def get_users_table():
    users = []
    with open(USERS_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append({'username': row['username'], 'email': row['email']})
    return users 