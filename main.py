from fastapi import FastAPI
from routes.User_Management import router as users
from routes.DC_Details import router as dc_details

app = FastAPI()

app.include_router(users)
app.include_router(dc_details)