# Free historical index data audit

Research only. Default execution is offline; no trading logic, signal tuning,
production imports, databases, subscriptions or deployment operations.

Python 3.11+ standard library is sufficient for reproduction using frozen calendar:

```bash
python research/free_historical_index_data/audit.py --cache /tmp/alpha-index-cache --fetch
python -m unittest discover -s research/free_historical_index_data -v
```

`--fetch` downloads only pinned public GitHub files listed in source-manifest.json.
It does not download new quotes from market vendors. Omit it for offline replay.
Inputs are cached outside Git and checked against SHA256 and Git blob identities.
No raw provider packs or upstream source code are redistributed in this PR.
Open repository visibility does not establish a data redistribution licence:
read source-audit.md before downstream use, especially the unlicensed thuning source.

Regenerate numerical outputs in another directory with `--output /tmp/audit-replay`.
The nine narrative reports are human-written synthesis, not silently regenerated.
CSV tables ending .gz.b64 decode with base64 then gzip to ordinary UTF-8 CSV;
gzip uses mtime=0 for deterministic output. Full membership stays source-separated.
Issuer CIK and security ID are separate fields; blank security ID means unknown.
No ticker alias, merger, reorganisation or share class is silently joined.

Calendar generation used exchange_calendars 4.11.2, XNYS 2009–2026, restricted to
2010-01-01 through last completed 2026-11-03; the 4235 dates are frozen and hashed.
This is an exchange-session reference, not independently certified Nasdaq-specific
halt history. 2026 is YTD; future November/December sessions are not invented.
