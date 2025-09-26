from fastapi import FastAPI
from pydantic import BaseModel

app=FastAPI()
print("hello")
db={}

class User(BaseModel):
    name: str
    role: str

@app.post('/create_user')
async def create(user: User):
    db["user"] = user.dict()
    return user

@app.get('/user')
async def get_user (name):
    if name not in db:
        print('User not defined')
    return db['user']
    