#!/usr/bin/env bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ing_user') THEN
      CREATE ROLE ing_user LOGIN PASSWORD '${ING_USER_PASSWORD}';
    ELSE
      ALTER ROLE ing_user WITH LOGIN PASSWORD '${ING_USER_PASSWORD}';
    END IF;
  END
  \$\$;

  CREATE DATABASE inglewood;
  GRANT CONNECT ON DATABASE inglewood TO ing_user;
EOSQL
