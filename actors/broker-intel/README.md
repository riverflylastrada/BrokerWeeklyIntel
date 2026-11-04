# broker-intel (private Apify Actor)

Multi-source collector for BrokerWeeklyIntel. Input `sources`: `reddit`, `play_store`, `app_store`, `youtube`, `linkedin`.

- **Reddit**: public `search.json`, falling back to public RSS when blocked. Low and slow by default: concurrency 1, randomized 8–15 s delay between requests, backoff 60/120/300 s on HTTP 429, brokers run one after another with a 30 s pause. Residential proxy (IN) when available.
- **Play Store / App Store**: newest reviews within `daysBack` (google-play-scraper, iTunes customer-reviews RSS).
- **YouTube**: popular comments on the 3 newest videos matching `youtube_query` (no API key).
- **LinkedIn**: public company page only, no login. If LinkedIn shows its auth wall, one `BLOCKED` row is output instead of trying to get around it.

Output rows: `source, broker, title, text, url, author, subreddit, created_utc, score, num_comments, rating, comments[]`. Per broker/source counts in key-value store `STATS`.

Deployed (private): `zippy_jogger/broker-intel` (id JPczg0Hrmcwio29fS). Redeploy: `cd actors/broker-intel && apify push` with APIFY_TOKEN set.

Note: Reddit JSON API returns 403 even via residential proxy; the actor falls back to public RSS (no score/comment counts) with 429 backoff.

## Mentions mode (twice-daily social listening)

`mode: "mentions"` + `category` (brokers|banks), `daysBack: 1`. Reddit uses one multi-subreddit RSS search per keyword; Play/App Store newest reviews. Each row is classified (sentiment positive/neutral/negative from star rating or keywords; issue tag outage/login/withdrawal/charges/support/kyc/fraud/praise), deduped by URL (App Store rows get a content-hash fragment), filtered by last-seen timestamp per entity/source (named KV store `social-listening-state`, key = category, updated only after a successful post), and posted to the PaisaInsights RPC `ingest_social_mentions` (secret token in task input, `isSecret`). Schema: `social/schema.sql`.

Apify tasks: `social-buzz-brokers` (08:00/20:00 IST), `social-buzz-banks` (08:40/20:40 IST), 512 MB, low and slow. Backup: `.github/workflows/social-listening-backup.yml` (no-op if a run already happened in the window).
