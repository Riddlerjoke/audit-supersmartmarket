# SuperSmartMarket - Plateforme d'Analyse de Données

## Contexte du Projet

SuperSmartMarket est une chaîne de supermarchés en plein développement en France qui redéfinit le concept du supermarché en intégrant des technologies de pointe pour rendre les courses rapides et agréables pour les consommateurs.

L'entreprise souhaite se démarquer en mettant l'accent sur l'hyper personnalisation de l'expérience en magasin avec des coupons promotionnels personnalisés, des recommandations basées sur les historiques d'achat, des recettes personnalisées en fonction des achats, etc.

SuperSmartMarket a besoin d'agrandir son équipe Data en recrutant un Data Engineer pour l'aider à comprendre et analyser les différents flux de données de l'entreprise. Jusqu'à présent, les Data Analysts se chargeaient de cette activité, mais les besoins récents en données ont conduit l'entreprise à vous recruter.

Vous êtes intégré à l'équipe Data Support. Cette équipe doit garantir la sécurité et la qualité des données pour l'ensemble de l'entreprise. Elle utilise une planification de processus avec des solutions Microsoft, un entrepôt de données de type OLAP et le support de l'application Microsoft PowerBI.

## Aperçu du Projet

Ce projet est une plateforme d'analyse de données pour SuperSmartMarket qui comprend :

- Une application backend FastAPI pour la gestion et l'analyse des données
- Une base de données PostgreSQL pour stocker les données OLAP (Online Analytical Processing)
- Des processus ETL (Extract, Transform, Load) pour charger des données à partir de fichiers Excel
- Des points d'accès API pour accéder aux tables de dimensions, aux tables de faits et aux analyses

La plateforme permet aux analystes de données et aux utilisateurs métier d'accéder et d'analyser les données de ventes, les informations clients, les données produits et les informations sur les employés pour prendre des décisions commerciales et personnaliser l'expérience client.

## Architecture

Le projet suit une architecture moderne de microservices :

- **Couche Base de Données** : Base de données PostgreSQL avec schéma OLAP (dimensions et faits)
- **Couche Backend** : Application FastAPI avec des routeurs pour différents domaines de données
- **Couche ETL** : Processus ETL basés sur Python pour le chargement et la transformation des données
- **Couche API** : Points d'accès API RESTful pour l'accès aux données et l'analyse

## Technologies Utilisées

- **Backend** : Python, FastAPI
- **Base de Données** : PostgreSQL
- **ORM** : SQLAlchemy
- **Traitement des Données** : Pandas
- **Conteneurisation** : Docker, Docker Compose
- **Format de Données** : Fichiers Excel pour l'importation de données

## Instructions d'Installation

### Prérequis

- Docker et Docker Compose installés sur votre système
- Git pour cloner le dépôt

### Étapes d'Installation

1. Cloner le dépôt :
   ```
   git clone <url-du-dépôt>
   cd audit-supersmartmarket
   ```

2. Créer les fichiers d'environnement :
   - Copier `.env.exemple` vers `.env`
   - Copier `backend/.env.exemple` vers `backend/.env`
   - Mettre à jour les variables d'environnement si nécessaire

3. Construire et démarrer les conteneurs :
   ```
   docker-compose up -d
   ```

4. L'application sera disponible à :
   - API Backend : http://localhost:8001
   - Base de données PostgreSQL : localhost:5433 (accessible avec les identifiants dans votre fichier .env)

## Instructions d'Utilisation

### Points d'Accès API

L'application fournit plusieurs points d'accès API :

- `/dim` - Accès aux tables de dimensions (dates, clients, employés, produits)
- `/faits` - Accès aux tables de faits (ventes)
- `/etl` - Points d'accès pour déclencher les processus ETL
- `/analytics` - Points d'accès d'analyse pour l'analyse des données
- `/logs` - Points d'accès de journalisation

### Chargement des Données

Les données peuvent être chargées dans le système en utilisant les points d'accès ETL ou en exécutant directement les scripts ETL :

1. Placez vos fichiers Excel dans le répertoire `backend/data`
2. Utilisez le point d'accès ETL pour charger les données :
   ```
   POST /etl/load-olap
   ```

   Ou exécutez directement le script ETL :
   ```
   docker exec -it fastapi_backend python -m backend.etl.load_olap backend/data/votre-fichier.xlsx
   ```

### Accès aux Analyses

Les analyses peuvent être accessibles via les points d'accès API :

```
GET /analytics/sales-by-date
GET /analytics/customer-insights
```

## Développement

### Structure du Projet

- `backend/` - Code de l'application FastAPI
  - `models/` - Modèles SQLAlchemy pour les tables de la base de données
  - `routers/` - Points d'accès API organisés par domaine
  - `etl/` - Scripts ETL pour le chargement des données
  - `data/` - Répertoire pour les fichiers de données
- `db/` - Scripts d'initialisation de la base de données
- `docker-compose.yml` - Configuration Docker Compose

### Ajout de Nouvelles Fonctionnalités

Pour ajouter de nouvelles fonctionnalités :

1. Créer ou modifier les modèles dans `backend/models/`
2. Créer ou mettre à jour les routeurs dans `backend/routers/`
3. Ajouter des processus ETL dans `backend/etl/` si nécessaire
4. Mettre à jour le schéma de la base de données dans `db/init.sql` si nécessaire

## Dépannage

- Si la connexion à la base de données échoue, vérifiez les variables d'environnement dans `.env`
- Si le chargement des données échoue, assurez-vous que vos fichiers Excel correspondent au format attendu
- Vérifiez les journaux des conteneurs pour des messages d'erreur détaillés :
  ```
  docker logs fastapi_backend
  docker logs postgres_db
  ```

## Licence

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

