from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from database import get_cursor
import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db = {
    "alice": {
        "username": "alice",
        "hashed_password": pwd_context.hash("password123")
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username, password):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in fake_users_db:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth credentials")

app = FastAPI()

class Menu(BaseModel):
    item: str
    price: int

@app.on_event("startup")
def startup():
    with get_cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item VARCHAR(255) NOT NULL,
            price INT NOT NULL
        )
        """)

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user["username"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/orders")
async def create_order(menu: Menu, current_user: str = Depends(get_current_user)):
    with get_cursor() as cursor:
        cursor.execute("INSERT INTO menu (item, price) VALUES (%s, %s)", (menu.item, menu.price))
        order_id = cursor.lastrowid
    return {"order_id": order_id, "item": menu.item, "price": menu.price, "user": current_user}

@app.get("/orders")
async def get_orders(current_user: str = Depends(get_current_user)):
    with get_cursor() as cursor:
        cursor.execute("SELECT id, item, price FROM menu")
        orders = cursor.fetchall()
    return [{"order_id": o[0], "item": o[1], "price": o[2]} for o in orders]

@app.get("/orders/{order_id}")
async def get_order(order_id: int, current_user: str = Depends(get_current_user)):
    with get_cursor() as cursor:
        cursor.execute("SELECT id, item, price FROM menu WHERE id=%s", (order_id,))
        order = cursor.fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order[0], "item": order[1], "price": order[2]}

@app.get("/items/{item_name}")
async def get_item(item_name: str, current_user: str = Depends(get_current_user)):
    with get_cursor() as cursor:
        cursor.execute("SELECT id, item, price FROM menu WHERE item=%s", (item_name,))
        items = cursor.fetchall()
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    return [{"order_id": i[0], "item": i[1], "price": i[2]} for i in items]

@app.delete("/items/{item_name}")
async def delete_item(item_name: str, current_user: str = Depends(get_current_user)):
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM menu WHERE item=%s", (item_name,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": f"Item '{item_name}' deleted successfully"}
