# Active Workstream Trackers

These files coordinate parallel product work and prevent overlapping branches,
worktrees, stories, and file ownership. They are assignment records, not product
contracts and not substitutes for Harness proof.

## Identity Map

| Tracker alias | Member identity | Tracker | Assignment state |
| --- | --- | --- | --- |
| THANH | dinh-nhat-thanh | [`THANH-NOW.md`](THANH-NOW.md) | Assigned by a human |
| USER1 | luu-thien-viet-cuong | [`USER1-NOW.md`](USER1-NOW.md) | Assigned by Cường (Lưu Thiện Việt Cường) on 2026-07-18; direction recorded in the member session log |
| USER2 | luu-thien-viet-cuong | [`USER2-NOW.md`](USER2-NOW.md) | Assigned by Cường (Lưu Thiện Việt Cường) on 2026-07-18; direction recorded in the member session log |
| DUY | luu-tien-duy | [`DUY-NOW.md`](DUY-NOW.md) | Assigned by Duy (Lưu Tiến Duy) on 2026-07-19; direction recorded in the member session log |

Aliases are not identities. An agent must never infer an alias owner from Git
configuration, operating-system usernames, earlier chat, or task content. A
human must update this table explicitly. Both `USER1` and `USER2` were mapped to
`luu-thien-viet-cuong` by Cường's explicit in-session direction on 2026-07-18: a
single member may own multiple aliases when solo-driving parallel lanes.
Conflict avoidance is enforced by each tracker's file boundary and serialized
merges, not by requiring one member per alias.


## Mandatory Use

Before product implementation:

1. Resolve the current team identity through `ai-logs/README.md`.
2. Confirm that this index maps that identity to exactly one tracker.
3. Read the mapped tracker and compare its story, dependencies, branch,
   worktree, and file boundary with the Harness matrix.
4. Stop before implementation if any value is missing, duplicated, blocked, or
   inconsistent.

Repository-governance work may update this index through its own registered
story. It must not claim or execute an unassigned product workstream.

## Update Rule

Only a human may assign or reassign a tracker alias. The mapped owner updates
only their tracker; the integration controller coordinates cross-tracker
changes. Completed tracker history remains in Git rather than being copied to
new ad hoc root files.
