# Single Account, Multi-Persona Pattern

When you only have one X account but want multiple ideological perspectives, use shared cookies with different follows lists. Validated 2026-05-16.

## When to Use This

- You have one X account (not 3 separate ones)
- You want to scan different ideological feeds for comparison
- You don't need X's algorithm to show different home feeds
- You just need to query different accounts and search terms per persona

## How It Works

All personas share the same `auth_token`, `ct0`, `twid` from one account. The scanner loads cookies from a single file (`left_lens_cookies.json`) for all personas. Each persona still queries different follows lists and search queries defined in `config/personas.yaml`.

## Implementation

```python
def load_persona_cookies(persona_name: str) -> Dict[str, str]:
    """Load cookies for a specific persona.
    
    All personas share the same account cookies (single account, different follows).
    Falls back to left_lens cookies if persona-specific file doesn't exist.
    """
    cookie_file = COOKIE_DIR / f"{persona_name}_cookies.json"
    
    # Fall back to shared cookies (left_lens = primary account)
    if not cookie_file.exists() or cookie_file.stat().st_size < 200:
        cookie_file = COOKIE_DIR / "left_lens_cookies.json"
        log(f"Using shared account cookies for {persona_name}")
    
    if not cookie_file.exists():
        raise FileNotFoundError(
            f"No cookies found. Create {COOKIE_DIR}/left_lens_cookies.json with auth_token, ct0, and twid."
        )
    
    with open(cookie_file) as f:
        return json.load(f)
```

## Results (Validated)

With one account and 3 personas:
- Left Lens: 141 tweets (AOC, Bernie, Maddow, TheIntercept, MotherJones)
- Center Lens: 138 tweets (Reuters, AP, BBCWorld, NPR, PBS)
- Right Lens: 113 tweets (GOP, BreitbartNews, DailyCaller, TuckerCarlson, dbongino)
- Total: 392 tweets, 384 unique after dedup

All user lookups succeeded (no 401s). Scanner resolved:
- @AOC -> 138203134
- @Reuters -> 1652541
- @GOP -> 2046223166461136896

## Limitations

- X's algorithm still shows YOUR bubble's content in home feeds
- Search queries and direct account lookups work fine
- For true algorithmic diversity, you need separate accounts
- Some accounts may block or limit your single account

## When to Upgrade to Multiple Accounts

Switch to separate cookies per persona when:
- You need X's recommendation algorithm to surface different content
- You're hitting rate limits on one account
- You want to avoid association between personas
- You need to follow accounts that would create a weird combined timeline

## File Structure

```
personas/
├── left_lens_cookies.json      # Primary account (real cookies)
├── center_lens_cookies.json    # Placeholder or copy of left_lens
└── right_lens_cookies.json     # Placeholder or copy of left_lens
```

The scanner auto-detects placeholder files (< 200 bytes) and falls back to `left_lens_cookies.json`.
