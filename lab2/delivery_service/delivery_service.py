from fastapi import  FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

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

packages_db = []
delivery_db = []

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
    for d in delivery_db:
        if d.id == delivery.id: 
            raise HTTPException(status_code=404, detail="User already exist")
        
    delivery_db.append(delivery)
    return delivery

@app.get("/delivery/{role}/{user_id}", response_model=List[Delivery])
def get_delivery_by_user(role: str, user_id: int, current_user: str = Depends(get_current_client)):
    deliveries = []
    if role == "sender":
        for d in delivery_db:
            if d.sender_id == user_id:
                deliveries.append(d)
        if len(deliveries) == 0:
            raise HTTPException(status_code=404, detail="No packages sent from this user")

    elif role == "receiver":
        for d in delivery_db:
            if d.receiver_id == user_id:
                deliveries.append(d)
        if len(deliveries) == 0:
            raise HTTPException(status_code=404, detail="No packages sent to this user")

    return deliveries

@app.post("/packages", response_model=Package)
def create_package(package: Package, current_user: str = Depends(get_current_client)):
    for p in packages_db:
        if p.id == package.id:
            raise HTTPException(status_code=404, detail="Package already exist")
    packages_db.append(package)
    return package

@app.get("/packages/{user_id}", response_model=List[Package])
def find_user_packages(user_id: int, current_user: str = Depends(get_current_client)):
    packages = []
    for p in packages_db:
        if p.sender_id == user_id:
            packages.append(p)
    if len(packages) == 0:
        raise HTTPException(status_code=404, detail="No packages for this user")
    return packages

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8001)