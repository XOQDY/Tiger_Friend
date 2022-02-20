from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from pymongo import MongoClient
from pydantic import BaseModel

from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "1bffc32856a4e21531c5bdd310fefe8a5313343150d3aa71e7b2d8ce58b6c6897"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class LightSensor(BaseModel):
    room: int
    time: float


class Vibration(BaseModel):
    room: int
    vibrate: int


class DangerDistance(BaseModel):
    room: int
    danger: int


class TempInput(BaseModel):
    room: int
    temp: float


class LightInput(BaseModel):
    room: int


class FoodDoor(BaseModel):
    room: int
    status: int


class FoodDrop(BaseModel):
    room: int

      
class TigerCase(BaseModel):
    room: int
    temperature: float
    status: int
    food_door: Optional[int]
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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def check_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return True

  
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
    query_cage = cage_collection.find({"room": temp_input.room})
    list_query = list(query_cage)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {temp_input.room}")
    new_temp = temp_input.temp
    cage_collection.update_one({"room": temp_input.room}, {"$set": {"temperature": new_temp}})
    return "DONE."


@app.post("/light")
def get_light(light: LightInput):
    query = cage_collection.find({"room": light.room}, {"_id": 0})
    list_query = list(query)
    if len(list_query) == 0:
        raise HTTPException(404, f"Couldn't find cage: {light.room}")
    light_sensor = {
        "cage": light.room,
        "time": datetime.now().timestamp()
    }
    query_light = light_collection.find({"cage": light.room})
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
        cage_collection.update_one({"room": light.room}, {"$set": {"hungry": 1}})
    else:
        cage_collection.update_one({"room": light.room}, {"$set": {"hungry": 0}})
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
def post_food_door(food_door: FoodDoor, permission: bool = Depends(check_token)):
    if permission:
        room = food_door.room
        query_cage = cage_collection.find({"room": room})
        list_cage = list(query_cage)
        if len(list_cage) == 0:
            raise HTTPException(404, f"Couldn't found cage: {room}")
        cage_collection.update_one({"room": room}, {"$set": {"food_door": food_door.status}})
        return "DONE."


@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_collection, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.put("/open-close-door/{room}/{status}")
async def close_door(room: int, status: int, permission: bool = Depends(check_token)):
    if permission:
        if status != 1 and status != 0:
            raise HTTPException(400, f"Status: {status} not found.")
        cage_collection.update_one({"room": room}, {"$set": {"status": status}})
        if status == 1:
            return {
                "message": f"Door in cage {room} are opening."
            }
        else:
            return {
                "message": f"Door in cage {room} are closing."
            }


@app.get("/tiger/{room}")
def information(room: int, permission: bool = Depends(check_token)):
    if permission:
        tiger = cage_collection.find_one({"room": room}, {"_id": 0, "food_door": 0})
        return tiger



@app.post("/food/success")
def fooddrop(fooddrop: FoodDrop):
    room = fooddrop.room
    query_cage = cage_collection.find({"room": room})
    list_cage = list(query_cage)
    if len(list_cage) == 0:
        raise HTTPException(404, f"Couldn't found cage: {room}")
    cage_collection.update_one({"room": room}, {"$set": {"food_door": 0}})
    return "DONE."
