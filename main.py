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


class LightSensor(BaseModel):
    case: int
    time: float


class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int

class Door(BaseModel):
    cage: int
    status: int

@app.post("/door/get")
def post_door(door: Door):
    room = door.cage
    query_cage = Case_collection.find({"room": room})
    list_cage = list(query_cage)
    if len(list_cage) == 0:
        raise HTTPException(404, f"Couldn't found cage: {room}")
    Case_collection.update_one({"room": room}, {"$set": {"status": door.status}})
    return "DONE."