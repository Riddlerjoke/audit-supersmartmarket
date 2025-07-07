from sqlalchemy import Column, Integer, String
from backend.database import Base


class DimDate(Base):
    __tablename__ = "dim_date"
    id_date = Column(Integer, primary_key=True, index=True)
    jour = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    annee = Column(Integer, nullable=False)
    jour_semaine = Column(String(10), nullable=False)
    mois_nom = Column(String(20), nullable=False)
    annee_mois = Column(Integer, nullable=False)
    trimestre = Column(String(2), nullable=False)


class DimClient(Base):
    __tablename__ = "dim_client"
    id_client = Column(String, primary_key=True, index=True)
    date_inscription = Column(Integer, nullable=False)


class DimEmploye(Base):
    __tablename__ = "dim_employe"
    id_employe = Column(String, primary_key=True, index=True)
    employe = Column(String(100))
    nom = Column(String(50))
    prenom = Column(String(50))
    date_debut = Column(Integer, nullable=False)
    hash_mdp = Column(String(100))
    mail = Column(String(100))


class DimProduit(Base):
    __tablename__ = "dim_produit"
    ean = Column(Integer, primary_key=True, index=True)
    category = Column(String(50))
    rayon = Column(String(50))
    libelle = Column(String(200))
    prix = Column(Integer)
