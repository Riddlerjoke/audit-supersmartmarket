from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.fact import FaitsVentes
from pydantic import BaseModel

router = APIRouter(prefix="/faits", tags=["Faits"])


class FaitIn(BaseModel):
    id_fait: str; id_date: int; id_client: str; id_employe: str; ean: int
    id_ticket: str = None


@router.post("/ventes", response_model=FaitIn)
def create_fait(fait: FaitIn, db: Session = Depends(get_db)):
    obj = FaitsVentes(**fait.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj
