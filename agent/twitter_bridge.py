#!/usr/bin/env python3
"""X/Twitter Feed Bridge for Hermes Agent.
Fetches tweets from tracked accounts and extracts repo links, mentions, and insights."""

import requests
import json
import re
import time
import os
from datetime import datetime
from pathlib import Path

# --- Config ---
CT0 = "2eeb0ca15994c40c324e89f800e43a7c4146ffcea6a5821cc72d3f59aea51d954be08a04cb005512157fcc912c68e8a38b9644e7409be575326a0edc84907bb09a1e4856af1ab653f58d2da2dbb04732"
AUTH = "2c16ccd91e59b677c6eee641350555897e8f57ca"
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

TRACKED_ACCOUNTS = {
    "Teknium": "1365020011123773442",  # @tek_nium - resolved via UserByScreenName
    "NousResearch": "1318419526132862976",
}

BRIDGE_DIR = Path.home() / ".hermes" / "twitter_bridge"
BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
SEEN_FILE = BRIDGE_DIR / "seen_tweets.json"
OUTPUT_FILE = BRIDGE_DIR / "latest_tweets.json"

HEADERS = {
    "Authorization": f"Bearer {BEARER}",
    "Cookie": f"auth_token={AUTH}; ct0={CT0}",
    "X-Csrf-Token": CT0,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Twitter-Active-User": "yes",
    "X-Twitter-Client-Language": "en",
    "Accept": "*/*",
    "Origin": "https://x.com",
    "Referer": "https://x.com/",
}

FEATURES = {
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False
}

def resolve_user_id(screen_name):
    """Resolve a screen name to user ID via UserByScreenName."""
    url = "https://x.com/i/api/graphql/BQ6xjFU6Mgm-WhEP3OiT9w/UserByScreenName"
    params = {
        "variables": json.dumps({"screen_name": screen_name, "withSafetyModeUserFields": True}),
        "features": json.dumps({"hidden_profile_subscriptions_enabled": True, "rweb_tipjar_consumption_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False, "subscriptions_verification_info_is_identity_verified_enabled": True, "subscriptions_verification_info_verified_since_enabled": True, "highlights_tweets_tab_ui_enabled": True, "responsive_web_twitter_article_notes_tab_enabled": True, "subscriptions_feature_can_gift_premium": True, "creator_subscriptions_tweet_preview_api_enabled": True, "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, "responsive_web_graphql_timeline_navigation_enabled": True}),
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        print(f"  UserByScreenName failed: {r.status_code}")
        return None
    data = r.json()
    user = data.get("data", {}).get("user", {}).get("result", {})
    return user.get("rest_id")

def fetch_tweets(user_id, screen_name, count=10):
    """Fetch recent tweets for a user."""
    url = "https://x.com/i/api/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets"
    variables = {
        "userId": str(user_id),
        "count": count,
        "includePromotedContent": False,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True,
        "withV2Timeline": True
    }
    params = {
        "variables": json.dumps(variables),
        "features": json.dumps(FEATURES),
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        print(f"  UserTweets failed for {screen_name}: {r.status_code} - {r.text[:200]}")
        return []
    
    tweets = []
    data = r.json()
    instructions = data.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
    
    for inst in instructions:
        entries = inst.get("entries", [])
        for entry in entries:
            content = entry.get("content", {})
            item = content.get("itemContent", {})
            if item.get("itemType") == "TimelineTweet":
                tweet = item.get("tweet_results", {}).get("result", {})
                legacy = tweet.get("legacy", {})
                
                # Extract tweet data
                tweet_data = {
                    "id": tweet.get("rest_id", ""),
                    "text": legacy.get("full_text", ""),
                    "created_at": legacy.get("created_at", ""),
                    "likes": legacy.get("favorite_count", 0),
                    "retweets": legacy.get("retweet_count", 0),
                    "replies": legacy.get("reply_count", 0),
                    "views": tweet.get("views", {}).get("count", "0"),
                    "url": f"https://x.com/{screen_name}/status/{tweet.get('rest_id', '')}",
                    "screen_name": screen_name,
                    "is_retweet": legacy.get("full_text", "").startswith("RT @"),
                    "links": [],
                    "github_links": [],
                    "media": [],
                }
                
                # Extract links
                urls = legacy.get("entities", {}).get("urls", [])
                for u in urls:
                    expanded = u.get("expanded_url", "")
                    if expanded:
                        tweet_data["links"].append(expanded)
                        if "github.com" in expanded:
                            tweet_data["github_links"].append(expanded)
                
                # Extract media
                media = legacy.get("entities", {}).get("media", [])
                for m in media:
                    tweet_data["media"].append({
                        "type": m.get("type", ""),
                        "url": m.get("media_url_https", ""),
                    })
                
                tweets.append(tweet_data)
    
    return tweets

def fetch_tweet_replies(tweet_id, screen_name):
    """Fetch top replies/quotes for a tweet to find repo links in comments."""
    url = "https://x.com/i/api/graphql/5sGVenr9szUMxfmfUwN7rA/TweetDetail"
    variables = {
        "focalTweetId": str(tweet_id),
        "withSafetyModeUserFields": True,
        "withVoice": True,
    }
    params = {
        "variables": json.dumps(variables),
        "features": json.dumps(FEATURES),
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        return []
    
    replies = []
    data = r.json()
    instructions = data.get("data", {}).get("threaded_conversation_with_injections_v2", {}).get("instructions", [])
    
    for inst in instructions:
        entries = inst.get("entries", [])
        for entry in entries:
            content = entry.get("content", {})
            items = content.get("items", [])
            if not items:
                items = [{"itemContent": content.get("itemContent", {})}]
            
            for item in items:
                ic = item.get("itemContent", item)
                if isinstance(ic, dict) and ic.get("itemType") == "TimelineTweet":
                    tweet = ic.get("tweet_results", {}).get("result", {})
                    legacy = tweet.get("legacy", {})
                    reply_text = legacy.get("full_text", "")
                    reply_user = legacy.get("user", {}).get("screen_name", "") if isinstance(legacy.get("user"), dict) else ""
                    
                    # Check for github links in reply
                    gh_links = []
                    for u in legacy.get("entities", {}).get("urls", []):
                        expanded = u.get("expanded_url", "")
                        if "github.com" in expanded:
                            gh_links.append(expanded)
                    
                    if reply_text and tweet.get("rest_id") != str(tweet_id):
                        replies.append({
                            "id": tweet.get("rest_id"),
                            "text": reply_text[:300],
                            "user": reply_user,
                            "github_links": gh_links,
                        })
    
    return replies[:10]

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def run_bridge():
    """Main bridge loop - fetch tweets from all tracked accounts."""
    print(f"[{datetime.utcnow().isoformat()}] Twitter Bridge starting...")
    
    seen = load_seen()
    all_new_tweets = []
    
    for screen_name, user_id in TRACKED_ACCOUNTS.items():
        print(f"\n--- Fetching @{screen_name} (ID: {user_id}) ---")
        
        # Resolve ID if needed
        if not user_id or user_id == "unknown":
            user_id = resolve_user_id(screen_name)
            if not user_id:
                print(f"  Could not resolve {screen_name}")
                continue
            TRACKED_ACCOUNTS[screen_name] = user_id
        
        tweets = fetch_tweets(user_id, screen_name, count=10)
        print(f"  Got {len(tweets)} tweets")
        
        for t in tweets:
            if t["id"] not in seen:
                seen[t["id"]] = datetime.utcnow().isoformat()
                all_new_tweets.append(t)
                print(f"\n  NEW: [{t['created_at']}] ♥{t['likes']} ↻{t['retweets']}")
                print(f"  {t['text'][:150]}")
                if t["github_links"]:
                    print(f"  GITHUB: {t['github_links']}")
                if t["media"]:
                    print(f"  MEDIA: {len(t['media'])} items")
                
                # For tweets with links, try to get replies for repo links
                if t["links"] or t["likes"] > 100:
                    print(f"  Fetching replies for hot tweet...")
                    replies = fetch_tweet_replies(t["id"], screen_name)
                    gh_in_replies = []
                    for r in replies:
                        if r["github_links"]:
                            gh_in_replies.extend(r["github_links"])
                            print(f"    REPLY GH: @{r['user']} -> {r['github_links']}")
                    t["reply_github_links"] = gh_in_replies
                
                time.sleep(2)  # Rate limit
            else:
                print(f"  Seen: {t['id'][:12]}...")
    
    # Save results
    save_seen(seen)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_new_tweets, f, indent=2, default=str)
    
    print(f"\n=== Summary: {len(all_new_tweets)} new tweets, {len(seen)} total seen ===")
    
    # Print digest
    if all_new_tweets:
        print("\n" + "="*60)
        print("TWITTER BRIDGE DIGEST")
        print("="*60)
        for t in all_new_tweets:
            print(f"\n@{t['screen_name']} [{t['created_at']}]")
            print(f"  {t['text'][:200]}")
            print(f"  ♥{t['likes']} ↻{t['retweets']} 👁{t['views']}")
            if t['github_links']:
                print(f"  REPO LINKS: {t['github_links']}")
            if t.get('reply_github_links'):
                print(f"  REPO IN REPLIES: {t['reply_github_links']}")
            print(f"  {t['url']}")
    
    return all_new_tweets

if __name__ == "__main__":
    tweets = run_bridge()
    print(f"\nDone. {len(tweets)} new tweets saved to {OUTPUT_FILE}")
