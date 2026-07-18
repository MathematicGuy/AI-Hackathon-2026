-- Enable pgvector. Used ONLY for the knowledge base (RAG over policy/FAQ),
-- never for product ranking (ADR-014 / product architecture principle 16).
CREATE EXTENSION IF NOT EXISTS vector;
