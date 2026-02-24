import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    os.getenv("VITE_URL", "http://localhost:3000"),
    os.getenv("BACKEND_URL", "http://localhost:8000"),
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # Specific allowed origins
        allow_credentials=True,  # Allow cookies and authentication headers
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],  # Allow all headers
    )

@app.get("/")
async def read_root():
    return {"ok": True}