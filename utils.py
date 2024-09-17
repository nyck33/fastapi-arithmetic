from datetime import timedelta, datetime
from jose import jwt
from typing import Optional
import os
import supabase

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

def authenticate_user(username: str, password: str):
    response = supabase.table('users').select('*').eq('username', username).execute()
    if response.error or not response.data:
        return None
    user = response.data[0]
    if user['password'] != password:  # Replace with hashed password check in production
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
