# Scheduled video runs — runbook

Scheduled sessions follow this file. Each run makes **one** TikTok video and leaves it in Buffer as a **draft** for a human to approve. Never publish or queue it.

## 0. Setup (fresh machine)

1. Attach the repo with push access (`add_repo` owner `963X-Protocol`, repo `99x-media`, access `push`), clone it, `cd` into it.
2. `bash pipeline/setup.sh` (installs Python packages, downloads the voice model from GitHub releases, ~340 MB).

## 1. Research (today's facts only)

Use WebSearch/WebFetch. Every number in the video must come from a page fetched in this run; write its source into `src`. Prefer: CoinDesk, The Block, Reuters, Bloomberg, Yahoo Finance, CoinGlass (via articles), SoSoValue (ETF flows), KuCoin/Binance daily reports, official company / fund / regulator announcements, and `https://99x.exchange/en/news` (99X's own research — good for perp positioning, funding, open interest and institutional news). If two sources disagree, use the more conservative number or leave it out. If you cannot confirm today's data, stop and report instead of guessing.

Series:

- **Daily Brief** (Mon–Fri): prices (BTC, ETH, SOL), the 24h move, liquidations, ETF flows, the main driver, today/this-week calendar, one key level. Badge `BREAKING`. `id` = `brief-YYYY-MM-DD`.
- **Weekly Recap** (Sun): the week in 5–6 beats: weekly move, biggest story, flows, one institutional story, next week's calendar. Badge `THIS WEEK`, `series` `WEEKLY RECAP`, `tapeColor` `teal`, `follow` `FOLLOW FOR THE WEEKLY RECAP`, `followSay` "Follow for the weekly recap." `id` = `recap-YYYY-MM-DD`.
- **Insight** (Tue, Thu): business news about crypto companies, funds, market makers, exchanges, investing (raises, acquisitions, custody launches, treasury buys, MM/fund moves, earnings). Pick the 2–3 most significant items of the last 48h and tell them as a story: what happened → why it matters for traders. Use `headline` beats. Badge `DEAL FLOW` or `INSIGHT`, `series` `INSIGHT`, `tapeColor` `purple`, `follow` `FOLLOW FOR DAILY INSIGHT`, `followSay` "Follow for more insight." `id` = `insight-YYYY-MM-DD`.

## 2. Editorial rules

- English voice and captions. Hook first: beat 1 must make someone stop scrolling.
- Report, don't predict: no price targets, no "will pump", no buy/sell calls. Levels are "levels to watch".
- Never say or imply 99X (the token) has a price or will gain value. Do not use "airdrop", "1000x", "guaranteed", "risk-free", "0 market impact".
- Only claim 99X features that are in the automatic pitch (AI agents, your rules/limits, agent keys can't withdraw).
- Public companies, funds and their executives are fine; no private individuals.
- Quotes must be real, short and attributed.
- Total voice length 35–50 s.

## 3. Build

1. Write `pipeline/episodes/<id>.json` (see `EPISODE_SPEC.md`, copy the shape of `example-brief.json`).
2. `python3 pipeline/make.py pipeline/episodes/<id>.json --stills` then **look at** `pipeline/work/<id>/sheet.png`. Fix overflow (text cut off, overlapping), wrong numbers or empty beats, and re-run until clean.
3. `python3 pipeline/make.py pipeline/episodes/<id>.json` → `videos/<id>.mp4` (must be < 50 MB).

## 4. Publish to the repo

1. Add to `queue.json` → `posts`: `{"id", "file": "videos/<id>.mp4", "title", "caption", "status": "draft", "bufferUrl": ""}`.
2. Commit the episode JSON, the video and `queue.json`; `git pull --rebase` then push to `main`.
3. Check `https://raw.githubusercontent.com/963X-Protocol/99x-media/main/videos/<id>.mp4` returns HTTP 200 (retry for up to a minute).

## 5. Buffer draft

Organization `My organization` (`6ad2d8c76f00424ac7119ce8`), TikTok channel `agentictrading` (`6ad2da72778b240e2f3339e7`).

`create_post` with `saveToDraft: true`, `schedulingType: "automatic"`, `text` = caption, one video asset (raw URL above, `metadata.title` = file name, `thumbnailOffset` 1500), `metadata.tiktok` = `{title, isAiGenerated: true}`.

Then set the item's `bufferPostId` in `queue.json`, commit and push.

## 6. Report

Send the human a short message (Vietnamese): video title, 1-line summary of each beat, sources, and that the draft is waiting in Buffer → TikTok → Drafts for approval. Attach the mp4. If anything failed, say exactly which step.
