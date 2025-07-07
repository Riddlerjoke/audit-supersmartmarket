import uvicorn
from fastapi import FastAPI

from backend.database import engine, Base
from backend.routers.dim import router as dim_router
from backend.routers.fact import router as fact_router
from backend.routers.etl import router as etl_router

# Charge les modèles pour Base.metadata
import backend.models.dim, backend.models.fact
from backend.routers import analytics

# Charger les modèles pour les logs
from backend.routers import logs

# Création automatique des tables OLAP
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OLAP PoC")
app.include_router(dim_router, prefix="/dim")
app.include_router(fact_router, prefix="/faits")
app.include_router(etl_router, prefix="/etl")
app.include_router(analytics.router)
app.include_router(logs.router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
