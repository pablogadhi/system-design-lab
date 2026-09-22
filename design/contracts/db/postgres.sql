-- Authoritative schema for the `app` database (component: postgres).
-- Owning service: sample-api (copies this into src/sample_api/migrations/0001_items.sql).
CREATE TABLE IF NOT EXISTS items (
    id          bigserial PRIMARY KEY,
    name        text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
