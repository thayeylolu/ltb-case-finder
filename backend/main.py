"""Task 7/11/13: FastAPI application entry point and route registration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.search import router as search_router

app = FastAPI(title="LTB Case Discovery Tool")

# The frontend (Task 12/13) is static HTML/CSS/JS served independently of
# this API (per architecture.md's two-lifecycle design), so its fetch()
# calls are cross-origin. No auth/user data exists in MVP 0 (plan.md
# section 11), so allowing any origin is acceptable here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(search_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
