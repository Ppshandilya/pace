from fastapi import FastAPI
from orders import app  

x = FastAPI()

# Include the order-related routes from 'orders.py'

@x.get("/")
def root():
    return {"message": "Hello, FastAPI!"}

x.include_router(app)

# You can add other routers here (e.g., user-related, product-related)
