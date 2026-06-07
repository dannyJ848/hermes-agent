#!/bin/bash
# Install stealth browser stack on DGX (ARM64 Ubuntu 24.04)
# Run this on DGX as djg6228

set -e

echo "=== DGX Stealth Browser Install ==="
echo "Architecture: $(uname -m)"
echo "OS: $(lsb_release -d 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME)"

# 1. Install system deps for chromium headless
echo "[1/5] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libwayland-client0 \
    xvfb \
    fonts-liberation \
    2>/dev/null || echo "Some packages may already be installed"

# 2. Install Python playwright + stealth
echo "[2/5] Installing Python playwright..."
pip3 install --user playwright playwright-stealth 2>/dev/null || pip3 install playwright playwright-stealth

# 3. Install chromium browser binaries for ARM64
echo "[3/5] Installing Chromium browsers..."
python3 -m playwright install chromium

# 4. Verify install
echo "[4/5] Verifying installation..."
python3 -c "
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
print('playwright:', sync_playwright().__enter__().chromium.version())
print('stealth: OK')
" 2>/dev/null || echo "Verification failed — may need to run 'playwright install' manually"

# 5. Create reddit browsing script
echo "[5/5] Creating reddit browser script..."
cat > /home/djg6228/reddit_browser.py << 'PYEOF'
#!/usr/bin/env python3
"""Stealth reddit browser for DGX — bypasses basic bot detection."""
import sys
import json
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def browse_reddit(subreddit="AskReddit", sort="hot", limit=5):
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    
    # Check for proxy env var: REDDIT_PROXY=socks5://host:port
    proxy = os.environ.get("REDDIT_PROXY")
    proxy_config = {"server": proxy} if proxy else None
    
    with sync_playwright() as p:
        # Launch with stealth args
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        
        browser = p.chromium.launch(
            headless=True,
            args=launch_args,
            proxy=proxy_config,
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = context.new_page()
        stealth_sync(page)
        
        # Navigate with timeout
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            content = page.content()
            
            # Check if blocked
            if "blocked by network security" in content or "You've been blocked" in content:
                print("ERROR: Reddit blocked this request (IP-based)")
                browser.close()
                return None
                
            # Try to extract JSON if it's the API endpoint
            try:
                data = json.loads(page.inner_text("body"))
                posts = []
                for child in data.get("data", {}).get("children", [])[:limit]:
                    post = child.get("data", {})
                    posts.append({
                        "title": post.get("title"),
                        "author": post.get("author"),
                        "score": post.get("score"),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "subreddit": post.get("subreddit"),
                    })
                browser.close()
                return posts
            except json.JSONDecodeError:
                # Not JSON — reddit served HTML block page
                print("ERROR: Reddit returned HTML instead of JSON")
                browser.close()
                return None
                
        except Exception as e:
            print(f"ERROR: {e}")
            browser.close()
            return None

def browse_reddit_page(subreddit="AskReddit", sort="hot"):
    """Browse the HTML page (not JSON API) — more likely to work with proxy."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}"
    proxy = os.environ.get("REDDIT_PROXY")
    proxy_config = {"server": proxy} if proxy else None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
            proxy=proxy_config,
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        stealth_sync(page)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)  # Let JS render
            
            # Extract post titles via JS
            posts = page.evaluate("""
                () => {
                    const posts = [];
                    document.querySelectorAll('[data-testid="post-container"]').forEach(el => {
                        const title = el.querySelector('h3, [data-testid="post-title"]');
                        if (title) posts.push(title.innerText);
                    });
                    return posts.slice(0, 10);
                }
            """)
            browser.close()
            return posts
        except Exception as e:
            print(f"ERROR: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    sub = sys.argv[1] if len(sys.argv) > 1 else "AskReddit"
    mode = sys.argv[2] if len(sys.argv) > 2 else "json"
    
    if mode == "json":
        posts = browse_reddit(subreddit=sub)
    else:
        posts = browse_reddit_page(subreddit=sub)
    
    if posts:
        print(json.dumps(posts, indent=2))
    else:
        sys.exit(1)
PYEOF

chmod +x /home/djg6228/reddit_browser.py

echo ""
echo "=== Install Complete ==="
echo "Run: python3 /home/djg6228/reddit_browser.py [subreddit]"
echo ""
echo "NOTE: If reddit still blocks (IP-based), you need a proxy."
echo "Add to the script: proxy={\"server\": \"socks5://host:port\"}"
