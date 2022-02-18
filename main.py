from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
from fastapi.encoders import jsonable_encoder

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
Case_collection = db["Case"]
Temp_collection = db["Temperature_Sensor"]


class LightSensor(BaseModel):
    cage: int
    time: float

class Temp_Input(BaseModel):
    cage: int
    temp: float

class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int

@app.post("/temp")
def post_temp(tempinput: Temp_Input):
    new_temp = tempinput.temp
    Temp_collection.update_one({},{"$set": {"temperature": new_temp}})
    return "DONE."
