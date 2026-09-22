-- Mirrors design/contracts/db/postgres.sql
CREATE TABLE IF NOT EXISTS items (
    id          bigserial PRIMARY KEY,
    name        text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
