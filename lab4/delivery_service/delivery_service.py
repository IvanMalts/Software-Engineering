from fastapi import  FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
import os

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

try:
    client = MongoClient("mongodb://mongo:mongo@mongodb:27017")
    print("OK")
except:
    print("Can't connect to mongo")

app = FastAPI()

class Delivery(BaseModel):
    id: int
    package_id: int
    receiver_id: int
    sender_id: int
    address: str
    deliveryman_id: int
    status: str

class Package(BaseModel):
    id: int
    sender_id: int
    dimensions: float
    weight: float

db = client['orders']

packages_collection = db['packages']
delivery_collection = db['delivery']

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8000/token")
async def get_current_client(token: str = Depends(oauth2_scheme)):
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
        else:
            return username
    except JWTError:
        raise credentials_exception

@app.post("/delivery", response_model=Delivery)
def create_delivery(delivery: Delivery, current_user: str = Depends(get_current_client)):
    if delivery_collection.find_one({"_id":delivery.id}) is not None:
        raise HTTPException(status_code=404, detail="User already exist")
    
    delivery_dict = delivery.model_dump()
    delivery_dict["_id"] = delivery_dict.pop("id")
    delivery_collection.insert_one(delivery_dict)
    return delivery

@app.get("/delivery/{role}/{user_id}", response_model=List[Delivery])
def get_delivery_by_user(role: str, user_id: int, current_user: str = Depends(get_current_client)):
    deliveries = []
    if role == "sender":
        for delivery in delivery_collection.find({"sender_id":user_id}):
                delivery["id"] = delivery.pop("_id")
                deliveries.append(delivery)
        if len(deliveries) == 0:
            raise HTTPException(status_code=404, detail="No packages sent from this user")

    elif role == "receiver":
        for delivery in delivery_collection.find({"receiver_id":user_id}):
                delivery["id"] = delivery.pop("_id")
                deliveries.append(delivery)
        if len(deliveries) == 0:
            raise HTTPException(status_code=404, detail="No packages sent to this user")

    return deliveries

@app.post("/packages", response_model=Package)
def create_package(package: Package, current_user: str = Depends(get_current_client)):
    if packages_collection.find_one({"_id":package.id}) is not None:
            raise HTTPException(status_code=404, detail="Package already exist")
    
    package_dict = package.model_dump()
    package_dict["_id"] = package_dict.pop("id")
    packages_collection.insert_one(package_dict)
    return package

@app.get("/packages/{user_id}", response_model=List[Package])
def find_user_packages(user_id: int, current_user: str = Depends(get_current_client)):
    packages = []
    for package in packages_collection.find({"sender_id": user_id}):
            package["id"] = package.pop("_id")
            packages.append(package)
    if len(packages) == 0:
        raise HTTPException(status_code=404, detail="No packages for this user")
    return packages

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8001)