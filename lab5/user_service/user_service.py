from fastapi import  FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import redis
import json
import os

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@user-postgres:5432/postgres"

engine = create_engine(url=DATABASE_URL)
session = sessionmaker(bind=engine)

def get_cache():
    redis_client = redis.from_url("redis://redis_cache:6379")
    try:
        yield redis_client
    finally:
        redis_client.close()

class Base(DeclarativeBase): pass

app = FastAPI()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    login = Column(String)
    name = Column(String)
    surname = Column(String)
    email = Column(String)
    hashed_password = Column(String)
    age = Column(Integer)

class UserInsert(BaseModel):
    id: int
    login: str
    name: str
    surname: str
    email: str
    hashed_password: str
    age: int

class UserResponse(BaseModel):
    id: int
    name: str
    surname: str
    class Config:
        from_attributes = True

Base.metadata.create_all(bind=engine)

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


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                  session: Session = Depends(get_db), cache: redis.Redis = Depends(get_cache)):
    password_check = False
    user = cache.get(form_data.username)
    password = ''
    if user is not None:
        user = UserInsert.model_validate_json(user)
        password = user.hashed_password
    else:
        query = select(User).filter_by(login=form_data.username)
        user = session.execute(query).first()
        password  = user[0].hashed_password
        cache.setex(user[0].login, timedelta(minutes=30), UserInsert(
                                                                id=user[0].id,
                                                                login=user[0].login,
                                                                name=user[0].name,
                                                                surname=user[0].surname,
                                                                email=user[0].email,
                                                                hashed_password=user[0].hashed_password,
                                                                age=user[0].age
                                                                ).model_dump_json())
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

@app.post("/users", response_model=UserResponse)
def create_user(user: UserInsert, session: Session = Depends(get_db), cache: redis.Redis = Depends(get_cache)):
    user.hashed_password = pwd_context.hash(user.hashed_password)
    base_user = User(**user.dict())
    try:
        session.add(base_user)
        session.commit()
        session.refresh(base_user)
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(status_code=404, detail="User already exist")
    cache.setex(user.login, timedelta(minutes=30), user.model_dump_json())
    return base_user

@app.get("/users/{user_login}", response_model=UserResponse)
def find_by_login(user_login: str, current_user: str = Depends(get_current_client),
                   session: Session = Depends(get_db), cache: redis.Redis = Depends(get_cache)):
    user = cache.get(user_login)
    if user is not None:
        user = UserResponse.model_validate_json(user)
        return user
    query = select(User).filter_by(login=user_login)
    user = session.execute(query).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    cache.setex(user_login, timedelta(minutes=30), UserInsert(
                                                        id=user[0].id,
                                                        login=user[0].login,
                                                        name=user[0].name,
                                                        surname=user[0].surname,
                                                        email=user[0].email,
                                                        hashed_password=user[0].hashed_password,
                                                        age=user[0].age
                                                    ).model_dump_json())
    return user[0]

@app.get("/users/{user_name}/{user_surname}", response_model=List[UserResponse])
def find_by_full_name(user_name: str, user_surname: str, current_user: str = Depends(get_current_client),
                       session: Session = Depends(get_db), cache: redis.Redis = Depends(get_cache)):
    full_name = user_name + user_surname
    users = cache.get(full_name)
    if users is not None:
        users = [UserResponse.model_validate_json(user) for user in json.loads(users)]
        return users 
    query = select(User).filter_by(name=user_name, surname=user_surname)
    users = session.execute(query).all()
    if users is None:
        raise HTTPException(status_code=404, detail="User not found")
    cache.setex(full_name, timedelta(minutes=30), json.dumps([UserInsert(
                                                        id=users[i].User.id,
                                                        login=users[i].User.login,
                                                        name=users[i].User.name,
                                                        surname=users[i].User.surname,
                                                        email=users[i].User.email,
                                                        hashed_password=users[i].User.hashed_password,
                                                        age=users[i].User.age
                                                    ).model_dump_json() for i in range(len(users))]))
    return [users[i].User for i in range(len(users))]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)