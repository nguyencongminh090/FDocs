import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middlewares.error_handler import unhandled_exception_handler
from app.routes import auth, documents, analysis, qa

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FDocs API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(qa.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
