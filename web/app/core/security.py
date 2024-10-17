import json
import os
from typing import Dict
from passlib.context import CryptContext
from core.config import settings
from fastapi import Request, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta


# Initialize the hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def load_users() -> Dict[str, dict]:
    if os.path.exists(settings.HASHED_PASSWORDS_FILE):
        with open(settings.HASHED_PASSWORDS_FILE, 'r') as file:
            users = json.load(file)
    else:
        users = {
            settings.ADMIN_USERNAME: {
                "username": settings.ADMIN_USERNAME,
                "hashed_password": hash_password(settings.ADMIN_PASSWORD),
                "role": "admin"
            },
            settings.USER_USERNAME: {
                "username": settings.USER_USERNAME,
                "hashed_password": hash_password(settings.USER_PASSWORD),
                "role": "user"
            }
        }
        os.makedirs(os.path.dirname(settings.HASHED_PASSWORDS_FILE), exist_ok=True)
        with open(settings.HASHED_PASSWORDS_FILE, 'w') as file:
            json.dump(users, file)
    return users

def authenticate_user(username: str, password: str):
    users = load_users()
    user = users.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
def is_admin(user: dict) -> bool:
    return user["role"] == "admin" if user else False
