# Episode JSON

One file per video in `pipeline/episodes/<id>.json`. `make.py` turns it into `videos/<id>.mp4`.
Example: `episodes/example-brief.json`.

## Top level

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | File-safe id, e.g. `brief-2026-10-27`, `recap-2026-11-01`, `insight-2026-10-27` |
| `series` | yes | Header tag: `DAILY BRIEF`, `WEEKLY RECAP`, `INSIGHT` |
| `badge` | yes | Red pill text: `BREAKING`, `THIS WEEK`, `DEAL FLOW`, … (short, caps) |
| `badgeColor` | no | `red` (default), `teal`, `purple`, `amber` |
| `date` | yes | `OCT 27, 2026` — the publish date, always shown |
| `src` | yes | `data as of <time> · sources: <names> · not financial advice` |
| `tape` | yes | 4–7 short ticker strings, e.g. `"BTC ~$80,150 ▼0.9%"` |
| `tapeColor` | no | `red` (default, market-down days), `teal` (up/neutral days), `purple` (insight) |
| `follow` | no | End-card line. Default `FOLLOW FOR THE DAILY BRIEF` |
| `followSay` / `followCap` | no | Last spoken line. Default "Follow for the daily brief." |
| `speed` | no | Voice speed, default 1.06 |
| `cta` | no | Two `[say, cap]` pairs replacing the default closing pitch lines (the visuals stay the same) |
| `beats` | yes | 5–7 beats (each beat = one voice line + one visual) |
| `title` | yes | TikTok title (≤ 90 chars) |
| `caption` | yes | TikTok caption, lowercase style, ending with 4–6 hashtags |

The closing 99X pitch (agent order passes, withdrawal denied) and the end card are added automatically. Do not add them as beats.

## Beat

Every beat has `type`, `say` (spoken; write numbers as words: "eighty-one thousand", "ninety-nine X", "G D P") and `cap` (caption; digits and symbols: "$81K", "99X", "GDP"). Keep each `say` under ~20 words. Optional `k` is the small grey label above the visual.

| `type` | Fields | Use for |
| --- | --- | --- |
| `hero` | `to` (number), `from`, `prefix`, `suffix`, `dec`, `color`, `sub` — or `text` instead of `to` for a fixed string | One big number that counts up/down. Always beat 1. |
| `cards` | `items: [{k, v, n?, color?}]` (1–3) | 2–3 related stats |
| `bars` | `v`, `items: [{label, pct, color}]`, `note` | Splits like long/short liquidations |
| `headline` | `text`, `sub?`, `items?: [{k, v, n?, color?}]` (0–2) | A news item (company, fund, MM, deal) |
| `list` | `items: [{k, v}]` (2–3) | Calendar / upcoming events (purple cards) |
| `levels` | `rows: [{k, v, color}]` (2–3) | Support / resistance levels |
| `quote` | `text`, `who` | A short attributed quote (≤ 12 words, must be real and sourced) |

Colors: `red`, `green`, `teal`, `amber`, `purple`, `white`, `grey`, or a hex value.

Layout limits (the frame is narrow): `hero` values ≤ 9 characters, `cards`/`headline` item values ≤ 16 characters, `headline.text` ≤ 60 characters.
