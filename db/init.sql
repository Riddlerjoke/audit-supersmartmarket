-- ┌──────────────────────────────────────────────────────────┐
-- │ 2) Modèle OLAP : Dimensions + Faits                      │
-- └──────────────────────────────────────────────────────────┘

-- Dimension Date (dérivée de la feuille « Calendrier »)
CREATE TABLE IF NOT EXISTS dim_date (
    id_date        INT          PRIMARY KEY,      -- code de date Excel ou serial
    annee          SMALLINT     NOT NULL,         -- colonne 'annee'
    mois           SMALLINT     NOT NULL,         -- colonne 'mois'
    jour           SMALLINT     NOT NULL,         -- colonne 'jour'
    mois_nom       VARCHAR(20)  NOT NULL,         -- colonne 'mois_nom'
    annee_mois     INT          NOT NULL,         -- colonne 'annee_mois'
    jour_semaine   VARCHAR(10)  NOT NULL,         -- colonne 'jour_semaine' (1=Lundi…7=Dimanche)
    trimestre      VARCHAR(2)   NOT NULL          -- colonne 'trimestre' (ex: 'Q1')
);

-- Dimension Client (feuille « Clients »)
CREATE TABLE IF NOT EXISTS dim_client (
    id_client          VARCHAR(50)  PRIMARY KEY,  -- CUSTOMER_ID
    date_inscription   DATE         NOT NULL      -- colonne 'date_inscription'
);

-- Dimension Employé (feuille « Employé »)
CREATE TABLE IF NOT EXISTS dim_employe (
    id_employe     VARCHAR(50)  PRIMARY KEY,      -- id_employe
    employe        VARCHAR(100),                  -- nom d'utilisateur ou identifiant
    prenom         VARCHAR(50),                   -- prénom
    nom            VARCHAR(50),                   -- nom
    date_debut     DATE,                          -- date de début
    hash_mdp       VARCHAR(255),                  -- mot de passe hashé
    mail           VARCHAR(100)                   -- adresse e-mail
);

-- Dimension Produit (feuille « Produits »)
CREATE TABLE IF NOT EXISTS dim_produit (
    ean            BIGINT       PRIMARY KEY,      -- code EAN
    category       VARCHAR(100),                  -- catégorie
    rayon          VARCHAR(100),                  -- rayon ou département
    libelle        VARCHAR(200),                  -- description du produit
    prix           NUMERIC(10,2)                  -- prix unitaire
);

-- Table de faits Ventes (feuille « Vente Détail »)
CREATE TABLE IF NOT EXISTS faits_ventes (
    id_fait        VARCHAR(50)  PRIMARY KEY,      -- ID_BDD
    id_date        INT,                            -- référent à dim_date.id_date
    id_client      VARCHAR(50),                    -- référent à dim_client.id_client
    id_employe     VARCHAR(50),                    -- référent à dim_employe.id_employe
    ean            BIGINT,                         -- référent à dim_produit.ean
    id_ticket      VARCHAR(50)                     -- ID_TICKET
);

-- table de pré-chargement brute (tout en TEXT pour accepter n’importe quoi)
CREATE TABLE IF NOT EXISTS logs_stage (
  id_user      TEXT,
  event_time   TEXT,
  operation    TEXT,
  target_table TEXT,
  target_id    TEXT,
  field_name   TEXT,
  detail       TEXT
);

CREATE TABLE IF NOT EXISTS logs (
  log_id       SERIAL       PRIMARY KEY,
  id_user      VARCHAR(50),
  event_time   TIMESTAMP     NOT NULL,
  operation    VARCHAR(10),
  target_table VARCHAR(50),
  target_id    VARCHAR(50),
  field_name   VARCHAR(100),
  detail    TEXT

);