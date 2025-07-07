# backend/routers/etl.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pathlib import Path

from backend.etl.load_olap import etl_from_excel

router = APIRouter(prefix="/etl", tags=["ETL"])

# Chemin fixe vers le fichier d'extraction
EXCEL_PATH = Path(__file__).parent.parent / "data" / "Extraction-cube-OLAP-2024.xlsx"


@router.post("/run")
def run_etl(background_tasks: BackgroundTasks):
    # Vérification que le fichier existe
    if not EXCEL_PATH.exists() or not EXCEL_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"Fichier introuvable : {EXCEL_PATH}"
        )
    # Lancement de l'ETL en tâche de fond
    background_tasks.add_task(etl_from_excel, str(EXCEL_PATH))
    return {
        "message": "ETL lancé avec le fichier par défaut",
        "file_used": str(EXCEL_PATH)
    }
