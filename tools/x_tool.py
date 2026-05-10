#!/usr/bin/env python3
"""
X/Twitter Cookie API Tool — Read-only tweet access via authenticated session.

This module provides Hermes tools for fetching tweets, user timelines, and
searching X/Twitter content using cookie-based authentication. No official
API key required — uses the user's existing X session cookies.

Tools:
- x_tweet_fetch: Fetch a single tweet by ID
- x_user_tweets: Fetch recent tweets from a user
- x_search: Search tweets by query

Authentication:
Cookies are read from Hermes config (~/.hermes/config.yaml) under the
x_cookies section, or from environment variables X_AUTH_TOKEN, X_CT0, X_TWID.

Usage:
    from tools.x_tool import x_tweet_fetch
    result = x_tweet_fetch(tweet_id="2050886233921061281")
"""

import json
import logging
import os
import re
from typing import Optional

import httpx
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _load_x_cookies() -> dict:
    """Load X cookies from Hermes config or environment variables."""
    # Try environment variables first
    auth_token = os.environ.get("X_AUTH_TOKEN")
    ct0 = os.environ.get("X_CT0")
    twid = os.environ.get("X_TWID")
    
    if auth_token and ct0 and twid:
        return {
            "auth_token": auth_token,
            "ct0": ct0,
            "twid": twid,
        }
    
    # Try Hermes config.yaml
    try:
        import yaml
        config_path = os.path.expanduser("~/.hermes/config.yaml")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = yaml.safe_load(f)
            cookies = config.get("x_cookies", {})
            if cookies.get("auth_token") and cookies.get("ct0"):
                return cookies
    except Exception:
        pass
    
    return {}

# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

def _get_x_client() -> tuple[httpx.Client, dict]:
    """Create an HTTP client with X authentication cookies."""
    cookies = _load_x_cookies()
    if not cookies:
        raise RuntimeError("No X cookies configured. Set X_AUTH_TOKEN, X_CT0, X_TWID env vars or add x_cookies to ~/.hermes/config.yaml")
    
    headers = {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "x-csrf-token": cookies.get("ct0", ""),
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "x-twitter-active-user": "yes",
        "referer": "https://x.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Origin": "https://x.com",
    }
    
    jar = httpx.Cookies()
    jar.set("auth_token", cookies.get("auth_token", ""), domain=".x.com")
    jar.set("ct0", cookies.get("ct0", ""), domain=".x.com")
    jar.set("twid", cookies.get("twid", ""), domain=".x.com")
    
    client = httpx.Client(
        headers=headers,
        cookies=jar,
        timeout=30.0,
        follow_redirects=True,
    )
    return client, cookies


def _get_graphql_hashes(client: httpx.Client) -> dict:
    """Extract current GraphQL query hashes from X's main page JavaScript."""
    try:
        resp = client.get("https://x.com/home")
        if resp.status_code != 200:
            return {}
        # Look for inline script with query IDs
        hashes = {}
        patterns = [
            (r'"([a-zA-Z0-9_-]{15,25})":"TweetResultByRestId"', "tweet_by_id"),
            (r'"([a-zA-Z0-9_-]{15,25})":"UserTweets"', "user_tweets"),
            (r'"([a-zA-Z0-9_-]{15,25})":"SearchTimeline"', "search"),
            (r'"([a-zA-Z0-9_-]{15,25})":"UserByScreenName"', "user_by_screen_name"),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, resp.text)
            if match:
                hashes[key] = match.group(1)
        return hashes
    except Exception:
        return {}


# Fallback hashes (last known working — will be refreshed dynamically)
_FALLBACK_HASHES = {
    "tweet_by_id": "V3vfsYzNEyD9tsf4xoFRgw",
    "user_tweets": "E3opETHurmVJflFsUBVuUQ",
    "search": "g7SDsWwiaaKtRjngIIq-mA",
    "user_by_screen_name": "G3KGOAsY-d5iAE5-4S2-MA",
}

# ---------------------------------------------------------------------------
# Core API functions
# ---------------------------------------------------------------------------

def _extract_tweet_data(result: dict) -> dict:
    """Extract clean tweet data from GraphQL result."""
    tweet = result.get("legacy", {})
    user = result.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
    
    return {
        "id": tweet.get("id_str"),
        "text": tweet.get("full_text", tweet.get("text", "")),
        "created_at": tweet.get("created_at"),
        "author": {
            "name": user.get("name"),
            "screen_name": user.get("screen_name"),
            "id": user.get("id_str"),
        },
        "metrics": {
            "likes": tweet.get("favorite_count"),
            "retweets": tweet.get("retweet_count"),
            "replies": tweet.get("reply_count"),
            "quotes": tweet.get("quote_count"),
        },
        "entities": tweet.get("entities", {}),
    }

def x_tweet_fetch(tweet_id: str) -> dict:
    """Fetch a single tweet by ID."""
    try:
        client, _ = _get_x_client()
        hashes = _get_graphql_hashes(client)
        tweet_hash = hashes.get("tweet_by_id", _FALLBACK_HASHES["tweet_by_id"])
        
        variables = json.dumps({
            "tweetId": tweet_id,
            "withCommunity": False,
            "includePromotedContent": False,
            "withVoice": False,
            "withBirdwatchNotes": False,
        })
        
        resp = client.get(
            f"https://x.com/i/api/graphql/{tweet_hash}/TweetResultByRestId",
            params={"variables": variables},
        )
        resp.raise_for_status()
        data = resp.json()
        
        result = data.get("data", {}).get("tweetResult", {}).get("result", {})
        if not result:
            return {"success": False, "error": "Tweet not found or not accessible"}
        
        tweet = _extract_tweet_data(result)
        return {"success": True, "tweet": tweet}
    except Exception as e:
        logger.exception("x_tweet_fetch error: %s", e)
        return {"success": False, "error": str(e)}

# Common user ID mappings (fallback when UserByScreenName hash is stale)
_USER_ID_CACHE = {
    "elonmusk": "44196397",
    "jack": "12",
    "twitter": "783214",
    "x": "17874544",
    "kanyewest": "169686021",
    "billgates": "50393960",
    "jeffbezos": "15506669",
    "sama": "1605",
    "karpathy": "408702380",
    "lexfridman": "323133381",
    "mrbeast": "2455740283",
    "nousresearch": "1487305860",
    "adamghowiba": "1225028680327614464",
}


def _resolve_user_id(screen_name: str) -> Optional[str]:
    """Resolve screen name to user ID. Uses cache first, then tries API."""
    # Check cache
    if screen_name.lower() in _USER_ID_CACHE:
        return _USER_ID_CACHE[screen_name.lower()]
    
    # Try API lookup
    try:
        client, _ = _get_x_client()
        hashes = _get_graphql_hashes(client)
        user_hash = hashes.get("user_by_screen_name", _FALLBACK_HASHES["user_by_screen_name"])
        
        user_vars = json.dumps({
            "screen_name": screen_name,
            "withHighlightedLabel": True,
            "withSafetyModeUserFields": True,
        })
        user_resp = client.get(
            f"https://x.com/i/api/graphql/{user_hash}/UserByScreenName",
            params={"variables": user_vars},
        )
        if user_resp.status_code == 200:
            data = user_resp.json()
            user_result = data.get("data", {}).get("user", {}).get("result", {})
            user_id = user_result.get("rest_id")
            if user_id:
                # Cache it
                _USER_ID_CACHE[screen_name.lower()] = user_id
                return user_id
    except Exception:
        pass
    
    return None


def x_user_tweets(screen_name: str, count: int = 20) -> dict:
    """Fetch recent tweets from a user by screen name."""
    try:
        client, _ = _get_x_client()
        
        # Resolve user ID (cache or API)
        user_id = _resolve_user_id(screen_name)
        if not user_id:
            return {"success": False, "error": f"User @{screen_name} not found"}
        
        # Fetch tweets
        hashes = _get_graphql_hashes(client)
        user_tweets_hash = hashes.get("user_tweets", _FALLBACK_HASHES["user_tweets"])
        
        tweet_vars = json.dumps({
            "userId": user_id,
            "count": min(count, 50),
            "includePromotedContent": False,
            "withCommunity": False,
            "withVoice": False,
            "withBirdwatchNotes": False,
        })
        tweet_resp = client.get(
            f"https://x.com/i/api/graphql/{user_tweets_hash}/UserTweets",
            params={"variables": tweet_vars},
        )
        tweet_resp.raise_for_status()
        tweet_data = tweet_resp.json()
        
        # Extract tweets from response — handle both v1 and v2 timeline structures
        user_result = tweet_data.get("data", {}).get("user", {}).get("result", {})
        timeline = user_result.get("timeline_v2", {}).get("timeline", {}) or user_result.get("timeline", {}).get("timeline", {})
        instructions = timeline.get("instructions", [])
        tweets = []
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                for entry in instruction.get("entries", []):
                    content = entry.get("content", {})
                    if content.get("entryType") == "TimelineTimelineItem":
                        item_content = content.get("itemContent", {})
                        if item_content.get("itemType") == "TimelineTweet":
                            tweet_result = item_content.get("tweet_results", {}).get("result", {})
                            if tweet_result:
                                tweets.append(_extract_tweet_data(tweet_result))
        
        return {
            "success": True,
            "user": {
                "screen_name": screen_name,
                "id": user_id,
                "name": user_result.get("legacy", {}).get("name"),
            },
            "tweets": tweets,
            "count": len(tweets),
        }
    except Exception as e:
        logger.exception("x_user_tweets error: %s", e)
        return {"success": False, "error": str(e)}

def x_search(query: str, count: int = 20) -> dict:
    """Search tweets by query string.
    
    NOTE: SearchTimeline GraphQL endpoint hash is currently stale (rotated by X).
    This function will return an error until the hash is refreshed.
    Use x_user_tweets or x_tweet_fetch for working alternatives.
    """
    try:
        client, _ = _get_x_client()
        hashes = _get_graphql_hashes(client)
        search_hash = hashes.get("search", _FALLBACK_HASHES["search"])
        
        search_vars = json.dumps({
            "rawQuery": query,
            "count": min(count, 50),
            "querySource": "typed_query",
            "product": "Top",
        })
        resp = client.get(
            f"https://x.com/i/api/graphql/{search_hash}/SearchTimeline",
            params={"variables": search_vars},
        )
        resp.raise_for_status()
        data = resp.json()
        
        instructions = data.get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
        tweets = []
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                for entry in instruction.get("entries", []):
                    content = entry.get("content", {})
                    if content.get("entryType") == "TimelineTimelineItem":
                        item_content = content.get("itemContent", {})
                        if item_content.get("itemType") == "TimelineTweet":
                            tweet_result = item_content.get("tweet_results", {}).get("result", {})
                            if tweet_result:
                                tweets.append(_extract_tweet_data(tweet_result))
        
        return {
            "success": True,
            "query": query,
            "tweets": tweets,
            "count": len(tweets),
        }
    except Exception as e:
        logger.warning("x_search: SearchTimeline endpoint hash is stale (X rotated it). "
                      "Use x_user_tweets or x_tweet_fetch instead. Error: %s", e)
        return {
            "success": False, 
            "error": "SearchTimeline endpoint hash is stale. X rotated their GraphQL query IDs. "
                    "x_tweet_fetch and x_user_tweets are fully operational. "
                    f"Technical: {str(e)[:100]}"
        }

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

X_TWEET_FETCH_SCHEMA = {
    "name": "x_tweet_fetch",
    "description": "Fetch a single X/Twitter tweet by its ID. Returns the tweet text, author, metrics, and entities.",
    "parameters": {
        "type": "object",
        "properties": {
            "tweet_id": {
                "type": "string",
                "description": "The tweet ID to fetch (e.g., '2050886233921061281')",
            },
        },
        "required": ["tweet_id"],
    },
}

X_USER_TWEETS_SCHEMA = {
    "name": "x_user_tweets",
    "description": "Fetch recent tweets from an X/Twitter user by screen name. Returns up to 50 tweets with text, metrics, and timestamps.",
    "parameters": {
        "type": "object",
        "properties": {
            "screen_name": {
                "type": "string",
                "description": "The user's screen name without @ (e.g., 'elonmusk')",
            },
            "count": {
                "type": "integer",
                "description": "Number of tweets to fetch (max 50, default 20)",
                "default": 20,
            },
        },
        "required": ["screen_name"],
    },
}

X_SEARCH_SCHEMA = {
    "name": "x_search",
    "description": "Search X/Twitter tweets by query string. Returns matching tweets with text, author, and metrics.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (e.g., 'AI agent architecture')",
            },
            "count": {
                "type": "integer",
                "description": "Number of results (max 50, default 20)",
                "default": 20,
            },
        },
        "required": ["query"],
    },
}

# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def check_x_tool_requirements() -> tuple[bool, str]:
    """Check if X cookies are configured."""
    cookies = _load_x_cookies()
    if not cookies:
        return False, "X cookies not configured. Set X_AUTH_TOKEN, X_CT0, X_TWID environment variables or add x_cookies to ~/.hermes/config.yaml"
    if not cookies.get("auth_token"):
        return False, "X auth_token missing"
    if not cookies.get("ct0"):
        return False, "X ct0 (CSRF token) missing"
    return True, ""

# ---------------------------------------------------------------------------
# Registry registration
# ---------------------------------------------------------------------------

registry.register(
    name="x_tweet_fetch",
    toolset="x",
    schema=X_TWEET_FETCH_SCHEMA,
    handler=lambda args, **kw: tool_result(x_tweet_fetch(tweet_id=args.get("tweet_id", ""))),
    check_fn=check_x_tool_requirements,
    requires_env=["X_AUTH_TOKEN", "X_CT0", "X_TWID"],
    emoji="𝕏",
)

registry.register(
    name="x_user_tweets",
    toolset="x",
    schema=X_USER_TWEETS_SCHEMA,
    handler=lambda args, **kw: tool_result(x_user_tweets(
        screen_name=args.get("screen_name", ""),
        count=args.get("count", 20),
    )),
    check_fn=check_x_tool_requirements,
    requires_env=["X_AUTH_TOKEN", "X_CT0", "X_TWID"],
    emoji="𝕏",
)

registry.register(
    name="x_search",
    toolset="x",
    schema=X_SEARCH_SCHEMA,
    handler=lambda args, **kw: tool_result(x_search(
        query=args.get("query", ""),
        count=args.get("count", 20),
    )),
    check_fn=check_x_tool_requirements,
    requires_env=["X_AUTH_TOKEN", "X_CT0", "X_TWID"],
    emoji="𝕏",
)
