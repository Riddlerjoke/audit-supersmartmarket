from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.database import SessionLocal

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/revenue_by_month")
def revenue_by_month(db: Session = Depends(get_db)):
    """
    Calcule le CA par mois :
      - on transforme id_date YYYYMMDD en 'YYYY-MM'
      - on somme prix * quantité (ici quantité=1 si vous n’en avez pas)
    """
    sql = text("""
        SELECT
           to_char(to_date(d.id_date::text, 'YYYYMMDD'), 'YYYY-MM') AS month,
           SUM(p.prix)                                          AS revenue
        FROM faits_ventes f
        JOIN dim_date    d ON f.id_date    = d.id_date
        JOIN dim_produit p ON f.ean        = p.ean
        GROUP BY 1
        ORDER BY 1
    """)
    rows = db.execute(sql).fetchall()
    return [
        {"month": r["month"], "revenue": float(r["revenue"] or 0)}
        for r in rows
    ]


@router.get("/monthly_revenue")
def monthly_revenue(db: Session = Depends(get_db)):
    """
    Retourne le chiffre d'affaires par mois (année + mois).
    """
    query = text(
        """
        SELECT d.annee AS year,
               d.mois  AS month,
               SUM(p.prix) AS revenue
        FROM faits_ventes f
        JOIN dim_date d     ON f.id_date    = d.id_date
        JOIN dim_produit p  ON f.ean        = p.ean
        GROUP BY d.annee, d.mois
        ORDER BY d.annee, d.mois;
        """
    )
    rows = db.execute(query).fetchall()
    return [
        {"year": r.year, "month": r.month, "revenue": float(r.revenue)}
        for r in rows
    ]


@router.get("/revenue_by_date/{id_date}")
def revenue_by_date(id_date: int, db: Session = Depends(get_db)):
    """
    Retourne le chiffre d'affaires total pour une date donnée (format YYYYMMDD).
    """
    query = text(
        """
        SELECT SUM(p.prix) AS revenue
        FROM faits_ventes f
        JOIN dim_produit p ON f.ean = p.ean
        WHERE f.id_date = :id_date;
        """
    )
    result = db.execute(query, {"id_date": id_date}).scalar()
    if result is None:
        raise HTTPException(status_code=404, detail=f"Aucune vente pour la date {id_date}")
    return {"id_date": id_date, "revenue": float(result)}


@router.get("/top_clients")
def top_clients(limit: int = 10, db: Session = Depends(get_db)):
    """
    Retourne le top N clients par chiffre d'affaires.
    """
    query = text(
        """
        SELECT f.id_client AS client,
               COUNT(*)       AS tickets,
               SUM(p.prix)    AS revenue
        FROM faits_ventes f
        JOIN dim_produit p ON f.ean = p.ean
        GROUP BY f.id_client
        ORDER BY revenue DESC
        LIMIT :limit;
        """
    )
    result = db.execute(query, {"limit": limit}).fetchall()
    return [
        {"client": row.client, "tickets": row.tickets, "revenue": float(row.revenue)}
        for row in result
    ]

@router.get("/revenue_share_by_employee")
def revenue_share_by_employee(db: Session = Depends(get_db)):
    """
    Calcule la part de chiffre d'affaires encaissé par employé.
    """
    # Chiffre d'affaires total
    total_query = text(
        "SELECT SUM(p.prix) AS total "
        "FROM faits_ventes f "
        "JOIN dim_produit p ON f.ean = p.ean"
    )
    total_result = db.execute(total_query).scalar()
    if total_result is None:
        raise HTTPException(status_code=404, detail="Aucune donnée de ventes trouvée")
    total_revenue = float(total_result)

    # Chiffre d'affaires par employé
    emp_query = text(
        """
        SELECT f.id_employe AS employee,
               SUM(p.prix)    AS revenue
        FROM faits_ventes f
        JOIN dim_produit p ON f.ean = p.ean
        GROUP BY f.id_employe;
        """
    )
    rows = db.execute(emp_query).fetchall()

    # Construction du résultat avec part en pourcentage
    output = []
    for row in rows:
        emp_revenue = float(row.revenue)
        share_pct = round((emp_revenue / total_revenue) * 100, 2)
        output.append({
            "employe": row.employee,
            "revenue": emp_revenue,
            "share_pct": share_pct
        })
    return {
        "total_revenue": total_revenue,
        "by_employee": output
    }

