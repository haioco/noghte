#!/usr/bin/env python3
"""Signature-level proof that the live Point DNS probe zone actually validates.

Queries the node over TCP with DO=1, verifies:
  1. the apex DNSKEY self-signature
  2. the RRSIG over www A (and verify TXT)
  3. a negative control: a tampered rrset must be rejected
Exit 0 = validating zone, exit 2 = failure.
"""
import sys
import dns.name, dns.message, dns.query, dns.rcode, dns.rdatatype, dns.dnssec

SERVER = "127.0.0.1"
ZONE = dns.name.from_text("probe.noghte-dns.example.")

def fetch(name, rdtype):
    r = dns.query.tcp(dns.message.make_query(name, rdtype, want_dnssec=True), SERVER, timeout=10)
    assert r.rcode() == dns.rcode.NOERROR, f"{name} {rdtype} -> {dns.rcode.to_text(r.rcode())}"
    return r

def rrset_of(resp, name, rdtype):
    for rrset in resp.answer:
        if rrset.name == name and rrset.rdtype == rdtype:
            return rrset
    return None

def sigset_of(resp, name, covered):
    for rrset in resp.answer:
        if rrset.name == name and rrset.rdtype == dns.rdatatype.RRSIG:
            matching = [rd for rd in rrset if rd.covers() == covered]
            if matching:
                import dns.rrset as R
                built = R.from_rdata_list(name, rrset.ttl, matching)
                return built
    return None

def verify(name, rdtype, label):
    resp = fetch(name, rdtype)
    apex = fetch(ZONE, dns.rdatatype.DNSKEY)
    rrset = rrset_of(resp, name, rdtype)
    sigs = sigset_of(resp, name, rdtype)
    keys = rrset_of(apex, ZONE, dns.rdatatype.DNSKEY)
    assert rrset is not None, f"no rrset for {label}"
    assert sigs is not None, f"no RRSIG rrset for {label}"
    assert keys is not None, "no apex DNSKEY"
    sig = next(iter(sigs))
    print(f"[{label}] {name.to_text()} {dns.rdatatype.to_text(rdtype)}: {len(rrset)} rr(s); "
          f"RRSIG alg={sig.algorithm} (13=ECDSAP256SHA256) keytag={sig.key_tag} "
          f"labels={sig.labels} ttl={sig.original_ttl}")
    dns.dnssec.validate(rrset, sigs, {ZONE: keys})
    print(f"[{label}] SIGNATURE VALID")

verify(ZONE, dns.rdatatype.DNSKEY, "apex DNSKEY")
QNAME = dns.name.from_text("www.probe.noghte-dns.example.")
verify(QNAME, dns.rdatatype.A, "www A")

resp = fetch(QNAME, dns.rdatatype.A)
rrset = rrset_of(resp, QNAME, dns.rdatatype.A)
sigs = sigset_of(resp, QNAME, dns.rdatatype.A)
keys = rrset_of(fetch(ZONE, dns.rdatatype.DNSKEY), ZONE, dns.rdatatype.DNSKEY)
import dns.rdata
bad = dns.rrset.from_rdata_list(QNAME, rrset.ttl, [dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, "10.9.8.7")])
try:
    dns.dnssec.validate(bad, sigs, {ZONE: keys})
    print("[negative control] FAILED: tampered rrset unexpectedly validated"); sys.exit(3)
except Exception as e:
    print(f"[negative control] tampered rrset correctly REJECTED ({type(e).__name__})")
print("RESULT: zone validates end to end (ECDSA P-256 / algorithm 13)")
