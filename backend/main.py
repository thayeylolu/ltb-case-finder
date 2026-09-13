"""Task 7/11: FastAPI application entry point and route registration."""

from fastapi import FastAPI

from backend.routes.search import router as search_router

app = FastAPI(title="LTB Case Discovery Tool")

app.include_router(search_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
