-- ============================================================================
-- 0001 -- initial schema for dewata cultural infrastructure
--
-- target:   postgis 3.4+, postgresql 16+
-- engine:   postgres + postgis + uuid-ossp
-- scope:    cultural_record / registry layer ONLY (calendar engine lives
--           in `phase-1/src/dewatacalendar/` and is unaffected)
--
-- DESIGN NOTES (provisional -- pending `phase-1/docs/runbook/SIGNOFF.md`
-- entries):
--
--   - all enums use a DO-block guard so the migration is re-runnable
--     against a not-perfectly-clean state (postgres has no native
--     "IF NOT EXISTS" for CREATE TYPE).
--
--   - identity uses uuid (uuid-ossp extension).  external handles
--     (kab_CODE-0001 style) are column-level not key-level, so
--     renames can evolve without migrations.
--
--   - actor.id is the canonical id; row-level authority and
--     delegation are stored separately.  no real names are stored --
--     only code-shaped identifiers.
--
--   - ceremony_state (the audit table) is **append only** via a
--     write-time trigger (`ceremony_state_append_only`) that blocks
--     UPDATE/DELETE on filled rows.  history is preserved even if a
--     role or system error tries to overwrite it.
--
--   - visibility tiers + roles are typed enums; the tier policy
--     itself lives in the application layer (see
--     `dewatacalendar.security`).
--
--   - "DELETE" on most tables is RESTRICTED (no ON DELETE CASCADE)
--     to preserve history.  the soft-delete columns `is_archived`
--     let records be removed from public-facing views without
--     erasing cultural history.
--
--   - the migrations are NOT applied to any production database as
--     of this commit.  only the disposable test container
--     (dewata-disposable-test) has seen them.
--
--   - until customary sign-off exists, every column is provisional.
-- ============================================================================

BEGIN;

-- ===== extensions =====
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== enums (idempotent via DO blocks) =====

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='authority_role') THEN
        CREATE TYPE authority_role AS ENUM (
            'pemangku',
            'pemangku_keramas',
            'kelian_adat',
            'bendesa_adat',
            'pekalang',
            'banjar_operator',
            'dewata_admin',
            'dewata_editor'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='visibility_tier') THEN
        CREATE TYPE visibility_tier AS ENUM (
            'public', 'banjar', 'desa_adat', 'restricted', 'private'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='ceremony_class') THEN
        CREATE TYPE ceremony_class AS ENUM (
            'piodalan',
            'odalan_utama',
            'odalan_madya',
            'melasti',
            'paruman'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='ceremony_phase') THEN
        CREATE TYPE ceremony_phase AS ENUM (
            'predicted',
            'confirmed',
            'occurring',
            'completed',
            'cancelled'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='evidence_kind') THEN
        CREATE TYPE evidence_kind AS ENUM (
            'photo', 'audio', 'document', 'video', 'link'
        );
    END IF;
END $$;

-- ===== actor / identity =====

CREATE TABLE actor (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    kind text NOT NULL,                -- 'person' | 'organization' | 'system'
    handle text UNIQUE NOT NULL,        -- canonical short ref like "actor:dewata-admin"
    display_name text NOT NULL,        -- rendered name; can be a code-shape pseudonym
    role authority_role NOT NULL,
    banjar_id uuid,                    -- nullable for system actors
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by_actor_id uuid,
    archived_at timestamptz
);

CREATE INDEX actor_handle_idx ON actor(handle);
CREATE INDEX actor_role_idx ON actor(role);
CREATE INDEX actor_banjar_idx ON actor(banjar_id) WHERE banjar_id IS NOT NULL;

-- ===== authority delegation (provisional) =====

CREATE TABLE authority_delegation (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    delegator_id uuid NOT NULL REFERENCES actor(id),
    delegate_id uuid NOT NULL REFERENCES actor(id),
    scope text NOT NULL,                -- dotted path like "ceremony.update"
    begins_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    reason text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX auth_deleg_chain_idx
    ON authority_delegation(delegator_id, delegate_id, begins_at DESC);

-- ===== geography =====

CREATE TABLE kabupaten (
    code char(4) PRIMARY KEY,           -- kab3 (e.g. 'gianyar')
    name text NOT NULL,
    province_code char(2) NOT NULL DEFAULT 'ba',
    geom geometry(MultiPolygon, 4326),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE desa_adat (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    kabupaten_code char(4) NOT NULL REFERENCES kabupaten(code),
    handle text UNIQUE NOT NULL,        -- desa_adat:kab_code
    display_name text NOT NULL,
    geom geometry(MultiPolygon, 4326),
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE INDEX desa_adat_kab_idx ON desa_adat(kabupaten_code);

CREATE TABLE banjar (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    kabupaten_code char(4) NOT NULL REFERENCES kabupaten(code),
    handle text UNIQUE NOT NULL,        -- bjr:kab_code
    display_name text NOT NULL,
    desa_adat_id uuid REFERENCES desa_adat(id),
    geom geometry(MultiPolygon, 4326),
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE INDEX banjar_kab_idx ON banjar(kabupaten_code);
CREATE INDEX banjar_desa_idx ON banjar(desa_adat_id);

-- ===== pura (temple) =====

CREATE TABLE pura (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    kabupaten_code char(4) NOT NULL REFERENCES kabupaten(code),
    handle text UNIQUE NOT NULL,
    display_name text NOT NULL,
    pura_kind text,                    -- 'kahyangan tiga' | 'kahyangan jagat' | etc.
    banjar_id uuid REFERENCES banjar(id),
    geom geometry(Point, 4326),
    created_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE INDEX pura_kab_idx ON pura(kabupaten_code);
CREATE INDEX pura_banjar_idx ON pura(banjar_id) WHERE banjar_id IS NOT NULL;

CREATE TABLE pura_relationship (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id uuid NOT NULL REFERENCES pura(id),
    child_id uuid NOT NULL REFERENCES pura(id),
    kind text NOT NULL,                -- 'sister' | 'precursor' | etc.
    valid_from timestamptz NOT NULL DEFAULT now(),
    valid_until timestamptz,
    source_url text,
    UNIQUE(parent_id, child_id, kind)
);

-- ===== ceremony core =====

CREATE TABLE ceremony (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    banjar_id uuid NOT NULL REFERENCES banjar(id),
    pura_id uuid REFERENCES pura(id),
    class ceremony_class NOT NULL,
    title text NOT NULL,
    external_handle text UNIQUE NOT NULL,        -- e.g. "CR-GIA-0001"
    visibility visibility_tier NOT NULL DEFAULT 'banjar',
    scheduled_for date,                          -- calendar date (NULL = floating)
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by_actor_id uuid REFERENCES actor(id),
    archived_at timestamptz
);

CREATE INDEX ceremony_banjar_idx ON ceremony(banjar_id);
CREATE INDEX ceremony_pura_idx ON ceremony(pura_id) WHERE pura_id IS NOT NULL;
CREATE INDEX ceremony_class_idx ON ceremony(class);
CREATE INDEX ceremony_scheduled_idx ON ceremony(scheduled_for)
    WHERE scheduled_for IS NOT NULL;

CREATE TABLE ceremony_state (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    ceremony_id uuid NOT NULL REFERENCES ceremony(id),
    state ceremony_phase NOT NULL,
    reason text,
    observed_at timestamptz NOT NULL DEFAULT now(),
    actor_id uuid REFERENCES actor(id),
    source_url text,
    evidence_blob_id uuid
);

CREATE INDEX ceremony_state_idx ON ceremony_state(ceremony_id, observed_at DESC);

-- append-only enforcement: `ceremony_state` rows cannot be updated/deleted.
CREATE OR REPLACE FUNCTION ceremony_state_append_only()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'ceremony_state is append only (id=%)', OLD.id
        USING ERRCODE = 'integrity_constraint_violation';
END $$;

CREATE TRIGGER ceremony_state_no_update BEFORE UPDATE ON ceremony_state
    FOR EACH ROW EXECUTE FUNCTION ceremony_state_append_only();
CREATE TRIGGER ceremony_state_no_delete BEFORE DELETE ON ceremony_state
    FOR EACH ROW EXECUTE FUNCTION ceremony_state_append_only();

-- ===== sources and provenance =====

CREATE TABLE ceremony_source (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    ceremony_id uuid NOT NULL REFERENCES ceremony(id),
    authority_id uuid REFERENCES actor(id),
    captured_at timestamptz NOT NULL DEFAULT now(),
    source_url text,
    notes text
);

CREATE TABLE ceremony_authority_link (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    ceremony_id uuid NOT NULL REFERENCES ceremony(id),
    actor_id uuid NOT NULL REFERENCES actor(id),
    role text NOT NULL,                -- 'confirming' | 'organising' | 'observing'
    begins_at timestamptz NOT NULL DEFAULT now(),
    ends_at timestamptz
);

CREATE INDEX ceremony_authority_link_actor_idx
    ON ceremony_authority_link(actor_id, ceremony_id);

-- ===== evidence files =====

CREATE TABLE evidence_blob (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    kind evidence_kind NOT NULL,
    sha256 char(64) NOT NULL,
    byte_length bigint NOT NULL,
    storage_uri text NOT NULL,         -- object storage ref like "s3://…"
    uploaded_at timestamptz NOT NULL DEFAULT now(),
    uploaded_by_actor_id uuid REFERENCES actor(id),
    UNIQUE(sha256)
);

-- ===== calendar ruleset reference =====

CREATE TABLE ceremony_ruleset_ref (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    ceremony_id uuid NOT NULL REFERENCES ceremony(id),
    ruleset_version text NOT NULL,     -- e.g. "pawukon-v0.4.1+saka-bali-v0.2.3"
    computation_method text NOT NULL,  -- 'engine:produce' | 'human:override'
    overrides jsonb,                   -- optional corrections per row
    UNIQUE(ceremony_id, ruleset_version)
);

-- ===== write-time guards =====

CREATE OR REPLACE FUNCTION ceremony_append_only()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'ceremony rows are append-only outside '
        'the api layer (id=%)', OLD.id
        USING ERRCODE = 'integrity_constraint_violation';
END $$;

CREATE TRIGGER ceremony_no_update BEFORE UPDATE ON ceremony
    FOR EACH ROW EXECUTE FUNCTION ceremony_append_only();
CREATE TRIGGER ceremony_no_delete BEFORE DELETE ON ceremony
    FOR EACH ROW EXECUTE FUNCTION ceremony_append_only();

-- ===== provisional grants for the `dewata` role =====
-- production role is **read-mostly** at first.  write access goes
-- through the api.  if your prod role has different grants, override
-- this block in a later migration.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='dewata') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA public TO dewata';
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA public TO dewata';
        EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dewata';
    END IF;
END $$;

-- ===== migration-runner bookkeeping table =====
-- maintained by `phase-1/src/dewatacalendar/db/__init__.py` once
-- the migration runs successfully.

CREATE TABLE IF NOT EXISTS schema_migrations (
    id serial PRIMARY KEY,
    version text NOT NULL UNIQUE,
    description text,
    applied_at timestamptz NOT NULL DEFAULT now(),
    checksum text,
    rollback_present boolean NOT NULL DEFAULT false
);

-- ===== seed data (synthetic-only) =====
-- the seed rows below use obviously fictional names so that no
-- mistaking them for canonical "gianyar" records is possible.
-- see `phase-1/tests/db/fixtures.py` and the SECURITY note in the
-- threat-model doc (`phase-1/docs/security/MODEL.md`).

INSERT INTO kabupaten (code, name) VALUES
    ('gbxx', 'PLACEHOLDER county __TEST__'),
    ('gaau', 'PLACEHOLDER county __TEST__')
ON CONFLICT (code) DO NOTHING;

COMMIT;
