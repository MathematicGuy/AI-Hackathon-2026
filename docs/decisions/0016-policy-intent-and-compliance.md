# 0016 Policy Intent and Compliance Behavior

Date: 2026-07-18

## Status

Accepted

## Context

Real policy documents now live in the dataset (warranty/return with monthly fee
schedules, delivery/installation fees and time windows, Apple unboxing, personal
data handling, terms of use). The product owner requires the agent to: ingest
policies **only when actually needed** based on user intent; comply with them
strictly; **quote the relevant policy text verbatim** back to the user; and
degrade gracefully — politely and sincerely, like a real employee apologizing —
when a request conflicts with policy.

The M1 intent enum is frozen at eight values and belongs to the mock rig
(ADR-0015).

## Decision

1. The E02 agent's intent enum adds a ninth intent: `policy_question`. The M1
   frozen enum is untouched (rig only).
2. Policy content is loaded lazily by a deterministic corpus tool (markdown
   sections indexed by heading; keyword-scored retrieval; no vector store per
   ADR-014). The LLM never answers a policy question from model memory.
3. Every policy answer must include at least one **verbatim quote** (validated
   as an exact substring of the source markdown) with its source document
   named. A response failing that validation is degraded to the retrieved
   sections themselves.
4. Requests that conflict with policy get a graceful-degradation response:
   sincere apology, the verbatim governing clause, and any legitimate
   alternative the policy allows. The agent never promises an exception.
5. Policy compliance outranks sales goals: the proactive-salesman behavior may
   never contradict or soften a policy clause.

## Alternatives Considered

1. Routing policy questions through the scope-safe/unsupported path — rejected:
   unstructured, hard to evaluate, no quoting guarantee.
2. Embedding policy text into the system prompt permanently — rejected: wastes
   context, violates lazy ingestion, and invites drift when documents change.

## Consequences

Positive: policy answers are traceable to source text, quoting is mechanically
verifiable, and eval cases can assert exact clauses.

Tradeoffs: keyword retrieval needs curated section headings and synonyms; long
sections must be windowed to keep quotes precise.

## Follow-Up

- US-203 implements the corpus, retrieval, quoting validation, and degradation
  templates; US-206 wires the router branch.
