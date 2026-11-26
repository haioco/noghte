# Point DNS — Phase 0 single-node installation

This directory holds a **single-node adaptation** of the authoritative DNS hosting
service described in `point-handbook_v4.html` → Part 3 "طرح اجرایی Point DNS، نسخه ۱
(فاز ۰)" (rev 2), section "پیکربندی موتور DNS".

## What the handbook specifies

- PowerDNS Authoritative 5.0 with the **gpgsql** backend; data lives in PostgreSQL.
- `dnsdist` as a sidecar in front of the engine: rate limiting, ANY/UDP → TC,
  NOTIMP for UPDATE, TCP limits, metrics.
- **All writes go through the PowerDNS HTTP API** — never direct SQL. The serving
  DB role is read-only (`SELECT` only).
- 10-second query/negative/cache TTLs for fast propagation; `version-string=anonymous`,
  `disable-axfr=yes`, `any-to-tcp=yes`, no EDNS client subnet processing.
- DNSSEC with **algorithm 13 (ECDSA P-256)** and DS displayed to the user.
- API instance: `api=yes`, `webserver=yes` on a private address, `default-api-rectify=yes`,
  `soa_edit_api=DEFAULT`.
- Health zone `probe.pointdns.example` in the original design.

## Single-node deviations (documented on purpose)

| Handbook (two sites / Kubernetes) | This installation |
|---|---|
| Two sites, `ns1`/`ns2`, Postgres replication | One HaioFlash VM; `ns1.noghte-dns.example` / `ns2.noghte-dns.example` placeholders in SOA, no public delegation |
| Serving pods read from DB replica; separate `pdns-api` deployment | Two local processes: `pdns.service` (read-only, `127.0.0.1:5300`) and `pdns-api.service` (writer, API on `127.0.0.1:8081`) |
| dnsdist sidecar in pod | `dnsdist.service` on the same VM, public `:53` → `127.0.0.1:5300` |
| `dnstap` frame stream + third stats sidecar (week 5) | **Out of scope**; `dnsdist` webserver metrics on `127.0.0.1:8083` instead |
| Secrets from Vault/Sealed Secrets | Generated at install time into `/etc/noghte-dns/secrets.env`, mode `0600`, never committed |
| Ubuntu 24.04 distro packages: PowerDNS Authoritative **4.8.3**, dnsdist **1.8.3** | **Pinned to the official PowerDNS repositories** — Authoritative `noble-auth-50` (5.0.10) + dnsdist `noble-dnsdist-19` (1.9.16), key `0xFD380FBB`, installed by `install.sh` since 2026-11-26 |
| Handbook: ANY/UDP → TC via dnsdist | `any-to-tcp=yes` is set on the serving engine and a dnsdist `QTypeRule`/`TCAction` rule is present, but on dnsdist 1.8.3 the rule does **not** match ANY queries in our tests (A queries do truncate if a generic TC rule is added). Any small signed ANY answer is therefore returned over UDP. Revisit with the pinned 1.9 package before beta. |

## Install

On a fresh Ubuntu 24.04 VM with root SSH access:

```bash
scp deploy/point-dns/install.sh root@<vm-ip>:/root/install-point-dns.sh
ssh root@<vm-ip> 'bash /root/install-point-dns.sh'
```

The script installs PostgreSQL, PowerDNS, dnsdist and `dig`; creates the `pdns`
database with `pdns_rw` / `pdns_ro` roles; writes both configs and the dnsdist
config; enables the three services; creates the health zone through the HTTP API;
adds `www.<zone>` A → the VM's public IP; and enables DNSSEC.

## Verify

```bash
source /etc/noghte-dns/secrets.env
ZONE=probe.noghte-dns.example.
curl -sS -H "X-API-Key: $PDNS_API_KEY" \
  http://127.0.0.1:8081/api/v1/servers/localhost/zones/$ZONE | jq '.dnssec, .kind'
dig @127.0.0.1 www.$ZONE A +short
dig @127.0.0.1 $ZONE SOA +short
dig @127.0.0.1 $ZONE DNSKEY +dnssec +short | head -5
dig @<vm-ip> www.$ZONE A +short        # through dnsdist from outside the VM
systemctl is-active pdns pdns-api dnsdist
```

The DS record for delegation is obtained through the API (DNSSEC → DS, digest
type 2 / SHA-256) and is shown in the panel in the full product.

DNSSEC signature verification (needs `python3-dnspython`):

```bash
scp deploy/point-dns/verify-dnssec.py root@<vm-ip>:/root/
ssh root@<vm-ip> 'python3 /root/verify-dnssec.py'
```

```
[apex DNSKEY] probe.noghte-dns.example. DNSKEY: 1 rr(s); RRSIG alg=13 (13=ECDSAP256SHA256) keytag=10273 labels=3 ttl=300
[apex DNSKEY] SIGNATURE VALID
[www A] www.probe.noghte-dns.example. A: 1 rr(s); RRSIG alg=13 (13=ECDSAP256SHA256) keytag=10273 labels=4 ttl=60
[www A] SIGNATURE VALID
[negative control] tampered rrset correctly REJECTED (ValidationFailure)
RESULT: zone validates end to end (ECDSA P-256 / algorithm 13)
```

## Verified installation (2026-11-25)

Installed on HaioFlash VM `noghte-dns-01` (`94.182.172.96`, Ubuntu 24.04,
Flash Max). All three services (`pdns`, `pdns-api`, `dnsdist`) are active.

- Zone `probe.noghte-dns.example.` — `kind: Native`, `dnssec: true`,
  serial `2026112502`; NS `ns1`/`ns2.noghte-dns.example.` are placeholders.
- `www.probe.noghte-dns.example. A 94.182.172.96` returns correctly over
  UDP and TCP, both from the VM and externally through dnsdist on `:53`.
- `txt.verify.probe.noghte-dns.example. TXT "noghte-phase0-ok"` was written
  via `PATCH /api/v1/servers/localhost/zones/...` (HTTP 204), proving API-only
  writes work; the serving DB role is read-only.
- DNSSEC CSK: ECDSAP256SHA256 (alg 13), keytag `23361`, active and published;
  `dig +dnssec` returns RRSIGs. (On 2026-11-26 the zone was recreated during the
  hardening work and got keytag `10273`; the RRSIGs returned then were not
  verifiable signatures — the zone did not validate until the PowerDNS 5.0
  upgrade. Current DS digests are in the upgrade section below.)
- UPDATE queries get `NOTIMP`; a nonexistent name under the zone returns a proper
  authoritative `NXDOMAIN` (rc=3).
- Fresh installs can serve REFUSED until the serving instance's negative cache
  expires. The installer now purges that cache after zone/key creation and
  asserts the expected A answer before finishing.

## Not included in this task

- The Go control-plane (`point-api`, `point-worker`) and React panel.
- Second site / anycast, replication, TLS for the control plane, TOTP/RBAC.
- Public delegation of the health zone — it exists for authoritative verification only.

## Hardening pass (2026-11-26) — `harden.sh`

An independent audit of the live VM (`dig @94.182.172.96`) found four deviations
from the Phase 0 authoritative-only design:

| Finding | Evidence | Fix |
|---|---|---|
| ~~Out-of-zone recursion~~ — **invalid finding.** Externally `google.com`/`youtube.com` answered NOERROR with `qr ra ad` (TTL 418, `+norecurse` ignored), but from **inside the VM** (both loopback and its own public IP) those names return `REFUSED`, and the live dnsdist pool only ever contained `127.0.0.1:5300`. The external answers were produced by response-path interception on the audit network, not by this server. No change made. | `dig @94.182.172.96 google.com A` (external) vs `ssh … 'dig @127.0.0.1 google.com A'` (REFUSED) | none — verified authoritative-only |
| `id.server CHAOS TXT` → `"noghte-dns-01"` (hostname leak; `version.bind` hidden) | `dig @94.182.172.96 id.server CHAOS TXT +short` | CHAOS class ⇒ REFUSED |
| ANY not refused/truncated | `dig @94.182.172.96 www.probe.noghte-dns.example ANY` → NOERROR, no `tc` (the `DNSQtype.ANY` constant rule does not match on dnsdist 1.8.3) | ANY ⇒ REFUSED on UDP **and** TCP via numeric `QTypeRule(255)` |
| (same root cause) external upstream reachable | sinkhole `10.10.34.36` seen for facebook/instagram upstream answers | removed with the pool rewrite |

Files:

- `dnsdist.conf` — the canonical config (placeholders `@DNSDIST_WEB_PASSWORD@` /
  `@DNSDIST_API_KEY@` are substituted from `/etc/noghte-dns/secrets.env`).
  Syntax-checked under a stubbed dnsdist environment (`luac -p` + stubbed globals
  load clean). `install.sh` now installs this file instead of an inline heredoc.
  **Applied live on 2026-11-26** (`harden.sh`, all assertions green): ANY → REFUSED,
  CHAOS → REFUSED, `www.probe` A/TXT unaffected, UPDATE → NOTIMP, `+dnssec` NOERROR.
  Note: the first config attempt used `DNSClass.CH` / `DNSQType.ANY` constants —
  both are **nil on dnsdist 1.8.3** (`dnsdist --check-config` fails with
  "Unable to convert parameter from nil"), so the config uses the numeric
  `QClassRule(3)` (CHAOS) and `QTypeRule(255)` (ANY) instead.
- `harden.sh` — the one-shot pass for the **already-installed** VM: backs up the
  live config, writes the canonical one, validates, restarts, then asserts:
  `www.probe` still answers `94.182.172.96`, `google.com`/`youtube.com` →
  REFUSED, ANY → REFUSED, CHAOS → REFUSED, UPDATE → NOTIMP, `+dnssec` → NOERROR
  (RRSIGs intact). Rolls back on any failure.

Because the VM is not reachable from the workstation that wrote this (the SSH key
attached to `noghte-dns-01` belongs to a different host, and the panel key-attach
API returned 400), the pass has **not** been applied to the live node yet. Run
it as root:

```bash
scp -r deploy/point-dns root@94.182.172.96:/root/
ssh root@94.182.172.96 'bash /root/point-dns/harden.sh'
```

## Applied live on 2026-11-26 — state and two new findings

`harden.sh` ran on `noghte-dns-01` after installing an SSH key; every assertion
passed (`www.probe` A `94.182.172.96`, `google.com`/`youtube.com` REFUSED,
ANY/CHAOS REFUSED, SOA NOERROR, `+dnssec` NOERROR, UPDATE NOTIMP).

Two findings from the zone work that day, both worth knowing before beta:

1. **`pdns_control purge` is not enough after a zone (re)create.** On an existing
   database, the serving instance keeps answering REFUSED for a recreated zone;
   only a full `systemctl restart pdns` reloads it. `install.sh` now restarts
   rather than purging. (Verified: after delete+recreate the zone served
   REFUSED through dnsdist while `dig @127.0.0.1 -p 5300` answered correctly.)
2. **RRSIG signing does not happen on distro pdns 4.8.3 + gsql.** The zone has
   DNSKEY published and DS retrievable through the API (keytag 10273, alg 13),
   but `rectify` (HTTP 200) never writes RRSIG rows (`records` stays at
   A/TXT/SOA/NS only), so the zone does not actually validate. Both instances
   run `gpgsql-dnssec=yes`; this is a bootstrap defect of the distro packages,
   not configuration. **Pin the PowerDNS 5.0 repositories before beta** (already
   the plan) and re-verify DNSSEC there; the probe zone has no delegation today,
   so nothing is broken publicly. → **Closed 2026-11-26 by the upgrade below.**

## PowerDNS 5.0 / dnsdist 1.9 upgrade (applied live on 2026-11-26)

`noghte-dns-01` was pinned to the official PowerDNS repositories and upgraded:
**PowerDNS Authoritative 5.0.10** (was 4.8.3) and **dnsdist 1.9.16** (was 1.8.3).
`install.sh` now performs the same pinning on a fresh node (key, sources, apt
pinning), so new installs land on the handbook versions directly.

Evidence after the upgrade (all against `127.0.0.1:53`, through dnsdist):

- Serving intact: `www.probe.noghte-dns.example A` → `94.182.172.96` (UDP + TCP).
- Hardening intact (`harden.sh`, exit 0, 8/8 OK): `google.com`/`youtube.com`
  → REFUSED, ANY → REFUSED, `id.server CHAOS TXT` → REFUSED, UPDATE →
  NOTIMP, SOA/`+dnssec` → NOERROR.
- **DNSSEC now signs**: `PUT /rectify` returns RRSIG-bearing rrsets — `dig
  +dnssec` shows RRSIG for DNSKEY (alg 13, keytag 10273), A, SOA, NS and TXT.
  `verify-dnssec.py` (dnspython, in this directory) verifies the signatures
  cryptographically and additionally rejects a tampered rrset:
  `[apex DNSKEY] SIGNATURE VALID`, `[www A] SIGNATURE VALID`,
  `[negative control] tampered rrset correctly REJECTED`.
- DS digests for delegation (API `cryptokeys[].ds`, keytag 10273, alg 13):
  `10273 13 2 1d67214d619554d800a633dbe8b21692796436b66ef590942fff3f9a2fa5ce71`,
  `10273 13 4 a2420106459ad2035c3fd420c41c54cfd9ce3b95964d07f045b8893f5765ba5ec45339f20b058be0cd96892f8b232df1`.

Two defects found while doing this, both fixed and documented:

1. **`control-console` (as an explicit socket path) is fatal on pdns 5.0.** The
   API instance started, bound `127.0.0.1:8081`/`:5301`, then died with
   `Fatal error in control listener: Guardian exited - going down as well`
   (with the guardian on, additionally `Unknown command: 'ECHO'`). The distro
   unit meanwhile runs fine because it passes `--guardian=no`. The control socket
   now lives in `socket-dir`, which under systemd is `$RUNTIME_DIRECTORY`
   (`--socket-dir` help: "Set to the RUNTIME_DIRECTORY environment variable").
   Fix: drop `control-console` from `/etc/powerdns-api/pdns.conf` and start the
   unit with `--guardian=no --daemon=no` (like `/usr/lib/systemd/system/pdns.service`).
2. **This VM runs `policy-rc.d` → package upgrades do not restart services**
   (`invoke-rc.d: policy-rc.d denied execution of restart`). After an apt
   upgrade the old binary keeps serving until an explicit
   `systemctl restart pdns pdns-api dnsdist`; `install.sh` already restarts
   explicitly, so re-running it after a package upgrade is the supported path.

Also fixed in `harden.sh`: `nsupdate` exits **2** when the server refuses an
update ("update failed: NOTIMP") — i.e. exactly the expected outcome — and with
`set -euo pipefail` that aborted the script before the UPDATE assertion and the
final log line. The pipelines now end in `|| true` and the assertion is made on
the parsed text.
