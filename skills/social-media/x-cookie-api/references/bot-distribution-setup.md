# Bot Distribution Setup — Fediverse + Newsletter

Reference for wiring Mastodon, Bluesky, and email newsletter distribution into the propaganda demystification pipeline. Built 2026-05-16.

## Architecture

```
Pipeline: scanner.py → digest_generator.py → site_generator.py → bot/run_bots.py
                                                              ↓
                                            ┌─────────────────┼─────────────────┐
                                            ↓                 ↓                 ↓
                                      Mastodon          Bluesky          Newsletter
                                      (toot)            (skeet)          (HTML email)
```

## Files

```
bot/
├── mastodon_poster.py       # Mastodon/Fediverse poster
├── bluesky_poster.py        # Bluesky (AT Protocol) poster
├── newsletter_sender.py     # SMTP email sender
├── run_bots.py              # Orchestrates all three
├── subscribers.txt          # Email list (one per line)
└── SETUP.md                 # Quick setup guide
```

## Mastodon Setup

1. Create account on any instance (mastodon.social, fosstodon.org, etc.)
2. Settings → Development → New Application
3. Name: "The Lens Bot", Scopes: `write:statuses read:accounts`
4. Copy Access Token
5. Set env var: `export FEDIVERSE_TOKEN=your_token`
6. Optional: `export FEDIVERSE_INSTANCE=mastodon.social`

**Toot format** (500 char limit):
```
📰 The Lens — Daily Digest (2026-05-16)

Analyzed 472 tweets across 4 perspectives

🔥 Top Stories:
1. politics (810,650 engagement)
2. other (487,968 engagement)
3. tech (352,805 engagement)

🔗 Full analysis: https://thelens.news

#TheLens #News #MediaLiteracy
```

## Bluesky Setup

1. Create account at bsky.app
2. Settings → App Passwords → Add App Password
3. Name: "The Lens Bot"
4. Copy app password (NOT main password)
5. Set env var: `export BLUESKY_PASSWORD=your_app_password`
6. Optional: `export BLUESKY_HANDLE=thelens.bsky.social`

**Skeet format** (300 char limit):
```
📰 The Lens — 2026-05-16

472 tweets analyzed

1. politics
2. other
🔗 Full digest in bio
```

## Newsletter Setup

1. Set SMTP credentials:
   ```bash
   export SMTP_HOST=smtp.gmail.com
   export SMTP_PORT=587
   export SMTP_USER=your.email@gmail.com
   export SMTP_PASS=your_app_password
   export FROM_EMAIL=your.email@gmail.com
   export FROM_NAME="The Curator"
   ```

2. Add subscribers to `bot/subscribers.txt`:
   ```
   # Comments and blank lines ignored
   friend1@example.com
   friend2@example.com
   ```

3. HTML email includes:
   - Dark-themed responsive design
   - Color-coded personas (red=left, yellow=center, green=right, blue=personal)
   - Top 5 stories with engagement scores
   - Framing analysis per persona
   - Unsubscribe link

## Pipeline Integration

The `run_pipeline.py` orchestrator now includes bot distribution as the final step:

```python
steps = [
    ("scanner.py", "Multi-persona feed scanning"),
    ("digest_generator.py", "Daily digest generation"),
    ("site_generator.py", "Static site generation"),
    ("bot/run_bots.py", "Bot distribution (Mastodon/Bluesky/Newsletter)"),
]
```

Bots run automatically after site generation when cron fires.

## Dry Run Testing

Without credentials set, bots print what they WOULD post:

```bash
cd ~/propaganda-demystifier
python3 bot/mastodon_poster.py   # Shows toot content, skips post
python3 bot/bluesky_poster.py    # Shows skeet content, skips post
python3 bot/newsletter_sender.py  # Shows subscriber count, skips send
python3 bot/run_bots.py          # Runs all three
```

## Environment Variables Summary

| Variable | Platform | Required |
|----------|----------|----------|
| `FEDIVERSE_TOKEN` | Mastodon | Yes |
| `FEDIVERSE_INSTANCE` | Mastodon | No (default: mastodon.social) |
| `BLUESKY_PASSWORD` | Bluesky | Yes |
| `BLUESKY_HANDLE` | Bluesky | No (default: thelens.bsky.social) |
| `SMTP_HOST` | Email | Yes |
| `SMTP_PORT` | Email | No (default: 587) |
| `SMTP_USER` | Email | Yes |
| `SMTP_PASS` | Email | Yes |
| `FROM_EMAIL` | Email | Yes |
| `FROM_NAME` | Email | No (default: "The Curator") |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Mastodon 401 | Invalid token | Regenerate in Settings → Development |
| Bluesky auth fail | Using main password | Use App Password, not main password |
| SMTP connection refused | Wrong host/port | Check provider settings (Gmail=587+TLS) |
| Newsletter shows 0 subscribers | Empty subscribers.txt | Add emails, one per line |
| Bots not running | Not in pipeline | Check `run_pipeline.py` includes bot step |

## Security Notes

- Store credentials in env vars, never in code
- Cookie files grant full X access — keep secure
- Use separate X account (not personal) for scanning
- App passwords (Bluesky) are revocable without changing main password
- SMTP app passwords (Gmail) are revocable independently
