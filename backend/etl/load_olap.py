import sys
import pandas as pd
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.dim import DimDate, DimClient, DimEmploye, DimProduit
from backend.models.fact import FaitsVentes

# Mapping des feuilles Excel vers groupe d’insertion
SHEET_MAP = {
    "Calendrier": "dates",
    "Clients": "clients",
    "Employé": "emps",
    "Produits": "prods",
    "Vente Détail": "faits"
}


def etl_from_excel(path: str):
    # Lire toutes les feuilles du fichier
    xls = pd.read_excel(path, sheet_name=list(SHEET_MAP.keys()), dtype=str)
    session: Session = SessionLocal()

    # Précharger les clés existantes
    existing = {
        "dates": {d.id_date for d in session.query(DimDate.id_date)},
        "clients": {c.id_client for c in session.query(DimClient.id_client)},
        "emps": {e.id_employe for e in session.query(DimEmploye.id_employe)},
        "prods": {p.ean for p in session.query(DimProduit.ean)},
        "faits": {f.id_fait for f in session.query(FaitsVentes.id_fait)},
    }
    to_add = {k: [] for k in existing}

    for sheet_name, df in xls.items():
        key = SHEET_MAP[sheet_name]
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()

        if key == 'dates':
            if 'date' not in df.columns:
                print("> Skip 'dates' : colonne 'date' manquante")
                continue
            for _, row in df.iterrows():
                raw = row.get('date')
                if pd.isna(raw) or not raw:
                    continue
                try:
                    serial = int(raw)
                    dt = pd.to_datetime(serial, unit='d', origin='1899-12-30')
                    id_date = int(dt.strftime('%Y%m%d'))
                except Exception:
                    print(f"> Ignore date invalide : {raw!r}")
                    continue
                if id_date not in existing['dates']:
                    mois_nom = dt.strftime('%B')
                    annee_mois = int(dt.strftime('%Y%m'))
                    trimestre = f"Q{((dt.month - 1) // 3) + 1}"
                    to_add['dates'].append(
                        DimDate(
                            id_date=id_date,
                            jour=dt.day,
                            mois=dt.month,
                            annee=dt.year,
                            jour_semaine=dt.day_name(),
                            mois_nom=mois_nom,
                            annee_mois=annee_mois,
                            trimestre=trimestre
                        )
                    )
                    existing['dates'].add(id_date)

        elif key == 'clients':
            id_col = next((c for c in df.columns if 'customer_id' in c or 'cust' in c or 'client' in c), None)
            insc_col = next((c for c in df.columns if 'inscription' in c), None)
            if not id_col:
                print("> Skip 'clients' : id_client non trouvé")
                continue
            for _, row in df.iterrows():
                cid = row.get(id_col)
                if pd.isna(cid) or cid in existing['clients']:
                    continue
                di = None
                if insc_col:
                    raw_di = row.get(insc_col)
                    if pd.notna(raw_di):
                        try:
                            di = pd.to_datetime(raw_di, dayfirst=True).date()
                        except:
                            pass
                to_add['clients'].append(
                    DimClient(
                        id_client=cid,
                        date_inscription=di
                    )
                )
                existing['clients'].add(cid)

        elif key == 'emps':
            id_col = next((c for c in df.columns if 'id_employe' in c), None)
            if not id_col:
                print("> Skip 'emps' : id_employe non trouvé")
                continue
            for _, row in df.iterrows():
                eid = row.get(id_col)
                if pd.isna(eid) or eid in existing['emps']:
                    continue
                employe = row.get('employe') or None
                prenom = row.get('prenom') or None
                nom_em = row.get('nom') or None
                debut = None
                raw_deb = row.get('date_debut')
                if pd.notna(raw_deb):
                    try:
                        # Excel serial to date
                        debut = pd.to_datetime(int(raw_deb), unit='d', origin='1899-12-30').date()
                    except:
                        try:
                            debut = pd.to_datetime(raw_deb, dayfirst=True).date()
                        except:
                            pass
                hashmdp = row.get('hash_mdp') or None
                mail = row.get('mail') or None
                to_add['emps'].append(
                    DimEmploye(
                        id_employe=eid,
                        employe=employe,
                        prenom=prenom,
                        nom=nom_em,
                        date_debut=debut,
                        hash_mdp=hashmdp,
                        mail=mail
                    )
                )
                existing['emps'].add(eid)

        elif key == 'prods':
            ean_col = next((c for c in df.columns if 'ean' in c), None)
            cat_col = next((c for c in df.columns if 'categorie' in c or 'category' in c), None)
            rayon_col = next((c for c in df.columns if 'rayon' in c), None)
            lib_col = next((c for c in df.columns if 'libelle' in c), None)
            prix_col = next((c for c in df.columns if 'prix' in c or 'price' in c), None)
            if not ean_col:
                print("> Skip 'prods' : ean non trouvé")
                continue
            for _, row in df.iterrows():
                raw = row.get(ean_col)
                if pd.isna(raw):
                    continue
                try:
                    code = int(raw)
                except:
                    continue
                if code not in existing['prods']:
                    cat = row.get(cat_col) or None
                    rayon = row.get(rayon_col) or None
                    libelle = row.get(lib_col) or None
                    prix = None
                    raw_pr = row.get(prix_col)
                    if pd.notna(raw_pr):
                        try:
                            prix = float(str(raw_pr).replace(',', '.'))
                        except:
                            pass
                    to_add['prods'].append(
                        DimProduit(
                            ean=code,
                            category=cat,
                            rayon=rayon,
                            libelle=libelle,
                            prix=prix
                        )
                    )
                    existing['prods'].add(code)

        elif key == 'faits':

            # Détection dynamique des colonnes
            fid_col = next((c for c in df.columns if 'id_bdd' in c), None)
            date_col = next((c for c in df.columns if 'date' in c), None)
            client_col = next((c for c in df.columns if 'client' in c or 'customer' in c), None)
            emp_col = next((c for c in df.columns if 'employe' in c), None)
            ean_col = next((c for c in df.columns if 'ean' in c), None)
            ticket_col = next((c for c in df.columns if 'ticket' in c.lower()), None)

            missing = [name for name, col in [
                ('id_bdd', fid_col), ('date', date_col),
                ('client', client_col), ('employe', emp_col), ('ean', ean_col)
            ] if not col]
            if missing:
                print(f"> Skip 'faits': colonnes manquantes {missing}")
                continue

            for _, row in df.iterrows():
                fid = row.get(fid_col)
                if pd.isna(fid) or fid in existing['faits']:
                    continue

                raw_date = row.get(date_col)
                if pd.isna(raw_date):
                    print(f"> Skip fait {fid}: date manquante")
                    continue
                try:
                    if isinstance(raw_date, str) and raw_date.isdigit():
                        dt = pd.to_datetime(int(raw_date), unit='d', origin='1899-12-30')
                    else:
                        dt = pd.to_datetime(raw_date, dayfirst=True)
                    id_date = int(dt.strftime('%Y%m%d'))
                except Exception as e:
                    print(f"> Skip fait {fid}: date invalide ({e})")
                    continue

                cid = row.get(client_col)
                eid = row.get(emp_col)
                if pd.isna(cid) or pd.isna(eid):
                    print(f"> Skip fait {fid}: client ou employé manquant")
                    continue

                try:
                    code = int(row.get(ean_col))
                except Exception:
                    print(f"> Skip fait {fid}: EAN invalide")
                    continue

                id_ticket = row.get('id_ticket')

                to_add['faits'].append(FaitsVentes(
                    id_fait=fid,
                    id_date=id_date,
                    id_client=cid,
                    id_employe=eid,
                    ean=code,
                    id_ticket=id_ticket,
                ))
                existing['faits'].add(fid)

    # Insertion en base: on utilise add_all pour garantir persistance de tous les champs
    for grp in ['dates', 'clients', 'emps', 'prods', 'faits']:
        if to_add[grp]:
            session.add_all(to_add[grp])
            print(f" • {len(to_add[grp])} {grp} insérés")

    session.commit()
    session.close()
    print("✅ ETL complet terminé !")


def main():
    if len(sys.argv) != 2:
        print("Usage: python load_olap.py <path_to_excel>")
        sys.exit(1)
    etl_from_excel(sys.argv[1])


if __name__ == '__main__':
    main()
