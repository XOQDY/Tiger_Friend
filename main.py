from tkinter.messagebox import NO
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
    cage: int
    time: float

class DangerDistance(BaseModel):
    room: int
    danger: int

class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int

@app.post("/Danger_Distance")
def case_vibration(status: DangerDistance):
    room = status.room
    query = Case_collection.find_one({"room": room}, {"_id": 0})
    if query is None:
        raise HTTPException(404, f"Couldn't find cage: {room}")
    if status.danger:
        Case_collection.update_one({"room": room}, {"$set": {"danger": 1}})
        return{
            "message": f"There is a people in danger distance at cage {room}."
        }
    else:
        Case_collection.update_one({"room": room}, {"$set": {"danger": 0}})
        return{
            "message": f"There is no people in danger distance at cage {room}."
        }