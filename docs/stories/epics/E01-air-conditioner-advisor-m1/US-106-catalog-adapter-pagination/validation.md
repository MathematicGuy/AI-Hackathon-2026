# Validation

## Required Cases

- Default 3, explicit 1 and 10, rejected 0 and 11.
- Stable order and next cursor.
- Cursor plus exclusions produces no skip or duplicate.
- Negative/malformed cursor rejected; out-of-range cursor is terminal empty page.
- Region filter deterministic.
- Mixed source snapshots rejected.

## Commands

```powershell
python -m pytest backend/tests/unit/tools/test_product_search.py -q
python -m pytest backend/tests/unit/tools/test_product_search.py backend/tests/contract -q
```
