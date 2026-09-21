# Study population flow

This diagram reports selection only. It does not depict accepted results or an experimental success rate.

```mermaid
flowchart LR
    H["Original historical archive: 100 papers"] --> R["Retained historical group: 97"]
    H --> E["Recorded retrospective exclusions: 3"]
    R --> A["Read-only evidence extraction: 97 papers"]
    A --> Q["Source-semantic review: pending"]
    N["Fixed prospective additions: 3"] --> P["Production case implementations prepared"]
    P --> U["Verified isolation unavailable; acceptance pending"]
    R --> D["Planned detailed-analysis population: 100"]
    N --> D
```

The original 100 records are preserved. The three new identities make the full selection history 103. The detailed analysis will report historical and new groups separately; source availability and selection differ between the groups. Counts originate from `cohort.json` and `data/summary.json`.
