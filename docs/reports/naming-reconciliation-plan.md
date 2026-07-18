# Dry-Run Naming Reconciliation Plan: AI Product Advisor

This dry-run plan outlines the proposed updates across the project's documentation (`.md`) files to transition the high-level project framing from **Air-Conditioner Advisor MVP** to the unified **AI Product Advisor** (or **AI Product Comparison Advisor**). 

In accordance with frozen contracts (ADR-001) and to prevent context drift, category-specific technical references (e.g., Python class names like `AirConditionerNeed`, database columns like `btu`/`cspf`, and catalog file names) will remain unchanged. This plan focuses solely on **General Naming** in documentation files.

---

## 1. Naming Mapping Rules

To ensure consistency across future features and agents, we establish the following renaming conventions:

| Old Term / Context | New Unified Term | Action Type | Notes |
|---|---|---|---|
| `Air-Conditioner Advisor` / `Air Conditioner Advisor` (Project title) | `AI Product Advisor` | **Rename** | Unified high-level project name. |
| `Deterministic Air-Conditioner Decision Engine` | `Product Advisor Decision Engine (Air-Conditioner slice)` | **Rename** | Retains general engine name while qualifying the M1 scope. |
| `air-conditioner-advisor-m1-contract.md` (filename) | `air-conditioner-advisor-m1-contract.md` | **Keep (No Change)** | Retains literal filepath to prevent breaking existing links and tools. |
| `AirConditionerNeed` (Python schema) | `AirConditionerNeed` | **Keep (No Change)** | Retains database/code level schemas to avoid contract drift. |
| `máy lạnh` / `air conditioner` (General category name) | `máy lạnh` / `air conditioner` | **Keep (No Change)** | Stays as the specific M1 category slice implementation. |

---

## 2. Proposed Changes by File

### 2.1 Project Root Files

#### `README.md`
Proposed updates to clarify general product description and point to M1 slice:
```diff
- # AI Product Comparison Advisor
+ # AI Product Advisor
  
- `air-conditioner`/`aircon` are M1's category-specific artifacts, not the whole
+ `air-conditioner`/`aircon` are M1's category-specific slice artifacts, not the whole
```

#### `PROJECT_MANAGEMENT.md`
Reconciles task names and milestone descriptions:
```diff
- > **Epic:** Release Milestone 1 — Máy lạnh decision-support advisor
+ > **Epic:** Release Milestone 1 — Product Advisor Decision Engine (Air-Conditioner slice)
  
- - **M1.2 — Deterministic Air-Conditioner Decision Engine**
+ - **M1.2 — Deterministic Product Advisor Decision Engine (Air-Conditioner slice)**
```

---

### 2.2 Documentation Index Files (`docs/`)

#### `docs/README.md`
Clarifies document index mapping to the unified name:
```diff
- | `docs/product/air-conditioner-advisor-m1-contract.md` | Accepted Milestone 1 product behavior |
+ | `docs/product/air-conditioner-advisor-m1-contract.md` | Product Advisor Contract — Milestone 1 (Air-Conditioner) |
```

#### `docs/product/README.md`
Reinforces general product description:
```diff
  The product is the general **AI Product Comparison Advisor** for Điện Máy XANH.
- The `air-conditioner-advisor-m1-*` documents below are the **Milestone 1 artifacts**
+ The `air-conditioner-advisor-m1-*` documents below are the **Milestone 1 (Air-Conditioner slice) artifacts**
```

---

### 2.3 Product Authority Files (`docs/product/`)

#### `docs/product/air-conditioner-advisor-m1-contract.md`
Updates file title header while leaving technical schemas and path definitions intact:
```diff
- # Air Conditioner Advisor M1 Contract
+ # Product Advisor Contract — Milestone 1 (Air-Conditioner)
```

#### `docs/product/architecture/air-conditioner-advisor-m1.md`
Updates file title header to reflect project-level naming:
```diff
- # Air Conditioner Advisor M1 Product Architecture
+ # Product Advisor M1 Product Architecture (Air-Conditioner slice)
```

#### `docs/product/requirements/air-conditioner-advisor-m1-prd.md`
Updates file title header and scope notes:
```diff
- # Air Conditioner Advisor — Milestone 1 Product Requirements (PRD)
+ # Product Advisor — Milestone 1 Product Requirements (PRD) (Air-Conditioner slice)
```

---

### 2.4 Story Map & Backlog Files (`docs/stories/`)

#### `docs/stories/backlog.md`
Updates the Epic description:
```diff
- | E01 — Air Conditioner Advisor M1 | Vietnamese máy lạnh decision-support MVP
+ | E01 — AI Product Advisor M1 (Air-Conditioner) | Vietnamese máy lạnh decision-support MVP
```

#### `docs/stories/epics/E01-air-conditioner-advisor-m1/US-106-catalog-adapter-pagination/overview.md`
Updates user-story overview scope descriptions:
```diff
- Provide a read-only catalog adapter and deterministic air-conditioner search
+ Provide a read-only catalog adapter and deterministic product search (air-conditioner slice)
```

---

## 3. Context Drift Risk Mitigation

To ensure that other agents do not misunderstand the naming hierarchy:
1. **Durable Story Records:** When registering future stories via `harness-cli`, title them under `Product Advisor` with the category suffix in parentheses, e.g., `Product Advisor (Air-Conditioner)`.
2. **Session Logs:** All future AI sessions should reference the unified project name `AI Product Advisor` in their metadata `task_summary` fields.
3. **Glossary:** Add the unified project naming distinction to `docs/GLOSSARY.md` under a new `AI Product Advisor` definition:
   > **AI Product Advisor:** The unified, multi-category decision-support advisor framework for Điện Máy XANH. Milestone 1 implements the `Air-Conditioner (Máy lạnh)` category slice.
