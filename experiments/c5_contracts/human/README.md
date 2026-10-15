# Human review of the C5 obligations

`c5-review-sheet.html` is a single self-contained page for a reviewer: a short
introduction, one worked example, and one card per contract obligation of
`deliver-feature` (before and after the contract fixes, shuffled, without telling
which). It takes about 15 minutes, works offline, keeps the answers in the browser
while the reviewer works, and downloads them as `c5-answers-<initials>.json`.

1. Send `c5-review-sheet.html` to the reviewer (as an attachment; no installation).
2. Put the file they return in `answers/`.
3. Run `python experiments/c5_contracts/analyse.py`.

Regenerate the sheet with `python experiments/c5_contracts/make_sheet.py` if the items
change (`python experiments/c5_contracts/items.py`).
