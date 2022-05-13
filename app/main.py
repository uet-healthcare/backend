from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.routes.public_routes import publicRoutes
from app.routes.private_routes import privateRoutes
import base64
import json


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_user_id_to_header(request: Request, call_next):
    if request.url.path.startswith("/private"):
        payload = request.headers.get("Authorization").split(".")[1]
        decoded = json.loads(
            (base64.urlsafe_b64decode(payload + "="*divmod(len(payload), 4)[1])).decode("utf-8"))
        request.state.x_user_id = decoded.get("sub")

    response = await call_next(request)
    return response


app.include_router(publicRoutes)
app.include_router(privateRoutes)
