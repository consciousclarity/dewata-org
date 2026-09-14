-- ============================================================================
-- 0001.down -- rollback of 0001_initial_schema
--
-- WARNING: this drops ALL data in the public schema.  it is intended
-- for disposable test environments only.  do NOT run on production.
--
-- equivalent to dropping everything in public.  the migration runner
-- will then record the version as "rolled back" in schema_migrations
-- (the runner drops the schema_migrations table itself so the table
-- gets recreated on the next up).
-- ============================================================================

BEGIN;
-- tables and functions: cascade handles dependent objects
DROP TABLE IF EXISTS schema_migrations CASCADE;
DROP TABLE IF EXISTS ceremony_ruleset_ref CASCADE;
DROP TABLE IF EXISTS evidence_blob CASCADE;
DROP TABLE IF EXISTS ceremony_authority_link CASCADE;
DROP TABLE IF EXISTS ceremony_source CASCADE;
DROP TABLE IF EXISTS ceremony_state CASCADE;
DROP TABLE IF EXISTS ceremony CASCADE;
DROP TABLE IF EXISTS pura_relationship CASCADE;
DROP TABLE IF EXISTS pura CASCADE;
DROP TABLE IF EXISTS banjar CASCADE;
DROP TABLE IF EXISTS desa_adat CASCADE;
DROP TABLE IF EXISTS kabupaten CASCADE;
DROP TABLE IF EXISTS authority_delegation CASCADE;
DROP TABLE IF EXISTS actor CASCADE;

-- enums (post-CASCADE)
DROP TYPE IF EXISTS evidence_kind;
DROP TYPE IF EXISTS ceremony_phase;
DROP TYPE IF EXISTS ceremony_class;
DROP TYPE IF EXISTS visibility_tier;
DROP TYPE IF EXISTS authority_role;

-- functions
DROP FUNCTION IF EXISTS ceremony_state_append_only();
DROP FUNCTION IF EXISTS ceremony_append_only();

COMMIT;
