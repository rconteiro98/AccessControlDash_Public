# Use the official PostgreSQL 16 image as the base
FROM postgres:17

ENV PGPORT 5433

# Copy the PostgreSQL config into the image
COPY postgres-custom.conf /etc/postgresql/postgresql.conf

# Copy the schema initialization script into the image
COPY init_schema.sql /docker-entrypoint-initdb.d/init.sql

EXPOSE 5433
