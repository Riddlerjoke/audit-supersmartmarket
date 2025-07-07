#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal


def load_logs_from_excel(path_to_excel: str):
    """
    1) Lit backend/data/logs.xlsx (feuille "Logs")
    2) Drop toute colonne “Unnamed: …” laissée par Excel
    3) Vérifie que les colonnes restantes sont exactement :
       id_user, date, action, table_insert, id_ligne, champs, detail
    4) Pour chaque ligne :
       - convertit “date” en datetime
       - si champs == 'prix', force detail en float (recomposition jour + mois si c’est un Timestamp),
         sinon si 'date' dans champs, parse detail en date et renvoie ISO string
       - sinon, garde detail en string brut
    5) Insère en base, dans la table `logs`, ces colonnes (mêmes noms).
    """

    # 1) Lecture de la feuille “Logs”.
    #    On force id_user, action, table_insert, id_ligne, champs en str, mais pas 'detail' :
    #    si Excel a déjà converti la cellule en date, pandas la lira en Timestamp.
    df = pd.read_excel(
        path_to_excel,
        sheet_name="Logs",
        dtype={
            "id_user": str,
            "action": str,
            "table_insert": str,
            "id_ligne": str,
            "champs": str,
            "detail": object  # On laisse 'detail' en object pour gérer les dates et autres types
        },
        keep_default_na=False
    )

    # 2) Drop des colonnes “Unnamed: …” éventuelles
    df = df.loc[:, [col for col in df.columns if not str(col).startswith("Unnamed")]]

    # 3) Normalisation des noms de colonnes (minuscules, sans espaces étranges)
    def normalize_col(c: str) -> str:
        return (
            str(c)
            .strip()
            .replace("\u00A0", " ")
            .replace(" ", "_")
            .lower()
        )

    df.columns = [normalize_col(c) for c in df.columns]

    # 4) Vérification des colonnes attendues
    expected = ["id_user", "date", "action", "table_insert", "id_ligne", "champs", "detail"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le fichier Logs.xlsx : {missing}")

    # 5) Ne garder QUE ces colonnes (dans l’ordre voulu)
    df = df[expected]

    # 6) Parsing de la colonne “date” pour transformer en datetime Python
    def parse_event_time(raw_date):
        """
        - Si raw_date est un entier (Excel serial, ex. 45518), on convertit via origin='1899-12-30'.
        - Si c’est déjà un Timestamp, on renvoie telle quelle.
        - Sinon, on tente de parser la chaîne (ISO ou JJ/MM/AAAA).
        """
        if pd.isna(raw_date):
            return None

        # Si pandas a déjà mis un Timestamp (Excel avait converti en date)
        if isinstance(raw_date, (pd.Timestamp, datetime.datetime, datetime.date)):
            return pd.to_datetime(raw_date).to_pydatetime()

        s = str(raw_date).strip()
        # Cas “Excel serial” (ex. '45518')
        if s.isdigit():
            try:
                ts = pd.to_datetime(int(s), unit="d", origin="1899-12-30")
                return ts.to_pydatetime()
            except Exception:
                pass

        # Sinon, on essaye d’interpréter la chaîne
        try:
            # Tentative ISO ou 'YYYY-MM-DD hh:mm:ss'
            return pd.to_datetime(s, dayfirst=False).to_pydatetime()
        except Exception:
            try:
                # Puis en format 'DD/MM/YYYY' ou autre
                return pd.to_datetime(s, dayfirst=True).to_pydatetime()
            except Exception:
                print(f"> [WARN] Impossible de parser la date '{raw_date}' dans ‘date’ (ligne...).")
                return None

    df["event_time"] = df["date"].apply(parse_event_time)

    # 7) Nettoyage et typage du champ “detail”
    def clean_detail(row):
        champ = str(row["champs"]).lower().strip()
        val = row["detail"]

        if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
            return None

        # ─── Si c'est un champ 'prix' ─────────────────────────────────────────────
        if champ == "prix":
            # a) Si pandas a déjà transformé la cellule en Timestamp
            if isinstance(val, (pd.Timestamp, datetime.datetime, datetime.date)):
                jour = pd.to_datetime(val).day
                mois = pd.to_datetime(val).month
                return float(f"{jour}.{mois:02d}")

            # b) Si c'est déjà un float ou int
            if isinstance(val, (float, int, np.floating, np.integer)):
                return float(val)

            # c) Sinon, on part du principe que c'est une chaîne du type '2.08' ou '2,54' ou éventuellement '02/08/2024'
            s = str(val).strip().replace(" ", "").replace(",", ".")
            try:
                return float(s)
            except ValueError:
                # d) Si ça ne rentre pas en float, on essaye quand même de parser en date
                try:
                    parsed = pd.to_datetime(s, dayfirst=True)
                    jour = parsed.day
                    mois = parsed.month
                    return float(f"{jour}.{mois:02d}")
                except Exception:
                    print(f"> [WARN] Impossible de caster '{val}' en float ou date pour 'prix' (id_ligne={row['id_ligne']})")
                    return None

        # ─── Si c'est un champ contenant 'date' (par ex. 'date_inscription', 'Date', etc.) ─
        elif "date_inscription" in champ:
            # a) Si pandas a déjà mis un Timestamp
            if isinstance(val, (pd.Timestamp, datetime.datetime, datetime.date)):
                # On retourne un string ISO (sans fuseau), ex. '2024-08-14 00:00:00'
                return pd.to_datetime(val).strftime("%Y-%m-%d %H:%M:%S")

            # b) Si c'est un entier (Excel serial)
            s = str(val).strip()
            if s.isdigit():
                try:
                    ts = pd.to_datetime(int(s), unit="d", origin="1899-12-30")
                    return ts.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            # c) Si c'est une chaîne 'DD/MM/YYYY' ou 'YYYY-MM-DD', on tente de parser
            try:
                parsed = pd.to_datetime(s, dayfirst=True)
                return parsed.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                print(f"> [WARN] Impossible de caster '{val}' en date pour '{champ}' (id_ligne={row['id_ligne']})")
                return None

        # ─── Sinon (tout le reste), on garde la chaîne brute ──────────────────────────
        else:
            return str(val)

    df["detail_clean"] = df.apply(clean_detail, axis=1)

    # 8) Construire le DataFrame final à insérer dans ‘logs’
    df_to_insert = pd.DataFrame({
        "log_id": np.arange(1, len(df) + 1),  # log_id auto-incrémenté
        "id_user": df["id_user"].astype(str),
        "event_time": df["event_time"],
        "operation": df["action"].astype(str),
        "target_table": df["table_insert"].astype(str),
        "target_id": df["id_ligne"].astype(str),
        "field_name": df["champs"].astype(str),
        # detail_clean contient soit :
        #  - un float pour 'prix' (ex. 2.08),
        #  - un string ISO pour un champ date (ex. '2024-08-14 00:00:00'),
        #  - soit le texte brut pour tout le reste.
        "detail": df["detail_clean"].astype(str)
    })

    # 9) Filtrer les lignes sans event_time valide
    n_before = len(df_to_insert)
    df_to_insert = df_to_insert[df_to_insert["event_time"].notna()]
    n_after = len(df_to_insert)
    if n_after < n_before:
        print(f"> [INFO] {n_before - n_after} ligne(s) ignorée(s) car 'event_time' invalide ou manquant.")

    # 10) Insertion en base, table “logs”
    session: Session = SessionLocal()
    try:
        df_to_insert.to_sql("logs", session.bind, if_exists="append", index=False)
        session.commit()
        print(f"→ {len(df_to_insert)} lignes insérées dans `logs`.")
    except Exception as e:
        session.rollback()
        print(f"> [ERROR] Échec insertion en base : {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))  # le dossier `backend/`
    file_path = os.path.join(base_dir, "data", "logs.xlsx")

    if not os.path.exists(file_path):
        print(f">[ERROR] Fichier introuvable : {file_path}")
    else:
        load_logs_from_excel(file_path)
