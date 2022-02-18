from typing import Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pymongo import MongoClient
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "1bffc32856a4e21531c5bdd310fefe8a5313343150d3aa71e7b2d8ce58b6c6897"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

client = MongoClient('mongodb://localhost', 27017)

db = client["Tiger_Friend"]
users_collection = db["Users"]
light_collection = db["Light_Sensor"]
cage_collection = db["Cage"]


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class Permission(BaseModel):
    access: int


class LightSensor(BaseModel):
    case: int
    time: float


class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(collection_users, username: str, password: str):
    user = collection_users.find_one({"username": username}, {"_id": 0})
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


@app.post("/request-permission", response_model=Permission)
async def login_for_open_door(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_collection, form_data.username, form_data.password)
    if not user:
        return {"access:": 0}
    cage_collection.update_one({"cage": form_data.scopes}, {"$set": {"status": 1}})
    return {"access": 1}
