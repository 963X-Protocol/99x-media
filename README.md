# 99x-media

Public video drop for 99X TikTok posts. Claude downloads a file from this repo, then uploads it in Buffer to the TikTok channel.

Anyone can download these files. Do not put private keys, Buffer tokens, or unreleased material here.

## Add a video

1. Put an `.mp4` in `videos/`. Keep it under 50 MB so GitHub serves the real file (GitHub rejects files over 100 MB).
2. Add one object to `queue.json` with `"status": "ready"`.
3. Commit and push to `main`.

Vertical 9:16 works best for TikTok. Caption lives in `queue.json`, not inside the video.

## Agent instructions

Read `queue.json`. For each post with `"status": "ready"`:

1. Download `https://raw.githubusercontent.com/963X-Protocol/99x-media/main/<file>`.
2. Open Buffer, choose the connected TikTok channel, and upload that file.
3. Use `caption` as the post text. Do not invent a different caption.
4. Send it through Buffer. Do not post from a personal TikTok login.
5. After Buffer accepts the post, change that item's `status` to `sent` and set `bufferUrl` if Buffer shows a link.

Skip `draft` and `sent`. If a download is not a video file, stop and say so.

## Queue fields

| Field | Meaning |
| --- | --- |
| `id` | Stable name for this post |
| `file` | Path inside this repo, for example `videos/launch.mp4` |
| `caption` | Exact TikTok text |
| `status` | `draft`, `ready`, or `sent` |
| `bufferUrl` | Filled after Buffer accepts the post |
