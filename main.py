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
Case_collection = db["Cage"]


class LightSensor(BaseModel):
    cage: int
    time: float

class Light_Input(BaseModel):
    cage: int

class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    vibrate: int
    hungry: int

@app.post("/light")
def get_light(light: Light_Input):
    query = Case_collection.find({"cage": light.cage},{"_id": 0})
    list_query = list(query)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {light.cage}")
    lightsensor = {
        "cage": light.cage,
        "time": datetime.now().timestamp()
    }
    query_light = Light_collection.find({"cage": light.cage})
    count = 1
    list_light = list(query_light)
    list_light.reverse()
    for r in list_light:
        print(r["time"])
        if count >= 10:
            Light_collection.delete_one(r)
            continue
        if (datetime.now().timestamp() - r["time"]) > 3600:
            Light_collection.delete_one(r)
            continue
        count = count + 1
    m = jsonable_encoder(lightsensor)
    Light_collection.insert_one(m)
    return "DONE."