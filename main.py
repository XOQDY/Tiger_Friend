from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware

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
Light_collection = db["Light_Sensor"]
Case_collection = db["Cage"]
Door_collection = db["Door"]

class LightSensor(BaseModel):
    case: int
    time: float

class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int

@app.get("/door/{number}")
def get_door(number: int):
    query = Case_collection.find_one({"room": number},{"_id": 0})
    list_query = list(query)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {number}")
    if query["status"] == 1:
        door = 1
    else:
        door = 0
    if query["food_door"] == 1:
        food = 1
    else:
        food = 0
    return {
        "door": door,
        "food": food
    }

