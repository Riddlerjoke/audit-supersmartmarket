from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc, text
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.logs import Log
import os
from backend.models.dim import DimProduit, DimClient
import datetime
from itertools import groupby

from backend.etl.load_logs import load_logs_from_excel
from backend.models.fact import FaitsVentes

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/load", summary="Charge et nettoie data/logs.xlsx dans la table logs")
def load_logs_from_file(db: Session = Depends(get_db)):
    base_dir = os.path.dirname(os.path.dirname(__file__))  # chemin vers backend/
    file_path = os.path.join(base_dir, "data", "logs.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable: {file_path}")

    try:
        load_logs_from_excel(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur ETL logs: {e}")

    return {
        "status": "success",
        "message": f"Le fichier {file_path} a bien été chargé (colonnes inchangées)."
    }


@router.get("/")
def read_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Log).order_by(Log.event_time.desc()).offset(skip).limit(limit).all()


@router.get("/by-table/{table_name}")
def read_logs_by_table(table_name: str, db: Session = Depends(get_db)):
    return db.query(Log).filter(Log.target_table == table_name).all()


@router.get("/par‐plage", summary="Retourne les logs entre deux dates")
def get_logs_par_plage(
        date_debut: str = Query(..., description="Date de début au format YYYY‐MM‐DD"),
        date_fin: str = Query(..., description="Date de fin au format YYYY‐MM‐DD"),
        db: Session = Depends(get_db)
):
    sql = """
      SELECT *
      FROM logs
      WHERE event_time >= :debut
        AND event_time <  :fin
      ORDER BY event_time DESC
      LIMIT 1000;
    """
    return db.execute(text(sql), {"debut": date_debut, "fin": date_fin}).fetchall()


@router.get("/prix‐produits", summary="Liste des changements de prix sur Produits")
def get_logs_prix_produits(
        date_debut: str = Query(..., description="Date début (YYYY‐MM‐DD)"),
        db: Session = Depends(get_db)
):
    sql = """
      SELECT
        l.event_time,
        l.id_user,
        l.target_id   AS produit_ean,
        l.detail   AS nouveau_prix
      FROM logs AS l
      WHERE l.target_table = 'Produits'
        AND l.field_name   = 'prix'
        AND l.event_time >= :debut
      ORDER BY l.event_time DESC;
    """
    return db.execute(text(sql), {"debut": date_debut}).fetchall()


@router.get("/stat‐clients‐par‐user", summary="Nombre de modifications Client par utilisateur")
def stats_modifs_clients(db: Session = Depends(get_db)):
    sql = """
      SELECT
        l.id_user,
        COUNT(*) AS nb_modifs_clients
      FROM logs AS l
      WHERE l.target_table = 'Client'
      GROUP BY l.id_user
      ORDER BY nb_modifs_clients DESC
      LIMIT 20;
    """
    return db.execute(text(sql)).fetchall()


@router.get("/corrections‐ventes", summary="Logs sur la table Ventes (fait_ventes)")
def get_logs_ventes(
        date_debut: str = Query(..., description="Date début (YYYY‐MM‐DD)"),
        db: Session = Depends(get_db)
):
    sql = """
      SELECT
        l.event_time,
        l.id_user,
        l.operation,
        l.target_id   AS id_fait,
        l.field_name,
        l.detail 
      FROM logs AS l
      WHERE l.target_table = 'Ventes'
        AND l.event_time >= :debut
      ORDER BY l.event_time DESC;
    """
    return db.execute(text(sql), {"debut": date_debut}).fetchall()


@router.post("/apply", summary="Applique les logs sur Ventes, Produits et Clients")
def apply_logs(db: Session = Depends(get_db)):
    # Récupérer les logs d'insertion Ventes, mise à jour Produits.prix et insertion Clients
    logs = db.query(Log).filter(
        ((Log.target_table == 'Ventes') & (Log.operation == 'INSERT')) |
        ((Log.target_table == 'Produits') & (Log.operation == 'UPDATE') & (Log.field_name == 'prix')) |
        ((Log.target_table == 'Client')  & (Log.operation == 'INSERT'))
    ).order_by(Log.target_table, Log.target_id, Log.field_name).all()

    if not logs:
        raise HTTPException(404, "Aucun log à appliquer")

    inserted_sales = 0
    updated_products = 0
    inserted_clients = 0

    # INSERT Ventes
    ventes = [lg for lg in logs if lg.target_table == 'Ventes' and lg.operation == 'INSERT']
    for id_fait, group in groupby(ventes, key=lambda lg: lg.target_id):
        m = { log.field_name.lower().strip(): log.detail for log in group }
        try:
            # reconstituer chaque vente
            cid = m['customer_id']
            eid = m['id_employe']
            ean = int(m['ean'])
            rawd = m['date']
            if str(rawd).isdigit():
                dt = datetime.datetime(1899,12,30) + datetime.timedelta(days=int(rawd))
            else:
                dt = datetime.datetime.fromisoformat(rawd)
            id_date = int(dt.strftime("%Y%m%d"))
            ticket = m.get('id ticket') or m.get('id_ticket')
        except Exception:
            continue
        db.add(FaitsVentes(
            id_fait=id_fait,
            id_date=id_date,
            id_client=cid,
            id_employe=eid,
            ean=ean,
            id_ticket=ticket
        ))
        inserted_sales += 1

    # UPDATE Produits.prix
    prods = [lg for lg in logs if lg.target_table == 'Produits' and lg.operation == 'UPDATE' and lg.field_name == 'prix']
    for lg in prods:
        try:
            new_price = float(lg.detail)
            ean = int(lg.target_id)
        except Exception:
            continue
        res = db.query(DimProduit).filter(DimProduit.ean == ean).update(
            {DimProduit.prix: new_price}, synchronize_session=False
        )
        if res:
            updated_products += 1

    # INSERT Clients
    clients = [lg for lg in logs if lg.target_table == 'Client' and lg.operation == 'INSERT']
    for lg in clients:
        cid = lg.target_id
        raw = lg.detail
        try:
            # detail est ISO string ou timestamp
            if isinstance(raw, str) and raw:
                dt = datetime.datetime.fromisoformat(raw)
            else:
                dt = raw  # assume datetime
            signup = int(dt.strftime("%Y%m%d"))
        except Exception:
            signup = None

        # Vérifier si le client existe déjà
        existing_client = db.query(DimClient).filter(DimClient.id_client == cid).first()
        if not existing_client:  # Si le client n'existe pas, on l'insère
            db.add(DimClient(id_client=cid, date_inscription=signup))
            inserted_clients += 1

    # Commit
    db.commit()

    return {
        "inserted_sales": inserted_sales,
        "updated_products": updated_products,
        "inserted_clients": inserted_clients
    }
