from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from backend.database import Base


class FaitsVentes(Base):
    __tablename__ = "faits_ventes"
    id_fait = Column(String, primary_key=True, index=True)
    id_date = Column(Integer, ForeignKey("dim_date.id_date"), nullable=False)
    id_client = Column(String, ForeignKey("dim_client.id_client"), nullable=False)
    id_employe = Column(String, ForeignKey("dim_employe.id_employe"), nullable=False)
    ean = Column(Integer, ForeignKey("dim_produit.ean"), nullable=False)
    id_ticket = Column(String, nullable=True)
