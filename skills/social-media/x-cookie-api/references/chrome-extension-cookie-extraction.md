# Chrome Extension for X Cookie Extraction

## Problem

X's `auth_token` cookie is **httpOnly** — JavaScript cannot access it via `document.cookie`. The `ct0` and `twid` cookies are accessible, but `auth_token` requires either:
1. Chrome DevTools manual extraction (tedious, 3 accounts)
2. A Chrome extension with `cookies` permission (one-click)
3. Native messaging host (overkill)

## Solution: X Cookie Extractor Extension

A minimal Chrome extension that uses the `chrome.cookies` API to extract all three required cookies in one click.

### Installation

1. Open Chrome → `chrome://extensions/`
2. Toggle **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the extension folder
5. Pin to toolbar

### Manifest (manifest.json)

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

### Key Implementation (popup.js)

```javascript
document.getElementById('extract').addEventListener('click', async () => {
  // Get all cookies for x.com and twitter.com
  const domains = ['x.com', 'twitter.com', '.x.com', '.twitter.com'];
  const allCookies = [];
  
  for (const domain of domains) {
    const cookies = await chrome.cookies.getAll({ domain });
    allCookies.push(...cookies);
  }
  
  // Extract required cookies
  const authToken = allCookies.find(c => c.name === 'auth_token');
  const ct0 = allCookies.find(c => c.name === 'ct0');
  const twid = allCookies.find(c => c.name === 'twid');
  
  // Output JSON ready to paste into persona files
  const result = {
    auth_token: authToken?.value || '',
    ct0: ct0?.value || '',
    twid: twid?.value || ''
  };
  
  // Display and allow copy-to-clipboard
});
```

### Why This Works

The `chrome.cookies` API has access to **all cookies** including httpOnly ones — unlike `document.cookie` which is restricted to non-httpOnly cookies. This is the only programmatic way to extract `auth_token` without using DevTools.

### Kimi WebBridge Limitation

The Kimi WebBridge extension (`fldmhceldgbpfpkbgopacenieobmligc`) has `tabs`, `debugger`, `activeTab` permissions but **NOT** `cookies`. It cannot extract httpOnly cookies. The extension above is purpose-built for this task.

## Manual Fallback (No Extension)

If the user won't install an extension:

1. Log into X.com in Chrome
2. DevTools → **Application** tab → **Cookies** → `https://x.com`
3. Copy:
   - `auth_token` (long hex, ~40 chars)
   - `ct0` (shorter hex)
   - `twid` (starts with `u%3D`)
4. Paste into JSON:

```json
{
  "auth_token": "FULL_HEX_STRING_HERE",
  "ct0": "CSRF_TOKEN_HERE",
  "twid": "u%3DNUMERIC_USER_ID"
}
```

## Security Notes

- Cookie files grant full X account access — keep them secure
- Never commit to git
- Use separate X accounts (not main personal account)
- Consider throwaway accounts for personas
- auth_token expires — re-extract when API returns 401

## Multi-Persona Workflow

For the propaganda demystification engine with 3 personas:

1. Log into X with **left lens** account
2. Click extension → copy JSON → save to `personas/left_lens_cookies.json`
3. Log into X with **center lens** account (or use incognito)
4. Click extension → copy JSON → save to `personas/center_lens_cookies.json`
5. Log into X with **right lens** account
6. Click extension → copy JSON → save to `personas/right_lens_cookies.json`

Each persona needs its own authenticated session. The scanner rotates through them automatically.
