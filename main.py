from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

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
Case_collection = db["Case"]


class LightSensor(BaseModel):
    case: int
    time: float

class Light_Input(BaseModel):
    case: int

class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int

@app.post("/light")
def get_light(light: Light_Input):
    lightsensor = {
        "case": light.case,
        "time": datetime.now()
    }
    m = jsonable_encoder(lightsensor)
    Light_collection.insert_one(m)
    return "DONE."