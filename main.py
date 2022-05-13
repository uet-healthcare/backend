import base64
from fastapi import FastAPI, Request
import json

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
