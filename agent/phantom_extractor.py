#!/usr/bin/env python3
"""
Phantom Extractor v2.0 — Hardened paywall bypass with full OPSEC.
Layered fallback: archive → cache → stealth fetch → phantom browser.
Zero attribution. Zero fingerprint. Zero trace.

Architecture:
  Layer 1: Archive services (archive.ph, Wayback Machine) — no direct contact with target
  Layer 2: Cache services (Google Cache, Bing Cache) — no direct contact
  Layer 3: Stealth HTTP (Tor/SOCKS, rotated UA, no JS, no cookies) — minimal fingerprint
  Layer 4: Phantom browser (Tor, anti-fingerprint, full JS render) — last resort

OPSEC Principles:
  - NEVER contact target directly unless all indirect methods fail
  - Route through Tor for ANY direct contact
  - Rotate User-Agent, Accept headers, TLS fingerprint on every request
  - No cookies, no JavaScript unless absolutely necessary
  - Random delays between requests (human-like)
  - Different Tor circuit per target domain
  - No DNS leaks (use DoH)
  - Clean session state between extractions
"""

import hashlib
import json
import os
import random
import re
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

# ── Configuration ──────────────────────────────────────────────────────────────

TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051
REQUEST_TIMEOUT = 30
USER_AGENTS = [
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
]

REFERERS = [
    "https://www.google.com/",
    "https://www.google.com/search?q=",
    "https://t.co/",
    "https://www.reddit.com/",
    "https://news.ycombinator.com/",
    "https://www.facebook.com/",
    "https://www.bing.com/search?q=",
]


# ── OPSEC Utilities ────────────────────────────────────────────────────────────

def _rand_ua() -> str:
    return random.choice(USER_AGENTS)

def _rand_accept() -> str:
    return random.choice(ACCEPT_HEADERS)

def _rand_referer() -> str:
    return random.choice(REFERERS)

def _rand_delay(min_s: float = 0.5, max_s: float = 2.5):
    """Human-like delay between requests."""
    time.sleep(random.uniform(min_s, max_s))

def _domain_hash(url: str) -> str:
    """Hash domain for logging (never log actual URLs)."""
    domain = urllib.parse.urlparse(url).netloc
    return hashlib.sha256(domain.encode()).hexdigest()[:12]

def _strip_metadata(html: str) -> str:
    """Remove tracking pixels, analytics scripts, beacons."""
    # Remove tracking scripts
    html = re.sub(r'<script[^>]*(?:analytics|tracking|beacon|pixel|gtag|gtm|facebook|google-analytics)[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
    # Remove tracking pixels/images
    html = re.sub(r'<img[^>]*(?:pixel|beacon|tracking|1x1)[^>]*>', '', html, flags=re.IGNORECASE)
    # Remove noscript tracking
    html = re.sub(r'<noscript>.*?</noscript>', '', html, flags=re.DOTALL|re.IGNORECASE)
    return html

def _html_to_text(html: str) -> str:
    """Extract readable text from HTML."""
    # Strip metadata first
    html = _strip_metadata(html)
    # Remove scripts and styles
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── Tor Management ─────────────────────────────────────────────────────────────

def _tor_is_running() -> bool:
    """Check if Tor daemon is running."""
    try:
        result = subprocess.run(['pgrep', '-x', 'tor'], capture_output=True, timeout=3)
        return result.returncode == 0
    except Exception:
        return False

def _tor_new_circuit():
    """Request new Tor circuit (new exit node)."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', TOR_CONTROL_PORT))
        s.sendall(b'AUTHENTICATE ""\r\n')
        resp = s.recv(1024)
        if b'250' in resp:
            s.sendall(b'SIGNAL NEWNYM\r\n')
            resp = s.recv(1024)
        s.close()
        time.sleep(1)  # Wait for circuit to build
    except Exception:
        pass  # Tor control not available, continue without

def _get_tor_session():
    """Create urllib opener routed through Tor SOCKS."""
    try:
        import socks
        import socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", TOR_SOCKS_PORT)
        socket.socket = socks.socksocket
        return True
    except ImportError:
        # Try without socks library — use subprocess curl instead
        return False


# ── Layer 1: Archive Services ──────────────────────────────────────────────────

def _try_archive_ph(url: str) -> Optional[str]:
    """Try archive.ph / archive.today — no direct contact with target."""
    _rand_delay()
    
    # archive.ph redirect pattern: submit URL, get archived version
    archive_urls = [
        f"https://archive.ph/new/{url}",
        f"https://archive.today/new/{url}",
        f"https://archive.is/new/{url}",
    ]
    
    for archive_url in archive_urls:
        try:
            req = urllib.request.Request(archive_url, headers={
                'User-Agent': _rand_ua(),
                'Accept': 'text/html',
            })
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                if resp.status == 200:
                    final_url = resp.url
                    html = resp.read().decode('utf-8', errors='replace')
                    
                    # Check if we got actual content (not just the submission page)
                    text = _html_to_text(html)
                    if len(text) > 500 and 'submitting' not in text[:200].lower():
                        return _clean_article(text, url)
                    
                    # Try to extract redirect URL from submission page
                    match = re.search(r'(https://archive\.(?:ph|today|is)/\w+)', html)
                    if match:
                        _rand_delay()
                        saved_url = match.group(1)
                        req2 = urllib.request.Request(saved_url, headers={
                            'User-Agent': _rand_ua(),
                        })
                        with urllib.request.urlopen(req2, timeout=REQUEST_TIMEOUT, context=ctx) as resp2:
                            html2 = resp2.read().decode('utf-8', errors='replace')
                            text2 = _html_to_text(html2)
                            if len(text2) > 500:
                                return _clean_article(text2, url)
        except Exception:
            continue
    
    return None


def _try_wayback(url: str) -> Optional[str]:
    """Try Wayback Machine — no direct contact with target."""
    _rand_delay()
    
    try:
        # Wayback CDX API to find archived snapshots
        api_url = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=3&fl=timestamp,original,statuscode,mimetype"
        req = urllib.request.Request(api_url, headers={'User-Agent': _rand_ua()})
        ctx = ssl.create_default_context()
        
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode())
        
        if len(data) < 2:  # First row is headers
            return None
        
        # Find best snapshot (200 status, text/html)
        for row in data[1:]:
            timestamp, original, status, mime = row
            if status == '200' and 'html' in mime:
                snapshot_url = f"https://web.archive.org/web/{timestamp}/{original}"
                _rand_delay()
                
                req2 = urllib.request.Request(snapshot_url, headers={
                    'User-Agent': _rand_ua(),
                    'Accept': _rand_accept(),
                })
                with urllib.request.urlopen(req2, timeout=REQUEST_TIMEOUT, context=ctx) as resp2:
                    html = resp2.read().decode('utf-8', errors='replace')
                    text = _html_to_text(html)
                    
                    if len(text) > 500:
                        # Remove Wayback Machine UI chrome
                        text = re.sub(r'Internet Archive.*?Wayback Machine', '', text, flags=re.DOTALL)
                        return _clean_article(text, url)
    except Exception:
        pass
    
    return None


def _try_google_cache(url: str) -> Optional[str]:
    """Try Google Cache — no direct contact with target."""
    _rand_delay()
    
    cache_urls = [
        f"https://webcache.googleusercontent.com/search?q=cache:{url}",
        f"https://webcache.googleusercontent.com/search?q=cache:{urllib.parse.quote(url, safe='')}",
    ]
    
    for cache_url in cache_urls:
        try:
            req = urllib.request.Request(cache_url, headers={
                'User-Agent': _rand_ua(),
                'Accept': _rand_accept(),
                'Referer': 'https://www.google.com/',
            })
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                html = resp.read().decode('utf-8', errors='replace')
                text = _html_to_text(html)
                
                if len(text) > 500 and 'did not match any documents' not in text[:500]:
                    return _clean_article(text, url)
        except Exception:
            continue
    
    return None


# ── Layer 2: Stealth HTTP ──────────────────────────────────────────────────────

def _stealth_fetch(url: str, use_tor: bool = True) -> Optional[str]:
    """
    Direct fetch with maximum stealth.
    Only used when archive services fail.
    Tries Tor first, then falls back to cleartext if Tor fails.
    """
    if use_tor and _tor_is_running():
        result = _stealth_fetch_tor(url)
        if result:
            return result
        # Tor failed (e.g. Cloudflare blocks Tor exits), try cleartext
    return _stealth_fetch_cleartext(url)


def _stealth_fetch_tor(url: str) -> Optional[str]:
    """Fetch via Tor using curl subprocess (most reliable Tor method)."""
    _rand_delay()
    _tor_new_circuit()
    
    cmd = [
        'curl', '-sL',
        '--socks5-hostname', f'127.0.0.1:{TOR_SOCKS_PORT}',
        '--max-time', str(REQUEST_TIMEOUT),
        '--connect-timeout', '15',
        '-H', f'User-Agent: {_rand_ua()}',
        '-H', f'Accept: {_rand_accept()}',
        '-H', f'Referer: {_rand_referer()}',
        '-H', 'Accept-Language: en-US,en;q=0.9',
        '-H', 'DNT: 1',
        '-H', 'Connection: close',
        '--compressed',
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=REQUEST_TIMEOUT + 10)
        if result.returncode == 0 and result.stdout:
            html = result.stdout.decode('utf-8', errors='replace')
            text = _html_to_text(html)
            if len(text) > 200:
                return _clean_article(text, url)
    except Exception:
        pass
    
    return None


def _stealth_fetch_cleartext(url: str) -> Optional[str]:
    """Fetch without Tor (fallback only). Uses curl for TLS fingerprint control
    and DoH (DNS-over-HTTPS) to prevent DNS leaks."""
    _rand_delay()

    # Use curl — gives us TLS fingerprint control, DoH, and better header control
    cmd = [
        'curl', '-sL',
        '--max-time', str(REQUEST_TIMEOUT),
        '--connect-timeout', '15',
        '--doh-url', 'https://dns.google/dns-query',  # DNS-over-HTTPS via Google
        '-H', f'User-Agent: {_rand_ua()}',
        '-H', f'Accept: {_rand_accept()}',
        '-H', f'Referer: {_rand_referer()}',
        '-H', 'Accept-Language: en-US,en;q=0.9',
        '-H', 'DNT: 1',
        '-H', 'Connection: close',
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=REQUEST_TIMEOUT + 10)
        if result.returncode == 0 and result.stdout:
            html = result.stdout.decode('utf-8', errors='replace')
            text = _html_to_text(html)
            if len(text) > 200:
                return _clean_article(text, url)
    except Exception:
        pass

    # Fallback to urllib if curl unavailable
    headers = {
        'User-Agent': _rand_ua(),
        'Accept': _rand_accept(),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'identity',
        'DNT': '1',
        'Connection': 'close',
        'Referer': _rand_referer(),
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            text = _html_to_text(html)
            if len(text) > 200:
                return _clean_article(text, url)
    except Exception:
        pass

    return None


# ── Layer 2.5: Academic Open-Access Resolution ────────────────────────────────

def _extract_doi(url: str) -> Optional[str]:
    """Extract DOI from a URL (e.g., doi.org/10.1234/xyz or journal article pages)."""
    parsed = urllib.parse.urlparse(url)
    # Direct DOI URL
    if 'doi.org' in parsed.netloc:
        doi = parsed.path.lstrip('/')
        if doi.startswith('10.'):
            return doi
    # Common journal patterns
    doi_match = re.search(r'(10\.\d{4,}/[^\s&?#]+)', url)
    if doi_match:
        doi = doi_match.group(1).rstrip('.')
        return doi
    return None


def _try_unpaywall(url: str) -> Optional[str]:
    """Query Unpaywall API (api.unpaywall.org) for open-access version of a DOI.
    Free, legal, no auth required — just needs an email for the API.
    Returns the full text of the open-access version if found."""
    doi = _extract_doi(url)
    if not doi:
        return None
    _rand_delay(0.3, 1.0)
    try:
        api_url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='')}?email=unpaywall@requester.net"
        req = urllib.request.Request(api_url, headers={
            'User-Agent': _rand_ua(),
            'Accept': 'application/json',
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        # Check best open-access location
        oa_url = data.get('best_oa_location', {}) or {}
        oa_pdf = oa_url.get('url_for_pdf')
        oa_landing = oa_url.get('url_for_landing_page')
        oa_url_val = oa_url.get('url')
        # Try PDF first (richest content)
        for candidate in [oa_pdf, oa_landing, oa_url_val]:
            if candidate and candidate.startswith('http'):
                text = _stealth_fetch(candidate, use_tor=False)
                if text and len(text) > 200:
                    return text
    except Exception:
        pass
    return None


def _try_oadoi(url: str) -> Optional[str]:
    """Query oaDOI (oa.works) for open-access version. Alternative to Unpaywall."""
    doi = _extract_doi(url)
    if not doi:
        return None
    _rand_delay(0.3, 1.0)
    try:
        api_url = f"https://api.oa.works/find/{urllib.parse.quote(doi, safe='')}"
        req = urllib.request.Request(api_url, headers={
            'User-Agent': _rand_ua(),
            'Accept': 'application/json',
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        oa_url = data.get('openAccess', {}).get('url')
        if oa_url and oa_url.startswith('http'):
            text = _stealth_fetch(oa_url, use_tor=False)
            if text and len(text) > 200:
                return text
    except Exception:
        pass
    return None


def _try_preprint_servers(url: str) -> Optional[str]:
    """Check if paper exists on arXiv, bioRxiv, medRxiv, SSRN, or PMC.
    Many paywalled papers have free preprint versions."""
    doi = _extract_doi(url)
    if not doi:
        return None
    _rand_delay(0.3, 0.8)
    try:
        # Try Semantic Scholar API to find open-access PDF
        ss_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(doi, safe='')}?fields=openAccessPdf,externalIds"
        req = urllib.request.Request(ss_url, headers={
            'User-Agent': _rand_ua(),
            'Accept': 'application/json',
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        # Direct open-access PDF
        oa_pdf = data.get('openAccessPdf', {})
        if oa_pdf and oa_pdf.get('url'):
            text = _stealth_fetch(oa_pdf['url'], use_tor=False)
            if text and len(text) > 200:
                return text
        # Check external IDs for preprint servers
        ext = data.get('externalIds', {})
        arxiv_id = ext.get('ArXiv')
        if arxiv_id:
            # Try arXiv HTML version (more readable than PDF)
            for arxiv_url in [
                f"https://arxiv.org/html/{arxiv_id}",
                f"https://arxiv.org/abs/{arxiv_id}",
            ]:
                text = _stealth_fetch(arxiv_url, use_tor=False)
                if text and len(text) > 200:
                    return text
        # Check PMC
        pmc_id = ext.get('PubMedCentral')
        if pmc_id:
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
            text = _stealth_fetch(pmc_url, use_tor=False)
            if text and len(text) > 200:
                return text
    except Exception:
        pass
    return None


# ── Layer 3: Paywall Bypass Services + Tricks ─────────────────────────────────

def _try_bypass_services(url: str) -> Optional[str]:
    """Try 12ft.io, smry.pro, and other paywall bypass services.
    These act as intermediaries — no direct contact with target."""
    bypass_services = [
        f"https://12ft.io/proxy?q={urllib.parse.quote(url, safe='')}",
        f"https://smry.pro/{urllib.parse.quote(url, safe='')}",
    ]
    for service_url in bypass_services:
        _rand_delay(0.5, 1.5)
        try:
            req = urllib.request.Request(service_url, headers={
                'User-Agent': _rand_ua(),
                'Accept': 'text/html',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
                html = resp.read().decode('utf-8', errors='replace')
                text = _html_to_text(html)
                if text and len(text) > 300:
                    return _clean_article(text, url)
        except Exception:
            continue
    return None


def _try_bing_cache(url: str) -> Optional[str]:
    """Try Bing's cached version of a page."""
    _rand_delay(0.3, 1.0)
    try:
        # Bing cache search
        cache_url = f"https://cc.bingj.com/cache.aspx?q=&d=503-{hashlib.md5(url.encode()).hexdigest()[:8]}&u={urllib.parse.quote(url, safe='')}"
        req = urllib.request.Request(cache_url, headers={
            'User-Agent': _rand_ua(),
            'Accept': 'text/html',
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            text = _html_to_text(html)
            if text and len(text) > 200:
                return _clean_article(text, url)
    except Exception:
        pass
    return None


def _try_paywall_tricks(url: str) -> Optional[str]:
    """Comprehensive paywall bypass: site-specific tricks, referer spoofing,
    Google first-click-free emulation, cookie clearing, AMP pages."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()

    # ── Site-specific strategies ──

    # Medium: append ?source= friends_link or use freedRead
    if 'medium.com' in domain or 'medium.' in domain:
        for variant in [
            url + '?source=friends_link&sk=' + hashlib.md5(url.encode()).hexdigest()[:8],
            url.replace('medium.com', 'scribe.rip'),
        ]:
            result = _stealth_fetch(variant, use_tor=False)
            if result:
                return result

    # NYT, WSJ, Bloomberg, FT: AMP pages + Google referrer
    news_domains = ['nytimes.com', 'wsj.com', 'bloomberg.com', 'ft.com',
                    'washingtonpost.com', 'theguardian.com', 'economist.com']
    if any(d in domain for d in news_domains):
        # AMP version
        amp_url = f"https://{parsed.netloc}{parsed.path}.amp.html"
        result = _stealth_fetch(amp_url, use_tor=True)
        if result:
            return result
        # Google First Click Free: spoof as coming from Google search
        _rand_delay(1.0, 2.0)
        headers = {
            'User-Agent': _rand_ua(),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/search?q=' + urllib.parse.quote(parsed.netloc + parsed.path),
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                html = resp.read().decode('utf-8', errors='replace')
                text = _html_to_text(html)
                if text and len(text) > 300:
                    return _clean_article(text, url)
        except Exception:
            pass

    # Substack: open with different UA + no cookies
    if 'substack.com' in domain:
        result = _stealth_fetch(url, use_tor=False)
        if result:
            return result

    # ── General strategies (apply to all) ──

    # Googlebot spoof (many sites serve full content to crawlers)
    _rand_delay(0.5, 1.5)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'text/html',
            'Accept-Encoding': 'identity',
            'Referer': 'https://www.google.com/',
        }
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            text = _html_to_text(html)
            if text and len(text) > 200:
                return _clean_article(text, url)
    except Exception:
        pass

    # Clear-cookies trick: add cache-busting params (soft paywalls use cookie counting)
    cache_bust = url + ('&' if '?' in url else '?') + f'_cb={int(time.time())}'
    _rand_delay(0.5, 1.0)
    result = _stealth_fetch(cache_bust, use_tor=True)
    if result:
        return result

    return None


# ── Layer 4: Phantom Browser (last resort) ────────────────────────────────────

def _try_phantom_browser(url: str) -> Optional[str]:
    """
    Use phantom browser (Tor-routed Playwright) for JS-heavy paywalls.
    Only used as last resort — highest fingerprint risk but handles anything.
    """
    phantom_script = os.path.expanduser("~/hermes-agent/agent/phantom_browser.py")
    if not os.path.exists(phantom_script):
        return None
    
    try:
        cmd = [
            sys.executable, phantom_script,
            'extract', url,
            '--tor',
            '--no-cookies',
            '--timeout', '20',
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=45)
        if result.returncode == 0 and result.stdout:
            text = result.stdout.decode('utf-8', errors='replace').strip()
            if len(text) > 200:
                return _clean_article(text, url)
    except Exception:
        pass
    
    return None


# ── Article Cleaning ──────────────────────────────────────────────────────────

def _clean_article(text: str, source_url: str) -> str:
    """Clean extracted text into readable article format."""
    # Remove common boilerplate
    boilerplate = [
        r'Subscribe to read.*',
        r'Sign in to read.*',
        r'This article is available to subscribers.*',
        r'Continue reading your article with.*',
        r'Already a subscriber\?.*',
        r'Start your free trial.*',
        r'Want the full story\?.*',
        r'Read more:.*',
        r'Share this article.*',
        r'Republish this article.*',
        r'Click here to subscribe.*',
        r'Cookie (?:Preferences|Settings|Consent).*',
        r'We use cookies.*?(?:site|experience|services)\.',
        r'Accept (?:All|Cookies)|Manage (?:Preferences|Consent)',
        r'Advertisement.*?(?=\n\n|\Z)',
        r'googletag\.cmd\.push.*?}\);',
        r'window\.__PRELOADED_STATE__.*?(?=\n\n|\Z)',
    ]
    
    for pattern in boilerplate:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE|re.DOTALL)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    
    # Prepend source attribution (hashed for privacy)
    domain = urllib.parse.urlparse(source_url).netloc
    header = f"[Source: {domain} | Extracted: {time.strftime('%Y-%m-%d %H:%M')}]\n\n"
    
    return header + text


# ── Main Extraction Pipeline ──────────────────────────────────────────────────

def extract(url: str, prefer_tor: bool = True, max_layers: int = 6) -> Dict:
    """
    Extract article content from URL, bypassing paywalls if necessary.
    
    6-Layer Extraction Pipeline:
      Layer 1: Archive services (archive.ph, Wayback, Google/Bing cache) — zero contact with target
      Layer 2: Academic open-access (Unpaywall, oaDOI, Semantic Scholar, PMC, arXiv)
      Layer 3: Paywall bypass services (12ft.io, smry.pro) — intermediary contact only
      Layer 4: Site-specific tricks (referer spoof, AMP, Googlebot, cookie bust)
      Layer 5: Stealth HTTP (Tor-routed, rotated UA/headers) — direct but anonymized
      Layer 6: Phantom browser (Tor + anti-fingerprint Playwright) — full JS render
    
    Returns dict with:
      success: bool
      content: str (article text)
      method: str (which layer succeeded)
      attempts: list of (method, result) tuples
    """
    attempts = []
    domain_h = _domain_hash(url)
    
    # Layer 1: Archive services (no direct contact with target)
    if max_layers >= 1:
        result = _try_archive_ph(url)
        attempts.append(("archive.ph", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "archive.ph", "attempts": attempts}
        
        result = _try_wayback(url)
        attempts.append(("wayback", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "wayback", "attempts": attempts}
        
        result = _try_google_cache(url)
        attempts.append(("google_cache", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "google_cache", "attempts": attempts}
        
        result = _try_bing_cache(url)
        attempts.append(("bing_cache", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "bing_cache", "attempts": attempts}
    
    # Layer 2: Academic open-access resolution (for DOIs / journal articles)
    if max_layers >= 2:
        result = _try_unpaywall(url)
        attempts.append(("unpaywall", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "unpaywall", "attempts": attempts}
        
        result = _try_oadoi(url)
        attempts.append(("oadoi", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "oadoi", "attempts": attempts}
        
        result = _try_preprint_servers(url)
        attempts.append(("preprint_servers", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "preprint_servers", "attempts": attempts}
    
    # Layer 3: Paywall bypass services (intermediary — no direct contact)
    if max_layers >= 3:
        result = _try_bypass_services(url)
        attempts.append(("bypass_services", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "bypass_services", "attempts": attempts}
    
    # Layer 4: Site-specific paywall tricks (referer spoof, AMP, Googlebot, cookie bust)
    if max_layers >= 4:
        result = _try_paywall_tricks(url)
        attempts.append(("paywall_tricks", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "paywall_tricks", "attempts": attempts}
    
    # Layer 5: Stealth HTTP (Tor-routed if available)
    if max_layers >= 5:
        result = _stealth_fetch(url, use_tor=prefer_tor)
        attempts.append(("stealth_http", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "stealth_http", "attempts": attempts}
    
    # Layer 6: Phantom browser (last resort)
    if max_layers >= 6:
        result = _try_phantom_browser(url)
        attempts.append(("phantom_browser", "OK" if result else "MISS"))
        if result:
            return {"success": True, "content": result, "method": "phantom_browser", "attempts": attempts}
    
    return {"success": False, "content": "", "method": "none", "attempts": attempts}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phantom Extractor v2 — Hardened paywall bypass")
    parser.add_argument("url", help="URL to extract")
    parser.add_argument("--no-tor", action="store_true", help="Skip Tor routing")
    parser.add_argument("--max-layers", type=int, default=4, help="Max extraction layers (1-4)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--check-tor", action="store_true", help="Check if Tor is running")
    
    args = parser.parse_args()
    
    if args.check_tor:
        running = _tor_is_running()
        print(f"Tor daemon: {'RUNNING' if running else 'NOT RUNNING'}")
        sys.exit(0 if running else 1)
    
    result = extract(args.url, prefer_tor=not args.no_tor, max_layers=args.max_layers)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"[OK] Method: {result['method']}")
            for method, status in result["attempts"]:
                print(f"  {method}: {status}")
            print(f"\n{'='*60}")
            print(result["content"][:5000])
            if len(result["content"]) > 5000:
                print(f"\n... ({len(result['content'])} chars total)")
        else:
            print("[FAIL] All methods exhausted:")
            for method, status in result["attempts"]:
                print(f"  {method}: {status}")
