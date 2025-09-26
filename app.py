from fastapi import FastAPI



app=FastAPI()

@app.get('/home')
async def home():

    print("Hello World")
    return {"hello":"world"}

