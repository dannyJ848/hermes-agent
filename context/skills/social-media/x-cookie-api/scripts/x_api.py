"""
X/Twitter API via cookie auth - READ ONLY
Uses Python requests with session cookies. NEVER post, like, retweet, or interact.

Usage:
    from x_api import get_user_tweets
    result = get_user_tweets("1225028680327614464", count=10)
"""
import requests, json, re

# === INSERT USER'S COOKIES HERE ===
AUTH_TOKEN = ""
CT0 = ""
TWID = ""
USER_ID = ""  # Extract from twid (the numeric part after u%3D)
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

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
    "responsive_web_enhance_cards_enabled": False,
}

def _session():
    s = requests.Session()
    s.cookies.update({"auth_token": AUTH_TOKEN, "ct0": CT0, "twid": TWID})
    s.headers.update({
        "Authorization": f"Bearer {BEARER}",
        "x-csrf-token": CT0,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "Referer": "https://x.com/home",
    })
    return s

def _extract_tweet(entry):
    """Extract tweet data from a timeline entry. Handles 3 different JSON nesting patterns."""
    content = entry.get("content", {})
    ic = content.get("itemContent", {})
    if not ic:
        return None

    tr = ic.get("tweet_results", {}).get("result", {})
    # Try direct legacy first, then nested under .tweet
    legacy = tr.get("legacy", {})
    if not legacy.get("full_text"):
        tr = tr.get("tweet", {})
        legacy = tr.get("legacy", {})

    text = legacy.get("full_text", "")
    if not text:
        return None

    user = tr.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
    return {
        "text": text,
        "screen_name": user.get("screen_name", "?"),
        "name": user.get("name", ""),
        "likes": legacy.get("favorite_count", 0),
        "retweets": legacy.get("retweet_count", 0),
        "replies": legacy.get("reply_count", 0),
        "created_at": legacy.get("created_at", ""),
        "tweet_id": legacy.get("id_str", ""),
        "is_retweet": text.startswith("RT @"),
    }

def get_user_tweets(user_id=None, count=10):
    """Get recent tweets from a user. Returns list of tweet dicts."""
    uid = user_id or USER_ID
    s = _session()
    url = "https://x.com/i/api/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets"
    params = {
        "variables": json.dumps({
            "userId": uid, "count": count,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": False,
            "withVoice": False, "withV2Timeline": True,
        }),
        "features": json.dumps(FEATURES),
    }
    r = s.get(url, params=params)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "size": len(r.text)}

    tweets = []
    try:
        instructions = r.json()["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
        for inst in instructions:
            for entry in inst.get("entries", []):
                t = _extract_tweet(entry)
                if t:
                    tweets.append(t)
    except Exception as e:
        return {"error": str(e), "raw_size": len(r.text)}
    return tweets

def get_gql_hashes():
    """Fetch current GraphQL operation hashes from X's JS bundles."""
    r = requests.get("https://x.com", headers={"User-Agent": "Mozilla/5.0"})
    urls = re.findall(r'https://abs\.twimg\.com/responsive-web/client-web/main\.[a-f0-9]+\.js', r.text)
    if not urls:
        return {}
    r2 = requests.get(urls[0], headers={"User-Agent": "Mozilla/5.0"})
    hashes = re.findall(r'"([a-zA-Z0-9_-]{15,25})":"(SearchTimeline|UserTweets|HomeTimeline|UserByScreenName|TweetDetail)"', r2.text)
    return {name: h for h, name in hashes}

if __name__ == "__main__":
    print("=== Current GQL Hashes ===")
    print(get_gql_hashes())
    print("\n=== User Tweets ===")
    tweets = get_user_tweets(count=10)
    if isinstance(tweets, list):
        for t in tweets:
            rt = " [RT]" if t["is_retweet"] else ""
            print(f"@{t['screen_name']}{rt}: {t['text'][:120]}")
            print(f"  ♥{t['likes']} RT:{t['retweets']} Replies:{t['replies']}\n")
    else:
        print(tweets)
