# Product Documentation

This directory contains the accepted product contract and the purpose-specific
documents derived from product discovery and requirements.

## Current Product Authority

Read product artifacts in this order:

1. [`air-conditioner-advisor-m1-contract.md`](air-conditioner-advisor-m1-contract.md)
   — accepted Milestone 1 behavior.
2. Relevant Accepted ADRs in [`../decisions/`](../decisions/README.md) — only
   the named superseding rules take precedence over the contract.
3. [`requirements/air-conditioner-advisor-m1-prd.md`](requirements/air-conditioner-advisor-m1-prd.md)
   — approved Milestone 1 scope and requirements.
4. [`architecture/air-conditioner-advisor-m1.md`](architecture/air-conditioner-advisor-m1.md)
   — product-specific system design.

Discovery and reference material inform this authority chain but do not
override it:

- [`discovery/`](discovery/README.md)
- [`../references/`](../references/README.md)

## Update Rule

When product behavior changes:

1. Update the affected authoritative product artifact.
2. Update or create the bounded story packet.
3. Update durable proof status with the Harness CLI.
4. Record an ADR when the change affects architecture, scope, risk, or a
   previously accepted rule.

The full placement and conflict policy is in
[`../README.md`](../README.md).
