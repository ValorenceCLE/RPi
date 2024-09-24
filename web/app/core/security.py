import os
import json 
from passlib.context import CryptContext # type: ignore
from typing import Dict
from core.config import settings
from fastapi import Request # type: ignore


# Initialize the hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def load_hashed_passwords() -> Dict[str, str]:
    if os.path.exists(settings.HASHED_PASSWORDS_FILE):
        with open(settings.HASHED_PASSWORDS_FILE, 'r') as file:
            hashed_passwords = json.load(file)
    else:
        ADMIN_USERNAME = settings.ADMIN_USERNAME
        ADMIN_PASSWORD = settings.ADMIN_PASSWORD
        USER_USERNAME = settings.USER_USERNAME
        USER_PASSWORD = settings.USER_PASSWORD
        
        if not all([ADMIN_USERNAME, ADMIN_PASSWORD, USER_USERNAME, USER_PASSWORD]):
            raise ValueError("Incomplete credentials in auth file")
        
        # Hash the passwords
        hashed_passwords = {
            "ADMIN_USERNAME": ADMIN_USERNAME,
            "ADMIN_PASSWORD_HASH": hash_password(ADMIN_PASSWORD),
            "USER_USERNAME": USER_USERNAME,
            "USER_PASSWORD_HASH": hash_password(USER_PASSWORD),
        }
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(settings.HASHED_PASSWORDS_FILE), exist_ok=True)
        
        # Save the hashed passwords
        with open(settings.HASHED_PASSWORDS_FILE, 'w') as file:
            json.dump(hashed_passwords, file)
    
    return hashed_passwords

async def get_current_user(request: Request):
    session_cookie = request.cookies.get("username")
    if session_cookie:
        # Since we are storing username directly in the cookie, we can retrieve it
        username = session_cookie
        # Determine the role based on the username
        if username == settings.ADMIN_USERNAME:
            role = "admin"
        else:
            role = "user"
        return {"username": username, "role": role}
    else:
        return None
    
def is_admin(user: dict) -> bool:
    return user["role"] == "admin" if user else False
