import asyncio
import logging

from fastapi import FastAPI

from api import router as api_router
from database import Base, engine
from scanner import scanner_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

app = FastAPI(title="Network Device Monitor", version="1.0.0")
app.include_router(api_router)


@app.on_event("startup")
async def startup() -> None:
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(scanner_loop())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
