Search JSON records by field

This folder contains a small Python CLI `search_by_tag.py` that helps you explore and search the JSON records in `matches_2025-12-03T15-36-21.json`.

Examples (PowerShell):

List discovered fields and sample values:

```powershell
python .\search_by_tag.py --file .\matches_2025-12-03T15-36-21.json --list-fields
```

List top values for a field (e.g. company):

```powershell
python .\search_by_tag.py -f .\matches_2025-12-03T15-36-21.json --list-values job.company
```

Search for records where a field contains a substring (case-insensitive):

```powershell
python .\search_by_tag.py -f .\matches_2025-12-03T15-36-21.json --search analysis.match_reasons "safety"
```

Show full record by index (index shown in search results):

```powershell
python .\search_by_tag.py -f .\matches_2025-12-03T15-36-21.json --show 0
```

Write matched records to a JSON file:

```powershell
python .\search_by_tag.py -f .\matches_2025-12-03T15-36-21.json --search job.title manager --json-out .\matches_manager.json
```

If you want a prettier HTML viewer or more advanced indexing (fast lookups, inverted index), tell me and I’ll add it.
