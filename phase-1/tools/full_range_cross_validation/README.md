# Full-range cross-validation harness

This harness executes Dewata and two immutable upstream implementations for
every Gregorian date from 1900-01-01 through 2099-12-31 (73,049 dates).
It does not alter or propose calendar rules.

## Pinned upstreams

- Peradnya TypeScript 0.4.3 at
  `da4193c26cc73c67a3dd82bb3281b27cc4f20dc4`
- SHA888 Rust 0.3.0 at
  `bbc82ff0dc73768a854b2e2183300e7a6c42f259`

`provenance.json` records the repository, tag object, commit, license, retrieval
date, and SHA-256 of every source file used. The Rust dependency resolution is
preserved in `rust-Cargo.lock`. Peradnya's own `package-lock.json` hash is pinned.

## Reproduction

Use clean, temporary checkouts at the commits above. Do not install either
historical dependency graph into a production environment.

1. In the Peradnya checkout, run `npm ci --ignore-scripts`, followed by
   `npm run build:nodejs`.
2. In the Rust checkout, copy `rust-Cargo.lock` to `Cargo.lock`, copy
   `rust_adapter.rs` to `examples/full_range_adapter.rs`, then run
   `cargo build --locked --release --example full_range_adapter`.
3. From `phase-1/`, run:

   `python tools/full_range_cross_validation/run.py --peradnya-root PATH --rust-root PATH --rust-binary PATH/target/release/examples/full_range_adapter --output-dir evidence/cross-validation/1900-2099`

The runner verifies source hashes before execution, forces `TZ=UTC` for the
legacy JavaScript date code, fails on any adapter error or row-count mismatch,
and emits deterministic gzip files (`mtime=0`).

## Security and legal boundary

Both upstreams identify as Apache-2.0. Only small adapter code, provenance,
dependency lock data, and generated observations are committed here; upstream
source is not vendored. The historical Peradnya lock resolved 753 packages and
the local package-manager audit reported 77 known vulnerabilities. It is used
only as an isolated evidence generator with install scripts disabled in the
documented reproduction path. It is not a Dewata runtime dependency.

Implementation agreement is not customary authority. The normalized output is
analytical and must never be substituted for the preserved raw output.
