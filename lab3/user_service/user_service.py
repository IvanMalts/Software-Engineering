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

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@user-postgres:5432/postgres"

engine = create_engine(url=DATABASE_URL)
session = sessionmaker(bind=engine)

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
        orm_mode = True

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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)):
    password_check = False
    query = select(User).filter_by(login=form_data.username)
    result = session.execute(query).first()
    password  = result[0].hashed_password
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
def create_user(user: UserInsert, session: Session = Depends(get_db)):
    user.hashed_password = pwd_context.hash(user.hashed_password)
    base_user = User(**user.dict())
    try:
        session.add(base_user)
        session.commit()
        session.refresh(base_user)
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(status_code=404, detail="User already exist")
    return base_user

@app.get("/users/{user_login}", response_model=UserResponse)
def find_by_login(user_login: str, current_user: str = Depends(get_current_client), session: Session = Depends(get_db)):
    query = select(User).filter_by(login=user_login)
    result = session.execute(query).first()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result[0]

@app.get("/users/{user_name}/{user_surname}", response_model=List[UserResponse])
def find_by_full_name(user_name: str, user_surname: str, current_user: str = Depends(get_current_client), session: Session = Depends(get_db)):
    query = select(User).filter_by(name=user_name, surname=user_surname)
    result = session.execute(query).all()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return [result[i].User for i in range(len(result))]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)