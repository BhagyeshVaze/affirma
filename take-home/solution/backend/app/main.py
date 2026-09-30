from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config

app = FastAPI(title="Is this week unusual?")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}
