# ADR-0002 — snapshot signing

> status: **proposed**
> date: 2026-09-14
> scope: choosing a signing mechanism for the periodic cultural-record
>        snapshots
> note: this ADR **does not** choose or generate keys.  selection
>       depends on human review of the threat model plus operational
>       constraints, which sit outside this run's scope.

## 1. background

we want to publish periodic signed snapshots of the cultural-record
state so that consumers can verify the integrity of the data they
hold.  snapshots are immutable AT THE TIME OF SIGNING — the act of
signing freezes a checksum and a ruleset version.

threat model:

- T-1  cryptographic forgery:  a malicious actor mints a snapshot
  claiming to come from dewata.org.
- T-2  silent tamper:  a redirect or man-in-the-middle replaces an
  honest snapshot with a different one.
- T-3  replay:  an old snapshot is re-published; consumers accept
  it as fresh.
- T-4  key compromise:  signing key is leaked; attacker can re-mint
  any snapshot.
- T-5  rollback attack:  an old valid snapshot is used as the basis
  for re-issuing state.

non-goals:

- encryption (snapshots are public; signatures verify, not encrypt).
- per-row authentication.  if a future protocol needs row-level
  signed proofs, that's a separate ADR.
- identity binding to a real person or institution.  dewata.org
  signs as the protocol, not as any individual.

## 2. evaluation criteria

- C-1  **canonical byte representation**.  the signature must
       apply to a deterministic byte encoding, not to a volatile
       JSON pretty-print.
- C-2  **detached signatures**.  the signature lives next to the
       snapshot, not interleaved.
- C-3  **public-key discovery**.  a verifier must be able to fetch
       the public key independently of the snapshot itself.
- C-4  **offline verification**.  no live service lookup required
       to verify a snapshot.
- C-5  **key custody**.  the key must be storable on a hardware
       device or in a paper backup; rotating it must not depend
       on a vendor service.
- C-6  **rotation and revocation**.  rotation is supported by
       protocol; old signatures remain valid with the corresponding
       old key (kept for the verification window).
- C-7  **historical verification**.  verifiers can confirm any
       historical snapshot.
- C-8  **reproducible snapshot construction**.  given the same
       input, the byte string is identical.  canonical encoding.
- C-9  **failure modes and rollback**.  documented procedure if
       signing hardware fails or a signature is found bad.
- C-10 **standard tooling**.  reasonable third-party tooling exists
       to verify signatures; we do not invent a new format.
- C-11 **liberal license**.  no proprietary encumbrance.

## 3. options considered

### option A — ed25519 via maintained lib

reference: `cryptography` (PyCA), `ed25519-dalek` (Rust), etc.

| criterion | result |
|---|---|
| C-1 canonical bytes   | yes — explicit canonical encoding (RFC 8032) |
| C-2 detached          | yes — `.sig` companion file |
| C-3 pubkey discovery  | yes — `.pub` companion file; can ship in `/.well-known` |
| C-4 offline           | yes |
| C-5 custody           | yes — single 32-byte private key fits in hardware tokens (yubikey), encrypted file, paper backup (via base32 / matrix codes) |
| C-6 rotation          | yes — versioned pubkey in metadata |
| C-7 historical        | yes — verifiers retain old pubkeys by version |
| C-8 reproducible      | yes — define canonical encoding (`json.dumps(..., sort_keys=True, ensure_ascii=False, separators=...)`) |
| C-9 failure modes     | documented; rotation path verified |
| C-10 standard tooling | yes — openssl `ed25519` support; `age` accepts ed25519 recipients |
| C-11 liberal license  | yes — public domain spec, BSD-style libs |

threat coverage:
- T-1 forgery:  cannot be done without private key.
- T-2 tamper:   a tampered snapshot has a different canonical-bytes;
                sig verification fails.
- T-3 replay:   consumers should pin a threshold (ruleset_version +
                snapshot_date); replay protection lives in client policy.
- T-4 key compromise:  mitigated by rotation + revocation list.
- T-5 rollback:  mitigated by versioning.

operational note:
- the **private key never** appears in chat, env files outside
  `/root/.env.dewata.online`, or git history.
- generated and stored off this vps, ideally on a hardware token.

### option B — minisign-compatible signatures

reference: `minisign` and `signify`.

| criterion | result |
|---|---|
| C-1..C-11 | largely matches option A; minisign uses ed25519 with a slightly different wire format.  |

evaluator's note: mostly the same as option A in security profile.
slightly easier to verify from the command line (`minisign -V`).
slightly less commonly supported outside macOS/Linux CLI communities.

### option C — sigstore / cosign

reference: `cosign sign --key …`, `sigstore.dev`.

| criterion | result |
|---|---|
| C-1..C-7 | mostly supported |
| C-8 reproducible | yes — if both producer and verifier consume the same bytes |
| C-10 standard tooling | wide adoption in OCI supply-chain space |
| C-11 liberal license | apache 2.0 |

threat coverage:
- T-1 through T-5: covered.
- ADDS:
  - T-6 transparency log tampering:  mitigated by inclusion in
    sigstore's transparency log.  downside: introduces a
    third-party (fulcio + rekor) into the trust chain.  this is
    non-trivial for a culture-first community project — it binds
    signatures to a vendor service.

evaluator's note:
- the transparency-log benefit is real for greenfield projects
  adopting binaries through CI.  for a culture-first data
  publishing pipeline, this introduces a vendor dependency that
  does not yet have a community understanding.
- the trade-off is convenience vs autonomy.  at v0.1 we
  recommend deferring this.

### option D — pki x.509 / rsa

| criterion | result |
|---|---|
| C-1..C-11 | supported, but heavy: requires certificate chain management. |
| ease of attack | PKI signature paths can drift; cross-cert scenarios are easy to misconfigure. |

evaluator's note:
- x.509 is well-known in the tls world but adds operational
  weight that ed25519 alternatives do not have.
- not recommended for v0.1 unless we later decide to use an
  existing trust anchor.

### option E — age (encryption tool)

the brief explicitly forbids using age for signing.  age is an
encryption tool with no standardised detached-signature flow.
this is **not** evaluated further — age is rejected.

## 4. recommendation

**option A (ed25519) is the default for v0.1** with the following
operating rules:

1. canonical encoding:  `json.dumps(record, sort_keys=True,
   ensure_ascii=False, separators=(",", ":"))`  +  b"\n"  +
   ruleset_version + "\n" + iso8601_utc_timestamp + "\n"
2. detached signature at `<snapshot>.sig` (ed25519 over canonical
   bytes).
3. public key at `/.well-known/dewata-snapshot-key.pub` with a
   `version` integer prefix (rotation-aware).
4. **at this stage we DO NOT generate the keypair.**  a separate
   ops runbook will produce and store the private key on a
   hardware token.  the public key will be published alongside
   the first signed snapshot.

## 5. transition to production

1. (separate ops run) **generate and store** the private key
   on a yubikey or paper backup, outside chat history.
2. publish the public key with `version=1` and a creation date.
3. enable signing for `datasets.dewata.org/snapshots/<...>`.
4. document verification commands in `phase-1/docs/runbook/VERIFY.md`.
5. (later) provide a `-C sigstore` switch to allow cosign-style
   transparency-log signing if the community later asks for it.

## 6. what this ADR does not decide

- which pubkey distribution mechanism (`/.well-known`, signed
  manifest, or DNS).
- how often rotation happens (annually? on staff turnover? on
  key event?).
- how long historical keys are retained.
- verifier-side policy for replay / rollback — that's a
  *client* concern.

## 7. acceptance criteria (per the brief)

- [x] covers threat model
- [x] covers canonical byte representation (item 1 above)
- [x] covers detached signature format (item 2)
- [x] covers public-key discovery (item 3)
- [x] covers offline verification (item 4)
- [x] covers key custody (item 1, deferred ops detail)
- [x] covers rotation and revocation (items 4-5)
- [x] covers historical verification (item 4)
- [x] covers reproducible snapshot construction (item 1)
- [x] covers failure modes and rollback (items 1 + 5)
