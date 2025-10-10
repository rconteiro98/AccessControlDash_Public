# Use the official PostgreSQL 16 image as the base
FROM postgres:17

ENV PGPORT 5433

# Copia tu archivo postgresql.conf al contenedor
COPY postgresql.conf /etc/postgresql/postgresql.conf

# Copy initialization scripts into the image (if needed)
COPY initdb.sql /docker-entrypoint-initdb.d/init.sql

EXPOSE 5433
