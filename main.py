from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pymongo import MongoClient
from pydantic import BaseModel

from datetime import datetime

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

temp_collection = db["Temperature_Sensor"]
door_collection = db["Door"]
users_collection = db["Users"]
light_collection = db["Light_Sensor"]
cage_collection = db["Cage"]


class Permission(BaseModel):
    username: str
    password: str
    room: int


class LightSensor(BaseModel):
    cage: int
    time: float


class Vibration(BaseModel):
    room: int
    vibrate: int


class DangerDistance(BaseModel):
    room: int
    danger: int


class TempInput(BaseModel):
    cage: int
    temp: float


class LightInput(BaseModel):
    cage: int


class FoodDoor(BaseModel):
    cage: int
    status: int


class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    food_door: int
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


@app.post("/vibrate")
def cage_vibration(status: Vibration):
    room = status.room
    query = cage_collection.find_one({"room": room}, {"_id": 0})
    if query is None:
        raise HTTPException(404, f"Couldn't find cage: {room}")
    if status.vibrate:
        cage_collection.update_one({"room": room}, {"$set": {"vibrate": 1}})
        return {
            "message": f"Cage {room} is getting vibrated."
        }
    else:
        cage_collection.update_one({"room": room}, {"$set": {"vibrate": 0}})
        return {
            "message": f"There is no vibration in cage {room}."
        }


@app.post("/Danger_Distance")
def cage_danger(status: DangerDistance):
    room = status.room
    query = cage_collection.find_one({"room": room}, {"_id": 0})
    if query is None:
        raise HTTPException(404, f"Couldn't find cage: {room}")
    if status.danger:
        cage_collection.update_one({"room": room}, {"$set": {"danger": 1}})
        return {
            "message": f"There is a people in danger distance at cage {room}."
        }
    else:
        cage_collection.update_one({"room": room}, {"$set": {"danger": 0}})
        return {
            "message": f"There is no people in danger distance at cage {room}."
        }


@app.post("/temp")
def post_temp(temp_input: TempInput):
    query_cage = cage_collection.find({"room": temp_input.cage})
    list_query = list(query_cage)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {temp_input.cage}")
    new_temp = temp_input.temp
    temp_collection.update_one({}, {"$set": {"temperature": new_temp}})
    cage_collection.update_one({"room": temp_input.cage}, {"$set": {"temperature": new_temp}})
    return "DONE."


@app.post("/light")
def get_light(light: LightInput):
    query = cage_collection.find({"room": light.cage}, {"_id": 0})
    list_query = list(query)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {light.cage}")
    light_sensor = {
        "cage": light.cage,
        "time": datetime.now().timestamp()
    }
    query_light = light_collection.find({"cage": light.cage})
    count = 1
    list_light = list(query_light)
    list_light.reverse()
    for r in list_light:
        if count >= 10:
            light_collection.delete_one(r)
            continue
        if (datetime.now().timestamp() - r["time"]) > 3600:
            light_collection.delete_one(r)
            continue
        count = count + 1
    if count >= 10:
        cage_collection.update_one({"room": light.cage}, {"$set": {"hungry": 1}})
    else:
        cage_collection.update_one({"room": light.cage}, {"$set": {"hungry": 0}})
    m = jsonable_encoder(light_sensor)
    light_collection.insert_one(m)
    return "DONE."


@app.get("/door/{number}")
def get_door(number: int):
    query = cage_collection.find_one({"room": number}, {"_id": 0})
    list_query = list(query)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {number}")
    return {
        "door": query["status"],
        "food": query["food_door"]
    }


@app.post("/food-door")
def post_food_door(food_door: FoodDoor):
    room = food_door.cage
    query_cage = cage_collection.find({"room": room})
    list_cage = list(query_cage)
    if len(list_cage) == 0:
        raise HTTPException(404, f"Couldn't found cage: {room}")
    cage_collection.update_one({"room": room}, {"$set": {"food_door": food_door.status}})
    return "DONE."


@app.put("/request-permission")
async def login_for_open_door(form_data: Permission):
    user = authenticate_user(users_collection, form_data.username, form_data.password)
    if not user:
        return {"access:": 0}
    cage_collection.update_one({"room": form_data.room}, {"$set": {"status": 1}})
    return {"access": 1}


@app.put("/close-door/{room}")
async def close_door(room: int):
    cage_collection.update_one({"room": room}, {"$set": {"status": 0}})
    return {
        "message": f"Door in cage {room} are closing."
    }


@app.get("/tiger/{room}", response_model=TigerCase)
async def information(room: int):
    tiger = cage_collection.find_one({"room": room}, {"_id": 0, "food_door": 0})
    return tiger
