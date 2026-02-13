from fastapi import FastAPI

from .governance_routes import router as governance_router
from .routes import router as core_router
from .validation_routes import router as validation_router
from core.observability.metrics import start_metrics_server, update_health_status


# Initialize observability metrics server
start_metrics_server()
update_health_status(True)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Open Epistemic Network",
        version="0.1.0",
        description="Open, non-blockchain epistemic protocol with hybrid stake+reputation validation.",
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict:  # pragma: no cover - trivial
        return {"status": "ok"}

    app.include_router(core_router)
    app.include_router(governance_router)
    app.include_router(validation_router)
    return app


app = create_app()


