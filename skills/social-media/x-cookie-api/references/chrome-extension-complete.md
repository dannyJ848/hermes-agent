# Complete X Cookie Extractor Extension (Production-Ready)

Validated 2026-05-16. Successfully extracted real auth_token, ct0, twid from X. Scanner authenticated and fetched 141 tweets.

## Files

Create a folder (e.g., `extract_x_cookies_extension/`) with these 4 files:

### manifest.json

```json
{
  "manifest_version": 3,
  "name": "X Cookie Extractor",
  "version": "1.0",
  "description": "Extract X/Twitter cookies for API access",
  "permissions": ["cookies", "activeTab"],
  "host_permissions": ["https://x.com/*", "https://twitter.com/*"],
  "action": { "default_popup": "popup.html" }
}
```

### popup.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { width: 400px; padding: 20px; font-family: system-ui; background: #0a0a0a; color: #e0e0e0; }
    h2 { margin-top: 0; color: #1d9bf0; }
    button { background: #1d9bf0; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; }
    button:hover { background: #1a8cd8; }
    #output { margin-top: 15px; background: #16181c; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 11px; word-break: break-all; }
    .found { color: #00ba7c; }
    .missing { color: #f4212e; }
    .label { color: #71767b; font-size: 10px; margin-top: 8px; }
  </style>
</head>
<body>
  <h2>X Cookie Extractor</h2>
  <button id="extract">Extract Cookies</button>
  <div id="output"></div>
  <script src="popup.js"></script>
</body>
</html>
```

### popup.js

```javascript
document.getElementById('extract').addEventListener('click', async () => {
  const domains = ['x.com', 'twitter.com', '.x.com', '.twitter.com'];
  const allCookies = [];
  for (const domain of domains) {
    const cookies = await chrome.cookies.getAll({ domain });
    allCookies.push(...cookies);
  }

  const authToken = allCookies.find(c => c.name === 'auth_token');
  const ct0 = allCookies.find(c => c.name === 'ct0');
  const twid = allCookies.find(c => c.name === 'twid');

  const result = {
    auth_token: authToken?.value || 'NOT FOUND',
    ct0: ct0?.value || 'NOT FOUND',
    twid: twid?.value || 'NOT FOUND'
  };

  const output = document.getElementById('output');
  output.innerHTML = `
    <div class="label">auth_token: <span class="${authToken ? 'found' : 'missing'}">${authToken ? 'FOUND' : 'NOT FOUND'}</span></div>
    <div class="label">ct0: <span class="${ct0 ? 'found' : 'missing'}">${ct0 ? 'FOUND' : 'NOT FOUND'}</span></div>
    <div class="label">twid: <span class="${twid ? 'found' : 'missing'}">${twid ? 'FOUND' : 'NOT FOUND'}</span></div>
    <pre style="margin-top:10px;white-space:pre-wrap;cursor:pointer;" onclick="navigator.clipboard.writeText(this.textContent);this.style.background='#1d9bf0';setTimeout(()=>this.style.background='',200)">${JSON.stringify(result, null, 2)}</pre>
    <div class="label" style="margin-top:8px;color:#71767b;">Click JSON to copy</div>
  `;
});
```

### README.md (optional)

```markdown
# X Cookie Extractor

1. Open Chrome → chrome://extensions/
2. Enable Developer mode
3. Click Load unpacked → select this folder
4. Log into x.com → click extension icon → Extract Cookies
5. Click JSON to copy → paste into your persona cookie file
```

## Installation Steps

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle top right)
3. Click **Load unpacked**
4. Select the folder containing the 4 files above
5. Pin to toolbar (click 🧩 puzzle piece → pin 📌)

## Usage

1. Log into x.com with the account you want to extract
2. Click the extension icon in toolbar
3. Click **Extract Cookies**
4. Click the JSON output to copy to clipboard
5. Paste into `personas/{persona}_cookies.json`

## Validation

After extraction, verify cookies work:

```bash
cd ~/propaganda-demystifier
python3 scanner.py
```

You should see:
```
[2026-05-16T00:10:48] Scanning persona: Left Lens
[2026-05-16T00:10:48] Fetching tweets from @AOC...
[2026-05-16T00:10:48] Resolved @AOC -> 138203134
[2026-05-16T00:10:51] Fetching tweets from @BernieSanders...
[2026-05-16T00:10:51] Resolved @BernieSanders -> 216776631
[2026-05-16T00:11:16] Collected 141 tweets for left_lens
```

If you see `Failed to resolve @AOC: 401`, the cookies are invalid or expired.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "Manifest file missing" | Wrong folder selected | Select folder containing manifest.json |
| "NOT FOUND" for cookies | Not logged into x.com | Log in and refresh |
| 401 errors in scanner | Cookies expired | Re-extract from browser |
| Extension won't load | Check chrome://extensions/ | Click "Errors" on extension card |

## Security

- Cookie files grant full X account access — keep them secure
- Never commit to git
- Use separate X accounts (not main personal account)
- auth_token expires — re-extract when API returns 401
