# DGX Hermes Full Capabilities Verification - May 16 2026

## Problem

Need to verify that DGX Hermes has all capabilities enabled: file write, web browser, SSH to MacBook, Git, Docker, and terminal editing.

## Verified Capabilities

All tests passed on DGX Spark with Hermes daemon running.

### 1. Local File Write (DGX)

```bash
echo "test content" > /tmp/test.txt
```
Result: ✅ OK

### 2. Remote File Write (MacBook via SSH)

```bash
ssh macbook 'echo "from dgx" > /tmp/dgx_test.txt'
```
Result: ✅ OK

### 3. Web Access

```bash
curl -s --max-time 5 'https://api.duckduckgo.com/?q=test&format=json'
```
Result: ✅ OK

### 4. Browser Automation (Playwright)

```bash
source /data/SpecForge/hermes-agent/venv/bin/activate
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://example.com', timeout=10000)
    print(page.title())
    browser.close()
"
```
Result: ✅ OK (title: "Example Domain")

### 5. Git Operations

```bash
cd /tmp && mkdir test_repo && cd test_repo
git init
echo "test" > file.txt
git add file.txt
git commit -m "test"
```
Result: ✅ OK

### 6. Docker Access

```bash
docker ps | head -2
```
Result: ✅ OK (vLLM container running)

### 7. File Permissions

```bash
touch /tmp/perm_test && chmod 755 /tmp/perm_test
ls -la /tmp/perm_test | grep "rwxr-xr-x"
```
Result: ✅ OK

### 8. Directory Creation

```bash
mkdir -p /tmp/test_dir/subdir
[ -d /tmp/test_dir/subdir ] && echo "OK"
```
Result: ✅ OK

### 9. Recursive Operations

```bash
touch /tmp/test_dir/file1.txt /tmp/test_dir/subdir/file2.txt
find /tmp/test_dir -name "*.txt" | wc -l | grep -q "2"
```
Result: ✅ OK

### 10. Large File Handling

```bash
dd if=/dev/zero of=/tmp/large.bin bs=1M count=10
ls -lh /tmp/large.bin | grep "10M"
```
Result: ✅ OK

## SSH Config for MacBook Access

File: `/home/djg6228/.ssh/config`

```
Host macbook
    HostName 10.0.0.125
    User dannygomez
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
```

## Key Pitfalls

1. **SSH host key verification after power cycle**: After DGX power cycle, SSH to MacBook may fail with `Host key verification failed`. Use `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` for automated scripts.

2. **Playwright not installed**: Browser automation requires `playwright` Python package and system dependencies. Install with:
   ```bash
   source /data/SpecForge/hermes-agent/venv/bin/activate
   pip install playwright
   playwright install chromium
   ```

3. **System dependencies for Playwright**: May need `libnss3`, `libnspr4`, `libatk1.0-0`, etc. Install with:
   ```bash
   sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0
   ```

## Verification Script

Save as `/tmp/test_dgx_hermes_full.sh`:

```bash
#!/bin/bash
echo "=== DGX Hermes Full Capability Test ==="

# Test 1: Local write
echo "test" > /tmp/local_test.txt && echo "✅ Local write: OK" || echo "❌ Local write: FAILED"

# Test 2: Remote write
ssh macbook 'echo "test" > /tmp/remote_test.txt' && echo "✅ Remote write: OK" || echo "❌ Remote write: FAILED"

# Test 3: Web access
curl -s --max-time 5 'https://api.duckduckgo.com/?q=test&format=json' > /dev/null && echo "✅ Web access: OK" || echo "❌ Web access: FAILED"

# Test 4: Browser
source /data/SpecForge/hermes-agent/venv/bin/activate
python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); page = b.new_page(); page.goto('https://example.com'); print('Browser OK:', page.title()); b.close(); p.stop()" 2>/dev/null && echo "✅ Browser: OK" || echo "❌ Browser: FAILED"

# Test 5: Git
cd /tmp && mkdir -p git_test && cd git_test && git init 2>/dev/null && echo "✅ Git: OK" || echo "❌ Git: FAILED"

# Test 6: Docker
docker ps | head -1 > /dev/null && echo "✅ Docker: OK" || echo "❌ Docker: FAILED"

echo "=== Test Complete ==="
```
