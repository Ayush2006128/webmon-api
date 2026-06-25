from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.database import engine, Base

from src.domains.auth.routers import router as auth_router
from src.domains.billing.routers import router as billing_router
from src.domains.agents.routers import router as agents_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    if engine:
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Webmon API", lifespan=lifespan)

origins = [
    "https://webmon-site.onrender.com",
    "http://localhost:1907",
    "http://127.0.0.1:1907"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(agents_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
