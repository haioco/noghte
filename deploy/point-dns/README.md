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
| Ubuntu 24.04 distro packages: PowerDNS Authoritative **4.8.3**, dnsdist **1.8.3** | Same feature set used by the Phase 0 design; pin to the PowerDNS 5.0 / dnsdist 1.9 repos before production beta |
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
  `dig +dnssec` returns RRSIGs. DS digests (API) are:
  `23361 13 1 7d542cd6c227520e600bc80bbf6365c55ff6d893`,
  `23361 13 2 8e51937e92bbfcaf4ccf49bb524ceef06a17ccf4f2060634ee9153f124763fd9`,
  `23361 13 4 9891173777f9f6f042329381ebda429325356fbbea79416a7a15613b185ccddf09462253a4ffae4ca259768b7a19b04e`.
- UPDATE queries get `NOTIMP`; a nonexistent name under the zone returns a proper
  authoritative `NXDOMAIN` (rc=3).
- Fresh installs can serve REFUSED until the serving instance's negative cache
  expires. The installer now purges that cache after zone/key creation and
  asserts the expected A answer before finishing.

## Not included in this task

- The Go control-plane (`point-api`, `point-worker`) and React panel.
- Second site / anycast, replication, TLS for the control plane, TOTP/RBAC.
- Public delegation of the health zone — it exists for authoritative verification only.
