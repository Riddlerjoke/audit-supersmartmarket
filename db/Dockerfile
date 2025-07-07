# Utilisation de l'image officielle PostgreSQL
FROM postgres:15

# Copier le script d'initialisation SQL dans le conteneur
COPY init.sql /docker-entrypoint-initdb.d/

# Exposer le port PostgreSQL
EXPOSE 5433