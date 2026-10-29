# broker-intel (private Apify Actor)

Multi-source collector for BrokerWeeklyIntel. Input `sources`: `reddit`, `play_store`, `app_store`, `youtube`, `linkedin`.

- **Reddit**: public `search.json` (restrict_sr, sort=new, t=month) across the given subreddits, plus top comments; 2 s delay between requests; residential proxy (IN) when available because Reddit blocks datacenter IPs.
- **Play Store / App Store**: newest reviews within `daysBack` (google-play-scraper, iTunes customer-reviews RSS).
- **YouTube**: popular comments on the 3 newest videos matching `youtube_query` (no API key).
- **LinkedIn**: public company page only, no login. If LinkedIn shows its auth wall, one `BLOCKED` row is output instead of trying to get around it.

Output rows: `source, broker, title, text, url, author, subreddit, created_utc, score, num_comments, rating, comments[]`. Per broker/source counts in key-value store `STATS`.

Deployed (private): `zippy_jogger/broker-intel` (id JPczg0Hrmcwio29fS). Redeploy: `cd actors/broker-intel && apify push` with APIFY_TOKEN set.

Note: Reddit JSON API returns 403 even via residential proxy; the actor falls back to public RSS (no score/comment counts) with 429 backoff.
