from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.dim import DimDate, DimClient, DimEmploye, DimProduit
from pydantic import BaseModel

router = APIRouter(prefix="/dim", tags=["Dimensions"])


class DateIn(BaseModel):
    id_date: int;
    jour: int;
    mois: int;
    annee: int;
    jour_semaine: str
    mois_nom: str
    annee_mois: int
    trimestre: str


@router.post("/date", response_model=DateIn)
def create_date(date: DateIn, db: Session = Depends(get_db)):
    obj = DimDate(**date.dict())
    db.add(obj);
    db.commit();
    db.refresh(obj)
    return obj


class ClientIn(BaseModel):
    id_client: str;
    date_inscription: int | None = None;
    # date_inscription: str | None = None;  # Format YYYY-MM-DD ou YYYYMMDD


@router.post("/client", response_model=ClientIn)
def create_client(client: ClientIn, db: Session = Depends(get_db)):
    obj = DimClient(**client.dict())
    db.add(obj);
    db.commit();
    db.refresh(obj)
    return obj


class EmployeIn(BaseModel):
    id_employe: str;
    employe: str | None = None;
    nom: str | None = None;
    prenom: str | None = None;
    date_debut: int | None = None;
    hash_mdp: str | None = None;
    mail: str | None = None;


@router.post("/employe", response_model=EmployeIn)
def create_employe(emp: EmployeIn, db: Session = Depends(get_db)):
    obj = DimEmploye(**emp.dict())
    db.add(obj);
    db.commit();
    db.refresh(obj)
    return obj


class ProduitIn(BaseModel):
    ean: int;
    libelle: str | None = None
    category: str | None = None;
    rayon: str | None = None;
    prix: int | None = None;


@router.post("/produit", response_model=ProduitIn)
def create_produit(prod: ProduitIn, db: Session = Depends(get_db)):
    obj = DimProduit(**prod.dict())
    db.add(obj);
    db.commit();
    db.refresh(obj)
    return obj
