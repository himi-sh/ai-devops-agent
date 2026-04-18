from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_db
from backend.api import alerts, diagnosis, remediation, metrics, stream


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title="AI DevOps Agent", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(alerts.router)
    app.include_router(diagnosis.router)
    app.include_router(remediation.router)
    app.include_router(metrics.router)
    app.include_router(stream.router)

    @app.get("/")
    def root():
        return {"service": "AI DevOps Agent", "status": "ok"}

    return app


app = create_app()
