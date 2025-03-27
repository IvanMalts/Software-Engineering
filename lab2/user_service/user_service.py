from fastapi import  FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

class User(BaseModel):
    id: int
    login: str
    name: str
    surname: str
    contacts: str
    hashed_password: str
    age: Optional[int] = None

users_db = []
users_db.append(User(id=0, 
                   login="admin",
                    name="Ivan",
                    surname="Ivanov",
                    contacts="admin@main.ru",
                    hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                    age=23))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def find_user(username: str):
    for user in users_db:
        if user.login == username:
            return user.hashed_password


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    password_check = False
    password = find_user(form_data.username)
    if pwd_context.verify(form_data.password, password):
        password_check = True

    if password_check:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/users", response_model=User)
def create_user(user: User):
    for u in users_db:
        if u.id == user.id:
            raise HTTPException(status_code=404, detail="User already exist")
    user.hashed_password = pwd_context.hash(user.hashed_password)
    users_db.append(user)
    return user

@app.get("/users/{user_login}", response_model=User)
def find_by_login(user_login: str, current_user: str = Depends(get_current_client)):
    for u in users_db:
        if u.login == user_login:
            return u
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/{user_name}/{user_surname}", response_model=User)
def find_by_full_name(user_name: str, user_surname: str, current_user: str = Depends(get_current_client)):
    for u in users_db:
        if u.surname == user_surname and u.name == user_name:
            return u
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)