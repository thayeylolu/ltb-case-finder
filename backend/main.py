"""Task 7: FastAPI application entry point.

Later tasks register additional routes here (Task 11 adds POST /search via
backend/routes/search.py).
"""

from fastapi import FastAPI

app = FastAPI(title="LTB Case Discovery Tool")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
