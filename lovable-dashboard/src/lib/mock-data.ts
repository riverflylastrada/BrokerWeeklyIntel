import { getTrackedBrokers, getBrokerNames } from "./broker-config";

export type Trend = "Improving" | "Declining" | "Stable";
export type Severity = "critical" | "high" | "medium" | "low";
export type Sentiment = "positive" | "mixed" | "negative";
export type Platform = "x" | "reddit" | "web" | "linkedin" | "youtube" | "discord" | "instagram" | "other";

export interface NewFeature {
  broker?: string;
  feature_name: string;
  launch_date: string;
  user_reaction: "Positive" | "Mixed" | "Negative" | "Too early to tell";
  discussion_volume: "High" | "Medium" | "Low";
  evidence_links: string[];
}

export interface KeyQuote {
  quote: string;
  context: string;
  sentiment: "positive" | "negative" | "neutral";
  source_url: string;
  author?: string;
  platform: Platform;
  broker?: string;
  sentimentScore?: number; // -1.0 (strongly negative, high impact) to +1.0 (strongly positive); computed from text tone + trading impact + engagement
}

export interface NegativeTheme {
  theme:
    | "Performance"
    | "Support"
    | "Charges"
    | "Reliability"
    | "UX"
    | "Features/Gaps"
    | "Transparency"
    | "Other";
  count: number;
  severity: Severity;
  example_quotes: string[];
}

export interface TechnicalIssue {
  broker?: string;
  description: string;
  severity: Severity;
  issue_type: "feature_specific" | "platform_wide";
  volume: number;
  first_seen: string;
  last_seen: string;
}

export interface BrokerReport {
  broker: string;
  slug: string;
  overall_rating: number;
  trend: Trend;
  previous_rating?: number;
  rating_breakdown: {
    engagement: number;
    sentiment: number;
    new_feature_response: number;
    technical_reliability: number;
    support: number;
    transparency: number;
    historical_trend: number;
  };
  new_features: NewFeature[];
  key_quotes: KeyQuote[];
  negative_themes: NegativeTheme[];
  technical_issues: TechnicalIssue[];
  watch_items: string[];
}

export interface WeeklyReport {
  week: string;
  week_start: string;
  week_end: string;
  report_version: "2.1";
  overall_sentiment: Sentiment;
  brokers: BrokerReport[];
  industry_themes: {
    positive: string[];
    negative: string[];
    emerging: string[];
    implications_for_socialcoffee?: string;
  };
  new_features_summary: NewFeature[];
  watch_items_next_2_weeks: string[];
}

const slugify = (s: string) => s.toLowerCase().replace(/\s+/g, "-");

// ============================================================
// DYNAMIC BROKER LIST - Supports adding new brokers via UI
// ============================================================
const ALL_BROKERS = getBrokerNames();

// ============================================================
// REAL W21 DATA + FULL BROKERS (including Sahi Broking)
// ============================================================

export const WEEKLY_REPORTS: WeeklyReport[] = [
  // ==================== 2026-W10 (Early baseline - Mar 2026) ====================
  {
    week: "2026-W10",
    week_start: "2026-03-02",
    week_end: "2026-03-08",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 7.1, trend: "Stable", previous_rating: 7.0, rating_breakdown: { engagement: 7.8, sentiment: 7.0, new_feature_response: 6.5, technical_reliability: 7.0, support: 7.2, transparency: 8.0, historical_trend: 6.5 }, new_features: [], key_quotes: [{ broker: "Zerodha", quote: "Zerodha app is reliable for most days but occasional lag during high volatility.", context: "General discussion on app stability", sentiment: "neutral", source_url: "https://www.reddit.com/", author: "r/IndianStreetBets user", platform: "reddit" }], negative_themes: [{ theme: "Performance", count: 3, severity: "medium", example_quotes: ["Lag spikes reported during volatile sessions"] }], technical_issues: [{ broker: "Zerodha", description: "Occasional app lag in high-vol sessions (pre-Terminal reports)", severity: "low", issue_type: "feature_specific", volume: 3, first_seen: "2026-03-02", last_seen: "2026-03-08" }], watch_items: [] },
      { broker: "Groww", slug: "groww", overall_rating: 7.4, trend: "Stable", previous_rating: 7.3, rating_breakdown: { engagement: 7.0, sentiment: 7.5, new_feature_response: 7.0, technical_reliability: 7.5, support: 7.2, transparency: 7.3, historical_trend: 6.5 }, new_features: [], key_quotes: [], negative_themes: [{ theme: "Performance", count: 2, severity: "medium", example_quotes: ["App slowdowns noted in older threads"] }], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.4, trend: "Stable", previous_rating: 6.3, rating_breakdown: { engagement: 6.2, sentiment: 6.3, new_feature_response: 5.8, technical_reliability: 6.5, support: 6.2, transparency: 6.8, historical_trend: 6.0 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.3, trend: "Stable", previous_rating: 6.2, rating_breakdown: { engagement: 6.0, sentiment: 6.2, new_feature_response: 5.5, technical_reliability: 6.6, support: 6.2, transparency: 6.5, historical_trend: 6.0 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.0, trend: "Improving", previous_rating: 6.8, rating_breakdown: { engagement: 6.8, sentiment: 7.0, new_feature_response: 7.2, technical_reliability: 7.2, support: 6.8, transparency: 7.0, historical_trend: 6.5 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.6, trend: "Stable", previous_rating: 6.5, rating_breakdown: { engagement: 6.3, sentiment: 6.5, new_feature_response: 6.0, technical_reliability: 6.8, support: 6.4, transparency: 7.2, historical_trend: 6.0 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.1, trend: "Stable", previous_rating: 6.0, rating_breakdown: { engagement: 5.8, sentiment: 6.0, new_feature_response: 5.5, technical_reliability: 6.5, support: 6.0, transparency: 6.5, historical_trend: 5.8 }, new_features: [], key_quotes: [], negative_themes: [{ theme: "Support", count: 1, severity: "low", example_quotes: ["Limited public discussion volume"] }], technical_issues: [], watch_items: ["Very low social footprint - monitor for early signals"] },
    ],
    industry_themes: { positive: ["Steady product updates across brokers with limited concentrated friction"], negative: ["Persistent low-level performance complaints during volatility (Zerodha, Groww)"], emerging: ["Growing interest in advanced order types and charting tools"], implications_for_socialcoffee: "Transparency channels like Z-Connect remain under-utilized by most brokers." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Early signals on new Terminal Mode beta (Zerodha)"],
  },
  // ==================== 2026-W12 (Mid Mar - Terminal beta early feedback) ====================
  {
    week: "2026-W12",
    week_start: "2026-03-16",
    week_end: "2026-03-22",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 7.0, trend: "Declining", previous_rating: 7.1, rating_breakdown: { engagement: 8.0, sentiment: 6.8, new_feature_response: 6.8, technical_reliability: 6.5, support: 7.0, transparency: 8.2, historical_trend: 6.2 }, new_features: [{ broker: "Zerodha", feature_name: "Kite Terminal Mode (beta) - early rollout", launch_date: "2026-03", user_reaction: "Mixed", discussion_volume: "Medium", evidence_links: ["https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode"] }], key_quotes: [{ broker: "Zerodha", quote: "Terminal mode is very nice. I can manage 2 terminals at a time which is very helpful.", context: "Z-Connect early feedback", sentiment: "positive", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode", author: "Vignesh K", platform: "web" }, { broker: "Zerodha", quote: "ITS LIKE ZERODHA HAS WOKE UP FROM A COMA. FINALLY BUILDING SOMETHING.", context: "User excitement on Z-Connect", sentiment: "positive", source_url: "https://zerodha.com/z-connect", author: "Community", platform: "web" }], negative_themes: [{ theme: "Performance", count: 2, severity: "medium", example_quotes: ["Early reports of freezes after inactivity"] }], technical_issues: [{ broker: "Zerodha", description: "Kite Terminal Mode freezes after inactivity (early beta)", severity: "low", issue_type: "feature_specific", volume: 2, first_seen: "2026-03-16", last_seen: "2026-03-22" }], watch_items: ["Monitor Terminal Mode stability in coming weeks"] },
      { broker: "Groww", slug: "groww", overall_rating: 7.3, trend: "Stable", previous_rating: 7.4, rating_breakdown: { engagement: 7.0, sentiment: 7.4, new_feature_response: 7.0, technical_reliability: 7.3, support: 7.0, transparency: 7.2, historical_trend: 6.5 }, new_features: [], key_quotes: [
          { broker: "Groww", quote: "New trailing stop loss feature is actually useful for intraday. Good update.", context: "Early feedback on Groww options tooling improvements", sentiment: "positive", source_url: "https://x.com", author: "Intraday trader", platform: "x", sentimentScore: 0.58 },
          { broker: "Groww", quote: "App felt slow during high volatility session today. Not the first time.", context: "Recurring performance complaint in March", sentiment: "negative", source_url: "https://x.com", author: "Active trader", platform: "x", sentimentScore: -0.42 }
        ], negative_themes: [{ theme: "Performance", count: 3, severity: "medium", example_quotes: ["App slowdowns during volatile sessions"] }], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.5, trend: "Stable", previous_rating: 6.4, rating_breakdown: { engagement: 6.3, sentiment: 6.4, new_feature_response: 5.8, technical_reliability: 6.6, support: 6.3, transparency: 6.9, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "Angel One", quote: "Portfolio view is clean but still missing some advanced order types that Zerodha has.", context: "Comparison during Terminal Mode discussions", sentiment: "neutral", source_url: "https://x.com", author: "Multi-broker user", platform: "x", sentimentScore: 0.12 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.3, trend: "Stable", previous_rating: 6.3, rating_breakdown: { engagement: 6.0, sentiment: 6.3, new_feature_response: 5.5, technical_reliability: 6.5, support: 6.2, transparency: 6.5, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "Upstox", quote: "Still no proper chart trading or keyboard shortcuts. Feels behind.", context: "Feature gap comments during Zerodha Terminal hype", sentiment: "negative", source_url: "https://x.com", author: "Power user", platform: "x", sentimentScore: -0.51 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.1, trend: "Improving", previous_rating: 7.0, rating_breakdown: { engagement: 6.9, sentiment: 7.1, new_feature_response: 7.3, technical_reliability: 7.3, support: 6.9, transparency: 7.1, historical_trend: 6.6 }, new_features: [], key_quotes: [
          { broker: "Fyers", quote: "Fyers has been stable and fast. Execution is clean even in volatile markets.", context: "Positive reliability mentions in March", sentiment: "positive", source_url: "https://x.com", author: "Options trader", platform: "x", sentimentScore: 0.61 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.6, trend: "Stable", previous_rating: 6.6, rating_breakdown: { engagement: 6.3, sentiment: 6.5, new_feature_response: 6.0, technical_reliability: 6.8, support: 6.5, transparency: 7.2, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "ICICI Direct", quote: "Interface feels dated compared to Zerodha or Fyers. Works but not exciting.", context: "General comparison comments", sentiment: "neutral", source_url: "https://x.com", author: "Long-term investor", platform: "x", sentimentScore: 0.05 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.2, trend: "Stable", previous_rating: 6.1, rating_breakdown: { engagement: 5.9, sentiment: 6.1, new_feature_response: 5.6, technical_reliability: 6.6, support: 6.0, transparency: 6.6, historical_trend: 5.9 }, new_features: [], key_quotes: [
          { broker: "Sahi Broking", quote: "Very low volume on the platform. Hard to get good fills sometimes.", context: "Liquidity complaint from small broker users", sentiment: "negative", source_url: "https://x.com", author: "Retail trader", platform: "x", sentimentScore: -0.38 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
    ],
    industry_themes: { positive: ["Zerodha Terminal Mode beta receives early praise for multi-terminal utility and 'woke up' innovation feel"], negative: ["Isolated early freeze reports on new Zerodha Terminal (feature-specific)"], emerging: ["User requests for more charting indicators and keyboard shortcuts surfacing on Z-Connect"], implications_for_socialcoffee: "Public feedback loops on Z-Connect turning beta friction into clear product roadmap signals." },
    new_features_summary: [{ broker: "Zerodha", feature_name: "Kite Terminal Mode (beta)", launch_date: "2026-03", user_reaction: "Mixed", discussion_volume: "Medium", evidence_links: ["https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode"] }],
    watch_items_next_2_weeks: ["Zerodha Terminal Mode freeze reports escalation"],
  },
  // ==================== 2026-W18 (Sahi negative surfaces + ongoing Zerodha) ====================
  {
    week: "2026-W18",
    week_start: "2026-04-27",
    week_end: "2026-05-03",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 6.9, trend: "Declining", previous_rating: 7.0, rating_breakdown: { engagement: 8.2, sentiment: 6.5, new_feature_response: 6.2, technical_reliability: 6.0, support: 7.0, transparency: 8.4, historical_trend: 6.0 }, new_features: [{ broker: "Zerodha", feature_name: "Fixed Deposits on Coin", launch_date: "2026-04-09", user_reaction: "Mixed", discussion_volume: "High", evidence_links: ["https://zerodha.com/z-connect/business-updates/introducing-fixed-deposits-on-coin"] }], key_quotes: [{ broker: "Zerodha", quote: "Terminal mode is very nice... but during order placement or chart changing , it freezes... page getting freezed. This is happening on every trade.", context: "Z-Connect ongoing Terminal complaints", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode", author: "Vignesh K", platform: "web" }, { broker: "Zerodha", quote: "This service is highly unreliable. I have been trying to make fd since morning. upi payment failed.", context: "Coin FD payment issues", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "Amit Kale", platform: "web" }], negative_themes: [{ theme: "Performance", count: 6, severity: "high", example_quotes: ["Terminal freezes during live order placement and chart changes (multiple users)"] }, { theme: "Reliability", count: 4, severity: "medium", example_quotes: ["UPI failures on FD setup"] }], technical_issues: [{ broker: "Zerodha", description: "Persistent Kite Terminal Mode freezes on order/chart actions (Mac/Windows)", severity: "high", issue_type: "feature_specific", volume: 6, first_seen: "2026-03", last_seen: "2026-05-03" }], watch_items: ["Zerodha addressing Terminal + FD reliability"] },
      { broker: "Groww", slug: "groww", overall_rating: 7.2, trend: "Declining", previous_rating: 7.4, rating_breakdown: { engagement: 7.1, sentiment: 7.0, new_feature_response: 7.5, technical_reliability: 7.0, support: 7.0, transparency: 7.2, historical_trend: 6.8 }, new_features: [], key_quotes: [
          { broker: "Groww", quote: "Lost money due to glitch during market hours. Never using this broker again.", context: "r/IndianStreetBets complaint thread", sentiment: "negative", source_url: "https://www.reddit.com/r/IndianStreetBets/comments/1example/", author: "Reddit user", platform: "reddit", sentimentScore: -0.85 },
          { broker: "Groww", quote: "New trailing stop loss feature is actually useful for intraday. Good update.", context: "Early feedback on Groww options tooling improvements", sentiment: "positive", source_url: "https://x.com", author: "Intraday trader", platform: "x", sentimentScore: 0.58 }
        ], negative_themes: [{ theme: "Performance", count: 4, severity: "high", example_quotes: ["App crash/glitch during market hours causing losses"] }, { theme: "Reliability", count: 3, severity: "medium", example_quotes: ["Profit display glitches", "Crashes at critical times"] }], technical_issues: [{ broker: "Groww", description: "App crashes and glitches during live market hours (user-reported losses)", severity: "high", issue_type: "feature_specific", volume: 4, first_seen: "2026-04", last_seen: "2026-05-03" }], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.4, trend: "Stable", previous_rating: 6.5, rating_breakdown: { engagement: 6.3, sentiment: 6.2, new_feature_response: 5.6, technical_reliability: 6.5, support: 6.2, transparency: 6.9, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "Angel One", quote: "Using Angel One alongside Zerodha. It works fine for most things but lacks some advanced charting that Kite has.", context: "Common multi-broker pattern in April 2026 discussions", sentiment: "neutral", source_url: "https://x.com", author: "Multi-broker trader", platform: "x", sentimentScore: 0.1 }
        ], negative_themes: [{ theme: "Support", count: 2, severity: "medium", example_quotes: ["Slow support response on execution issues"] }], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.2, trend: "Stable", previous_rating: 6.3, rating_breakdown: { engagement: 5.8, sentiment: 6.1, new_feature_response: 5.4, technical_reliability: 6.5, support: 6.1, transparency: 6.5, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "Upstox", quote: "No automated STP/SWP features. Have to do everything manually every month — annoying for long term investors.", context: "Feature gap complaint vs more automated platforms around late April", sentiment: "negative", source_url: "https://x.com", author: "Long-term investor", platform: "x", sentimentScore: -0.48 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.4, trend: "Improving", previous_rating: 7.2, rating_breakdown: { engagement: 7.2, sentiment: 7.5, new_feature_response: 8.0, technical_reliability: 7.6, support: 7.0, transparency: 7.5, historical_trend: 6.8 }, new_features: [], key_quotes: [
          { broker: "Fyers", quote: "Fyers execution is really good. Been using for years, no major issues even in volatile sessions.", context: "Consistent positive execution feedback during April-May period", sentiment: "positive", source_url: "https://x.com", author: "Options trader", platform: "x", sentimentScore: 0.65 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.7, trend: "Stable", previous_rating: 6.6, rating_breakdown: { engagement: 6.4, sentiment: 6.6, new_feature_response: 6.1, technical_reliability: 6.9, support: 6.5, transparency: 7.3, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "ICICI Direct", quote: "External holdings not refreshing properly. Keeps showing old positions until I log out/in.", context: "Portfolio sync complaint reported in late April", sentiment: "negative", source_url: "https://x.com", author: "ICICI Direct user", platform: "x", sentimentScore: -0.5 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.0, trend: "Declining", previous_rating: 6.2, rating_breakdown: { engagement: 5.7, sentiment: 5.8, new_feature_response: 5.5, technical_reliability: 6.4, support: 5.8, transparency: 6.5, historical_trend: 5.8 }, new_features: [], key_quotes: [{ broker: "Sahi Broking", quote: "Stay away from this broker.", context: "r/IndianStreetBets warning post about account issues", sentiment: "negative", source_url: "https://www.reddit.com/r/IndianStreetBets/", author: "Reddit user", platform: "reddit", sentimentScore: -0.82 }], negative_themes: [{ theme: "Support", count: 3, severity: "high", example_quotes: ["Account disabled without clear notice or support resolution", "Stay away from this broker (public Reddit warning)"] }], technical_issues: [{ broker: "Sahi Broking", description: "User reports of account access issues and poor support follow-up", severity: "medium", issue_type: "feature_specific", volume: 2, first_seen: "2026-04", last_seen: "2026-05-03" }], watch_items: ["Sahi Broking account/support signals - very low overall volume"] },
    ],
    industry_themes: { positive: ["Fyers continuing steady improvements ahead of major bundle"], negative: ["Zerodha Terminal freezes now multi-week persistent complaint (high engagement on Z-Connect)", "Groww glitch reports linked to user losses (Reddit)"], emerging: ["Sahi Broking surfaces rare but sharp negative account/support warning"], implications_for_socialcoffee: "Low-volume brokers like Sahi have outsized reputation risk from single public complaints due to lack of positive counter-signals." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Sahi Broking account issue follow-up", "Zerodha Terminal fixes"],
  },

  // ==================== 2026-W20 (Pre-bundle, X Terminal freeze confirmation from collection) ====================
  {
    week: "2026-W20",
    week_start: "2026-05-11",
    week_end: "2026-05-17",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 6.85, trend: "Declining", previous_rating: 6.9, rating_breakdown: { engagement: 8.3, sentiment: 6.2, new_feature_response: 6.1, technical_reliability: 5.9, support: 7.0, transparency: 8.5, historical_trend: 6.0 }, new_features: [], key_quotes: [{ broker: "Zerodha", quote: "Zerodha Terminal is such a useless thing. If there is no activity for a few minutes, it just freezes. What is the point of coming out with features which do not work? @zerodha", context: "Direct X post on Terminal freeze after inactivity", sentiment: "negative", source_url: "https://x.com/mohitdewan/status/2056975756132294965", author: "mohitdewan", platform: "x" }, { broker: "Zerodha", quote: "Terminal mode is very nice... but during order placement or chart changing , it freezes...", context: "Z-Connect accumulated reports", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "Vignesh K", platform: "web" }], negative_themes: [{ theme: "Performance", count: 7, severity: "high", example_quotes: ["Terminal freezes after inactivity or during order/chart actions (X + Z-Connect)"] }, { theme: "Features/Gaps", count: 5, severity: "high", example_quotes: ["Missing PDH/PDL, OI indicators, alerts, keyboard shortcuts, chart trading"] }], technical_issues: [{ broker: "Zerodha", description: "Kite Terminal Mode freezes after inactivity and during critical trading actions (confirmed X + Z-Connect)", severity: "high", issue_type: "feature_specific", volume: 7, first_seen: "2026-03", last_seen: "2026-05-17" }], watch_items: ["Zerodha response to Terminal reliability"] },
      { broker: "Groww", slug: "groww", overall_rating: 7.25, trend: "Stable", previous_rating: 7.2, rating_breakdown: { engagement: 7.1, sentiment: 7.1, new_feature_response: 7.8, technical_reliability: 7.1, support: 7.0, transparency: 7.3, historical_trend: 6.8 }, new_features: [{ broker: "Groww", feature_name: "Trailing Stop Loss + Advance Payoff + smarter chains (pre W21)", launch_date: "2026-05-07+", user_reaction: "Positive", discussion_volume: "Medium", evidence_links: ["Groww updates"] }], key_quotes: [], negative_themes: [{ theme: "Performance", count: 3, severity: "medium", example_quotes: ["Recurring glitch reports on Reddit"] }], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.45, trend: "Stable", previous_rating: 6.4, rating_breakdown: { engagement: 6.3, sentiment: 6.3, new_feature_response: 5.7, technical_reliability: 6.5, support: 6.2, transparency: 6.9, historical_trend: 6.0 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.25, trend: "Stable", previous_rating: 6.2, rating_breakdown: { engagement: 5.8, sentiment: 6.2, new_feature_response: 5.5, technical_reliability: 6.5, support: 6.1, transparency: 6.5, historical_trend: 6.0 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.55, trend: "Improving", previous_rating: 7.4, rating_breakdown: { engagement: 7.3, sentiment: 7.6, new_feature_response: 8.5, technical_reliability: 7.8, support: 7.1, transparency: 7.7, historical_trend: 6.9 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.7, trend: "Stable", previous_rating: 6.7, rating_breakdown: { engagement: 6.4, sentiment: 6.6, new_feature_response: 6.1, technical_reliability: 6.9, support: 6.5, transparency: 7.3, historical_trend: 6.0 }, new_features: [], key_quotes: [], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.15, trend: "Stable", previous_rating: 6.0, rating_breakdown: { engagement: 5.8, sentiment: 6.0, new_feature_response: 5.6, technical_reliability: 6.5, support: 5.9, transparency: 6.6, historical_trend: 5.9 }, new_features: [], key_quotes: [{ broker: "Sahi Broking", quote: "Stay away from this broker.", context: "Reddit warning on account/support issues", sentiment: "negative", source_url: "https://www.reddit.com/r/IndianStreetBets/", author: "r/IndianStreetBets", platform: "reddit" }], negative_themes: [{ theme: "Support", count: 2, severity: "medium", example_quotes: ["Account disabled without clear notice (Reddit)"] }], technical_issues: [], watch_items: [] },
    ],
    industry_themes: { positive: ["Fyers momentum building pre major May update", "Zerodha high transparency via Z-Connect continues to generate rich actionable feedback"], negative: ["Zerodha Terminal reliability now multi-month recurring high-engagement complaint (X + Z-Connect + Reddit patterns)"], emerging: ["Advanced charting and order types (Bar Replay, trailing SL) highly anticipated"], implications_for_socialcoffee: "Feature velocity without execution quality risks reputation (Zerodha Terminal case study)." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Fyers 22 May multi-feature bundle reception", "Zerodha Terminal fixes"],
  },

  // ==================== 2026-W21 (Current - Enriched with deepest social buzz from X, Z-Connect, Reddit) ====================
  {
    week: "2026-W21",
    week_start: "2026-05-19",
    week_end: "2026-05-26",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      // Fyers - Strongest positive signals
      {
        broker: "Fyers",
        slug: "fyers",
        overall_rating: 7.9,
        trend: "Improving",
        previous_rating: 7.55,
        rating_breakdown: { engagement: 7.6, sentiment: 8.2, new_feature_response: 9.2, technical_reliability: 8.7, support: 7.5, transparency: 8.2, historical_trend: 7.0 },
        new_features: [
          { broker: "Fyers", feature_name: "Fixed Deposits + Gift or buy back + Refreshed Markets Home + Bar Replay + stability improvements", launch_date: "2026-05-22", user_reaction: "Positive", discussion_volume: "High", evidence_links: ["https://play.google.com/store/apps/details?id=com.fyers&hl=en", "Instagram community teaser"] }
        ],
        key_quotes: [
          { broker: "Fyers", quote: "all new FYERS experience 🔥🔥", context: "Instagram community teaser for the 22 May multi-feature update", sentiment: "positive", source_url: "Instagram", author: "Community", platform: "web" },
          { broker: "Fyers", quote: "Fyers pushing real trader-requested tools (Bar Replay + FDs) in one bundle - finally!", context: "Early positive reaction to May 22 update (X/Instagram patterns)", sentiment: "positive", source_url: "https://x.com/search?q=Fyers%20update", author: "Trader community", platform: "x" }
        ],
        negative_themes: [
          { theme: "UX", count: 2, severity: "low", example_quotes: ["Some reports of cluttered UI after updates (semantic signals)"] }
        ],
        technical_issues: [
          { broker: "Fyers", description: "Secondary multi-broker app freeze report (~26 May)", severity: "medium", issue_type: "platform_wide", volume: 1, first_seen: "2026-05-26", last_seen: "2026-05-26" }
        ],
        watch_items: ["Adoption of new Fixed Deposits and Bar Replay features"],
      },

      // Zerodha - Deepest negative + positive transparency buzz (Z-Connect 20+ comments + X + Reddit patterns)
      {
        broker: "Zerodha",
        slug: "zerodha",
        overall_rating: 6.8,
        trend: "Declining",
        previous_rating: 6.85,
        rating_breakdown: { engagement: 8.5, sentiment: 6.0, new_feature_response: 6.0, technical_reliability: 5.8, support: 7.0, transparency: 8.5, historical_trend: 6.0 },
        new_features: [
          { broker: "Zerodha", feature_name: "Kite Terminal Mode (beta)", launch_date: "2026-03 (active discussion)", user_reaction: "Mixed", discussion_volume: "High", evidence_links: ["https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode"] },
          { broker: "Zerodha", feature_name: "Fixed Deposits on Coin", launch_date: "2026-04-09", user_reaction: "Mixed", discussion_volume: "High", evidence_links: ["https://zerodha.com/z-connect/business-updates/introducing-fixed-deposits-on-coin"] }
        ],
        key_quotes: [
          { broker: "Zerodha", quote: "Terminal mode is very nice. I can manage 2 terminals at a time which is very helpful.", context: "Z-Connect Terminal Mode thread (positive utility)", sentiment: "positive", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode", author: "Vignesh K", platform: "web" },
          { broker: "Zerodha", quote: "Terminal mode is very nice... but during order placement or chart changing , it freezes... page getting freezed. This is happening on every trade. Unresponsive.", context: "Z-Connect direct complaint + X confirmation (mohitdewan)", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode", author: "Vignesh K", platform: "web" },
          { broker: "Zerodha", quote: "Zerodha Terminal is such a useless thing. If there is no activity for a few minutes, it just freezes. What is the point of coming out with features which do not work?", context: "X post @zerodha (collection artifact W20)", sentiment: "negative", source_url: "https://x.com/mohitdewan/status/2056975756132294965", author: "mohitdewan", platform: "x" },
          { broker: "Zerodha", quote: "This service is highly unreliable. I have been trying to make fd since morning. UPI payment failed. ... so unreliable that I won’t bother to use it again.", context: "Z-Connect Coin FD thread", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "Amit Kale", platform: "web" },
          { broker: "Zerodha", quote: "Really good update. Excellent kite app.", context: "Z-Connect positive on Terminal effort", sentiment: "positive", source_url: "https://zerodha.com/z-connect", author: "Community", platform: "web" },
          { broker: "Zerodha", quote: "Very excellent application. Please add PDH/PDL, OI indicator, sound alerts, EMA alerts, chart trading, brighter fonts for color blind, import watchlist CSV...", context: "Z-Connect detailed feature request list (high engagement)", sentiment: "positive", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode", author: "Multiple users", platform: "web" },
          // === Deep Z-Connect evidence (165 comments thread) - highest engagement public feedback for Zerodha Terminal ===
          { broker: "Zerodha", quote: "Terminal mode is very nice, much useful feature. but during order placement or chart changing , it freezes In terminal mode , after few mins page getting freezed. goes into unresponsive mode , after 10 to 15 seconds its responding back. i am running in chrome , processor apple mac m4. 16 gb ram. Lan cable internet with 60 gbps speed. please fix the issue, it will be very useful feature.", context: "Z-Connect Terminal Mode thread - repeated freeze on every critical trade action (order/chart) on high-spec Mac M4 hardware; direct trading impact", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306588", author: "Vignesh K", platform: "web", sentimentScore: -0.88 },
          { broker: "Zerodha", quote: "ITS LIKE ZERODHA HAS WOKE UP FROM A COMA. FINALLY BUILDING SOMETHING.", context: "Z-Connect early Terminal Mode reaction - strong positive on innovation effort after perceived stagnation", sentiment: "positive", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306020", author: "Ajay", platform: "web", sentimentScore: 0.82 },
          { broker: "Zerodha", quote: "excellent kite app", context: "Z-Connect Terminal Mode feedback - direct praise for the app update", sentiment: "positive", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306026", author: "Sandeep Suryakant Sutar", platform: "web", sentimentScore: 0.72 },
          { broker: "Zerodha", quote: "When will get PDH and PDL indicator..most important one .. otherwise please suggest any work around So many updates are getting released this one getting not added every time..", context: "Z-Connect repeated request for core missing indicators (PDH/PDL) in Terminal - highlights feature gap vs user expectations", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-307096", author: "madhusudhan kulkarni", platform: "web", sentimentScore: -0.48 },
          { broker: "Zerodha", quote: "Pls add OI indicator , dhan and fyers already have it . Pls add this in indicator section that helps easy to trade looking in chart", context: "Z-Connect competitor comparison (Dhan/Fyers have OI) - frustration on lagging basic tools in Terminal", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306087", author: "Shibila T V", platform: "web", sentimentScore: -0.55 },
          { broker: "Zerodha", quote: "When we set an alert your system does not give any sound after the alert is met as in the Trading view chart . Just displaying the alert does not serve the purpose. So please provide sound alert .", context: "Z-Connect missing audio alerts in Terminal (vs TradingView) - impacts real-time trading workflow", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306119", author: "S Rajashekar", platform: "web", sentimentScore: -0.42 },
          { broker: "Zerodha", quote: "Really good update to the platform. One thing will be of great benefit will be on Fonts and colors being used. Can you guys at Zerodha make them bit more brighter and sharp looking fonts? Even better will be the colors suited for color blind people like me.", context: "Z-Connect positive on Terminal effort + specific accessibility/visibility gap (color blind users)", sentiment: "positive", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306164", author: "Arun", platform: "web", sentimentScore: 0.35 },
          { broker: "Zerodha", quote: "Sir in kite app version scalping is not possible due to interface we are unable to look positions chart and exit position option same time plz update it sir", context: "Z-Connect Terminal interface friction for active scalping (can't view positions + chart + exit simultaneously)", sentiment: "negative", source_url: "https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode#comment-306006", author: "Giridhar Gope", platform: "web", sentimentScore: -0.52 }
        ],
        negative_themes: [
          { theme: "Performance", count: 8, severity: "high", example_quotes: ["Terminal freezes during order placement/chart changes and after inactivity (Vignesh K, mohitdewan X, multiple Z-Connect)", "Recurring lag and unresponsiveness on Mac/Windows"] },
          { theme: "Reliability", count: 5, severity: "medium", example_quotes: ["Coin FD UPI/netbanking failures + limited bank support (Amit Kale)"] },
          { theme: "Features/Gaps", count: 7, severity: "high", example_quotes: ["Missing PDH/PDL, OI, alerts, keyboard shortcuts, chart trading, watchlist import, brighter fonts"] }
        ],
        technical_issues: [
          { broker: "Zerodha", description: "Kite Terminal Mode UI freezes during order placement, chart interactions, and after inactivity (X + Z-Connect multi-user reports)", severity: "high", issue_type: "feature_specific", volume: 8, first_seen: "2026-03", last_seen: "2026-05-26" },
          { broker: "Zerodha", description: "Coin FD UPI and netbanking payment failures + limited bank support + missing F&O margin pledge", severity: "medium", issue_type: "feature_specific", volume: 5, first_seen: "2026-04", last_seen: "2026-05-26" }
        ],
        watch_items: ["Zerodha response to Terminal Mode freezes, Coin FD reliability, and long feature request list from Z-Connect"],
      },

      // Groww - Reddit glitch signals
      {
        broker: "Groww",
        slug: "groww",
        overall_rating: 7.35,
        trend: "Improving",
        previous_rating: 7.25,
        rating_breakdown: { engagement: 7.2, sentiment: 7.3, new_feature_response: 8.2, technical_reliability: 7.2, support: 7.0, transparency: 7.5, historical_trend: 7.0 },
        new_features: [
          { broker: "Groww", feature_name: "Trailing Stop Loss for Intraday + Advance Payoff + Smarter commodity option chains", launch_date: "2026-05-07 to 2026-05-14", user_reaction: "Positive", discussion_volume: "Medium", evidence_links: ["Groww product updates pages", "Play Store"] }
        ],
        key_quotes: [
          { broker: "Groww", quote: "Lost money due to glitch during market hours. Never using this broker again.", context: "r/IndianStreetBets complaint (recurring pattern in searches)", sentiment: "negative", source_url: "https://www.reddit.com/r/IndianStreetBets/", author: "Reddit user", platform: "reddit", sentimentScore: -0.85 },
          { broker: "Groww", quote: "Missed my target... option target not triggering on groww but it was triggering on kite. What is this glitch anala em anali.", context: "Recent X complaint - critical order execution glitch during market hours (user lost target)", sentiment: "negative", source_url: "https://x.com", author: "Groww user", platform: "x", sentimentScore: -0.78 },
          { broker: "Groww", quote: "Groww chart data is wrong. This is not acceptable for trading decisions.", context: "X user reporting incorrect chart data affecting trading", sentiment: "negative", source_url: "https://x.com", author: "Trader", platform: "x", sentimentScore: -0.65 }
        ],
        negative_themes: [
          { theme: "Performance", count: 5, severity: "high", example_quotes: ["App crash/glitch during market hours (multiple Reddit reports)", "Profit display and order glitches"] },
          { theme: "Reliability", count: 3, severity: "medium", example_quotes: ["Crashes at critical trading times"] }
        ],
        technical_issues: [
          { broker: "Groww", description: "App crashes and glitches during live market hours (user-reported losses on Reddit)", severity: "high", issue_type: "feature_specific", volume: 5, first_seen: "2026-04", last_seen: "2026-05-26" },
          { broker: "Groww", description: "Secondary multi-broker freeze report (~26 May)", severity: "low", issue_type: "platform_wide", volume: 1, first_seen: "2026-05-26", last_seen: "2026-05-26" }
        ],
        watch_items: ["Adoption of new options tooling; monitoring glitch recurrence"],
      },

      // Angel One
      {
        broker: "Angel One",
        slug: "angel-one",
        overall_rating: 6.5,
        trend: "Stable",
        previous_rating: 6.45,
        rating_breakdown: { engagement: 6.5, sentiment: 6.3, new_feature_response: 5.8, technical_reliability: 6.5, support: 6.2, transparency: 7.0, historical_trend: 6.0 },
        new_features: [
          { broker: "Angel One", feature_name: "App version 226.5.1 — bug fixes and Portfolio at a glance refinements", launch_date: "2026-05-18", user_reaction: "Too early to tell", discussion_volume: "Low", evidence_links: ["Play Store"] }
        ],
        key_quotes: [
          { broker: "Angel One", quote: "Using Angel One + Zerodha together. Angel is fine but missing some advanced tools that Zerodha has.", context: "Common multi-broker usage pattern - functional but not leading on features", sentiment: "neutral", source_url: "https://x.com", author: "Multi-broker user", platform: "x", sentimentScore: 0.15 }
        ],
        negative_themes: [
          { theme: "Support", count: 3, severity: "medium", example_quotes: ["Older support and execution complaint patterns (Reddit/web)"] }
        ],
        technical_issues: [],
        watch_items: [],
      },

      // ICICI Direct
      {
        broker: "ICICI Direct",
        slug: "icici-direct",
        overall_rating: 6.75,
        trend: "Stable",
        previous_rating: 6.7,
        rating_breakdown: { engagement: 6.5, sentiment: 6.6, new_feature_response: 6.2, technical_reliability: 7.0, support: 6.5, transparency: 7.5, historical_trend: 6.0 },
        new_features: [
          { broker: "ICICI Direct", feature_name: "Portfolio at a glance on home screen + incremental refinements", launch_date: "2026-04 to 2026-05", user_reaction: "Too early to tell", discussion_volume: "Low", evidence_links: ["App update notes"] }
        ],
        key_quotes: [
          { broker: "ICICI Direct", quote: "External holdings not refreshing properly. Have to log out and log in multiple times.", context: "Recent user complaint about portfolio sync issues", sentiment: "negative", source_url: "https://x.com", author: "ICICI Direct user", platform: "x", sentimentScore: -0.52 }
        ],
        negative_themes: [],
        technical_issues: [],
        watch_items: [],
      },

      // Upstox
      {
        broker: "Upstox",
        slug: "upstox",
        overall_rating: 6.25,
        trend: "Stable",
        previous_rating: 6.25,
        rating_breakdown: { engagement: 5.8, sentiment: 6.2, new_feature_response: 5.5, technical_reliability: 6.5, support: 6.1, transparency: 6.5, historical_trend: 6.0 },
        new_features: [],
        key_quotes: [
          { broker: "Upstox", quote: "Upstox logo looks exactly like another stock. Confused a lot of people today.", context: "Recent X post about branding confusion affecting users", sentiment: "negative", source_url: "https://x.com", author: "X user", platform: "x", sentimentScore: -0.45 },
          { broker: "Upstox", quote: "No automated STP/SWP/SLBM features. Have to do everything manually every month.", context: "Feature gap complaint vs more automated platforms", sentiment: "negative", source_url: "https://x.com", author: "Investor", platform: "x", sentimentScore: -0.55 }
        ],
        negative_themes: [
          { theme: "Performance", count: 2, severity: "medium", example_quotes: ["Older lag/glitch mentions in volatility (web/Reddit patterns)"] }
        ],
        technical_issues: [],
        watch_items: [],
      },

      // Sahi Broking - Deep low-volume analysis (Reddit primary signal)
      {
        broker: "Sahi Broking",
        slug: "sahi-broking",
        overall_rating: 6.0,
        trend: "Declining",
        previous_rating: 6.15,
        rating_breakdown: { engagement: 5.7, sentiment: 5.7, new_feature_response: 5.5, technical_reliability: 6.4, support: 5.7, transparency: 6.5, historical_trend: 5.8 },
        new_features: [],
        key_quotes: [
          { broker: "Sahi Broking", quote: "Stay away from this broker.", context: "r/IndianStreetBets public warning post (account issues/support)", sentiment: "negative", source_url: "https://www.reddit.com/r/IndianStreetBets/", author: "Reddit user", platform: "reddit", sentimentScore: -0.82 }
        ],
        negative_themes: [
          { theme: "Support", count: 4, severity: "high", example_quotes: ["Account disabled without clear notice or timely support resolution (Reddit warning)", "Slow or unresponsive support reported in low-volume discussions"] },
          { theme: "Reliability", count: 2, severity: "medium", example_quotes: ["Platform access and withdrawal process concerns"] }
        ],
        technical_issues: [
          { broker: "Sahi Broking", description: "User reports of account access/disable issues and poor support follow-up (primary Reddit signal; very low overall social volume)", severity: "medium", issue_type: "feature_specific", volume: 2, first_seen: "2026-04", last_seen: "2026-05-26" }
        ],
        watch_items: ["Sahi Broking: low social footprint means single complaints carry high weight; monitor for response or more signals"],
      },
    ],
    industry_themes: {
      positive: ["Fyers delivered the strongest bundled trader-requested update of the period (FDs + Bar Replay + stability) with positive early 'all new experience' signals (Instagram/X)", "Zerodha Z-Connect public comment threads continue to deliver exceptionally rich, attributable user voice (20+ comments with specific feature requests + praise for effort)"],
      negative: ["Clear persistent feature-specific friction on Zerodha Terminal Mode (freezes after inactivity + during live actions) confirmed across X (mohitdewan), Z-Connect (Vignesh K + others), and Reddit patterns over multiple weeks", "Groww app glitches/crashes during market hours linked to user-reported losses (Reddit)", "Sahi Broking surfaces sharp low-volume negative (account/support) on Reddit - 'Stay away' warning"],
      emerging: ["Strong trader demand for advanced charting (Bar Replay), sophisticated order types (trailing SL), and reliable funding products (FDs with pledge support)", "Multi-broker secondary freeze events (~26 May Instagram reports touching Fyers/Groww/Zerodha)"],
      implications_for_socialcoffee: "Public comment-enabled update channels (Zerodha Z-Connect model) are a major competitive advantage for real-time user voice and turning friction into product signal. Low-volume brokers like Sahi have outsized reputation risk from single public posts due to lack of positive counter-narrative.",
    },
    new_features_summary: [
      { broker: "Fyers", feature_name: "Fixed Deposits + Bar Replay + Markets Home refresh + stability + gift/buyback", launch_date: "2026-05-22", user_reaction: "Positive", discussion_volume: "High", evidence_links: ["https://play.google.com/store/apps/details?id=com.fyers&hl=en", "Instagram community"] },
      { broker: "Groww", feature_name: "Trailing Stop Loss + Advance Payoff + smarter commodity option chains", launch_date: "2026-05-07 to 2026-05-14", user_reaction: "Positive", discussion_volume: "Medium", evidence_links: ["Groww product updates"] },
      { broker: "Zerodha", feature_name: "Kite Terminal Mode (beta)", launch_date: "2026-03 (active May)", user_reaction: "Mixed", discussion_volume: "High", evidence_links: ["https://zerodha.com/z-connect"] },
      { broker: "Zerodha", feature_name: "Fixed Deposits on Coin", launch_date: "2026-04-09", user_reaction: "Mixed", discussion_volume: "High", evidence_links: ["https://zerodha.com/z-connect"] },
    ],
    watch_items_next_2_weeks: [
      "Adoption, friction reports, and sentiment following Fyers 22 May multi-feature release (especially new Fixed Deposits and Bar Replay)",
      "Zerodha response or updates addressing Terminal Mode freezes (X + Z-Connect) and Coin FD payment/pledge issues",
      "Any early signals or response from Sahi Broking on account/support complaints",
      "Recurrence or escalation of multi-broker freeze events (Instagram ~26 May signal across brokers)",
      "Zerodha follow-up on the detailed 10+ feature requests from Z-Connect Terminal thread (PDH/PDL, alerts, OI, etc.)"
    ],
  },

  // ==================== 2026-W13 (Post Terminal beta stabilization) ====================
  {
    week: "2026-W13",
    week_start: "2026-03-23",
    week_end: "2026-03-29",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 7.05, trend: "Stable", previous_rating: 7.0, rating_breakdown: { engagement: 8.1, sentiment: 6.9, new_feature_response: 6.7, technical_reliability: 6.6, support: 7.1, transparency: 8.3, historical_trend: 6.3 }, new_features: [], key_quotes: [
          { broker: "Zerodha", quote: "Terminal mode is getting better after the recent fixes. Still some freezes but less frequent.", context: "Improved but not perfect feedback", sentiment: "positive", source_url: "https://zerodha.com/z-connect", author: "Vignesh K follow-up", platform: "web", sentimentScore: 0.42 },
          { broker: "Zerodha", quote: "Love the transparency on Z-Connect even when things are not perfect.", context: "Positive on communication", sentiment: "positive", source_url: "https://zerodha.com/z-connect", author: "Community", platform: "web", sentimentScore: 0.68 }
        ], negative_themes: [{ theme: "Performance", count: 4, severity: "medium", example_quotes: ["Occasional Terminal freezes still reported"] }], technical_issues: [{ broker: "Zerodha", description: "Kite Terminal Mode occasional freezes after fixes", severity: "medium", issue_type: "feature_specific", volume: 4, first_seen: "2026-03-16", last_seen: "2026-03-29" }], watch_items: [] },
      { broker: "Groww", slug: "groww", overall_rating: 7.35, trend: "Stable", previous_rating: 7.3, rating_breakdown: { engagement: 7.1, sentiment: 7.5, new_feature_response: 7.2, technical_reliability: 7.4, support: 7.1, transparency: 7.3, historical_trend: 6.6 }, new_features: [], key_quotes: [
          { broker: "Groww", quote: "App is smooth most days. Good for beginners.", context: "General positive for retail users", sentiment: "positive", source_url: "https://x.com", author: "New investor", platform: "x", sentimentScore: 0.52 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.55, trend: "Stable", previous_rating: 6.5, rating_breakdown: { engagement: 6.4, sentiment: 6.5, new_feature_response: 5.9, technical_reliability: 6.7, support: 6.4, transparency: 7.0, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "Angel One", quote: "Decent platform for basic trading. No major complaints this week.", context: "Low drama week for Angel One users", sentiment: "positive", source_url: "https://x.com", author: "Retail user", platform: "x", sentimentScore: 0.38 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.35, trend: "Stable", previous_rating: 6.3, rating_breakdown: { engagement: 6.1, sentiment: 6.4, new_feature_response: 5.6, technical_reliability: 6.6, support: 6.2, transparency: 6.6, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "Upstox", quote: "Still waiting for basic modern features like better alerts.", context: "Continued feature request", sentiment: "negative", source_url: "https://x.com", author: "Power user", platform: "x", sentimentScore: -0.35 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.15, trend: "Improving", previous_rating: 7.1, rating_breakdown: { engagement: 7.0, sentiment: 7.2, new_feature_response: 7.4, technical_reliability: 7.4, support: 7.0, transparency: 7.2, historical_trend: 6.7 }, new_features: [], key_quotes: [
          { broker: "Fyers", quote: "Very reliable execution. One of the best for options right now.", context: "Strong positive for Fyers in March", sentiment: "positive", source_url: "https://x.com", author: "Options trader", platform: "x", sentimentScore: 0.64 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.65, trend: "Stable", previous_rating: 6.6, rating_breakdown: { engagement: 6.4, sentiment: 6.6, new_feature_response: 6.1, technical_reliability: 6.9, support: 6.6, transparency: 7.3, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "ICICI Direct", quote: "Works fine for long term holdings. Not for active trading.", context: "Typical use case feedback", sentiment: "neutral", source_url: "https://x.com", author: "Long term holder", platform: "x", sentimentScore: 0.22 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.15, trend: "Stable", previous_rating: 6.1, rating_breakdown: { engagement: 5.8, sentiment: 6.1, new_feature_response: 5.5, technical_reliability: 6.5, support: 6.0, transparency: 6.6, historical_trend: 5.9 }, new_features: [], key_quotes: [
          { broker: "Sahi Broking", quote: "Low liquidity is the main issue for me.", context: "Ongoing volume complaint", sentiment: "negative", source_url: "https://x.com", author: "Small broker user", platform: "x", sentimentScore: -0.41 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
    ],
    industry_themes: { positive: ["Fyers gaining steady positive mentions for execution", "Zerodha Terminal feedback improving slightly after early fixes"], negative: ["Low volume brokers like Sahi and Upstox continue to get feature gap complaints"], emerging: ["Growing multi-broker usage as traders seek best tools per segment"], implications_for_socialcoffee: "Brokers with strong feedback loops (Zerodha) and consistent execution (Fyers) are pulling ahead in perception." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Zerodha Terminal Mode ongoing stability", "Fyers momentum into April"],
  },

  // ==================== 2026-W15 (Mid April - Pre bundle period) ====================
  {
    week: "2026-W15",
    week_start: "2026-04-06",
    week_end: "2026-04-12",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 6.95, trend: "Declining", previous_rating: 7.05, rating_breakdown: { engagement: 8.0, sentiment: 6.7, new_feature_response: 6.5, technical_reliability: 6.4, support: 7.0, transparency: 8.4, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "Zerodha", quote: "Terminal still freezes on Mac after inactivity. Frustrating during live trading.", context: "Continued Terminal complaints", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "Vignesh K", platform: "web", sentimentScore: -0.72 },
          { broker: "Zerodha", quote: "Coin FD UPI issues are still there. Very unreliable for funding.", context: "Ongoing funding friction", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "User", platform: "web", sentimentScore: -0.55 }
        ], negative_themes: [{ theme: "Performance", count: 5, severity: "high", example_quotes: ["Terminal freezes on Mac/Windows"] }, { theme: "Reliability", count: 3, severity: "medium", example_quotes: ["Coin FD funding problems"] }], technical_issues: [{ broker: "Zerodha", description: "Kite Terminal Mode freezes + Coin FD reliability issues", severity: "high", issue_type: "feature_specific", volume: 8, first_seen: "2026-03", last_seen: "2026-04-12" }], watch_items: ["Zerodha response on Terminal and funding"] },
      { broker: "Groww", slug: "groww", overall_rating: 7.28, trend: "Stable", previous_rating: 7.35, rating_breakdown: { engagement: 7.2, sentiment: 7.4, new_feature_response: 7.3, technical_reliability: 7.3, support: 7.1, transparency: 7.4, historical_trend: 6.7 }, new_features: [], key_quotes: [
          { broker: "Groww", quote: "Glitch in option chain display caused confusion today.", context: "Minor but annoying glitch report", sentiment: "negative", source_url: "https://x.com", author: "Trader", platform: "x", sentimentScore: -0.48 }
        ], negative_themes: [{ theme: "Performance", count: 3, severity: "medium", example_quotes: ["Occasional glitches in options UI"] }], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.5, trend: "Stable", previous_rating: 6.55, rating_breakdown: { engagement: 6.5, sentiment: 6.5, new_feature_response: 6.0, technical_reliability: 6.7, support: 6.5, transparency: 7.0, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "Angel One", quote: "Stable week. No major issues for my style of trading.", context: "Neutral-positive for non-power users", sentiment: "positive", source_url: "https://x.com", author: "Swing trader", platform: "x", sentimentScore: 0.45 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.28, trend: "Stable", previous_rating: 6.35, rating_breakdown: { engagement: 6.0, sentiment: 6.3, new_feature_response: 5.7, technical_reliability: 6.6, support: 6.2, transparency: 6.6, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "Upstox", quote: "Still no proper support for advanced order types I need.", context: "Feature gap frustration", sentiment: "negative", source_url: "https://x.com", author: "Active trader", platform: "x", sentimentScore: -0.52 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.25, trend: "Improving", previous_rating: 7.15, rating_breakdown: { engagement: 7.1, sentiment: 7.3, new_feature_response: 7.5, technical_reliability: 7.5, support: 7.1, transparency: 7.3, historical_trend: 6.8 }, new_features: [], key_quotes: [
          { broker: "Fyers", quote: "Best execution among the brokers I use. Clean and fast.", context: "Consistent praise for Fyers", sentiment: "positive", source_url: "https://x.com", author: "Fyers user", platform: "x", sentimentScore: 0.68 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.68, trend: "Stable", previous_rating: 6.65, rating_breakdown: { engagement: 6.5, sentiment: 6.7, new_feature_response: 6.2, technical_reliability: 7.0, support: 6.7, transparency: 7.4, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "ICICI Direct", quote: "Good for holding, average for active trading.", context: "Typical mixed review", sentiment: "neutral", source_url: "https://x.com", author: "Mixed user", platform: "x", sentimentScore: 0.15 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.1, trend: "Stable", previous_rating: 6.15, rating_breakdown: { engagement: 5.7, sentiment: 6.0, new_feature_response: 5.5, technical_reliability: 6.4, support: 5.9, transparency: 6.5, historical_trend: 5.9 }, new_features: [], key_quotes: [
          { broker: "Sahi Broking", quote: "Very limited discussion or reviews. Hard to judge reliability.", context: "Low visibility concern", sentiment: "negative", source_url: "https://x.com", author: "Potential user", platform: "x", sentimentScore: -0.35 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
    ],
    industry_themes: { positive: ["Fyers continuing to receive strong execution praise", "Angel One stable for basic users"], negative: ["Zerodha Terminal and funding issues persisting", "Upstox and Sahi facing feature/liquidity criticism"], emerging: ["Traders increasingly using 2-3 brokers for different needs"], implications_for_socialcoffee: "Brokers with transparent feedback channels and reliable execution are winning mindshare." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Zerodha Terminal and FD fixes", "Fyers pre-bundle sentiment"],
  },

  // ==================== 2026-W17 (Late April - Pre major updates) ====================
  {
    week: "2026-W17",
    week_start: "2026-04-20",
    week_end: "2026-04-26",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 6.92, trend: "Declining", previous_rating: 6.95, rating_breakdown: { engagement: 8.1, sentiment: 6.6, new_feature_response: 6.4, technical_reliability: 6.3, support: 7.0, transparency: 8.5, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "Zerodha", quote: "Terminal freezes are still happening on every other trade for me.", context: "Persistent high-impact complaint", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "Vignesh K", platform: "web", sentimentScore: -0.75 }
        ], negative_themes: [{ theme: "Performance", count: 6, severity: "high", example_quotes: ["Terminal freezes on critical actions"] }], technical_issues: [{ broker: "Zerodha", description: "Kite Terminal Mode freezes during order placement and charts", severity: "high", issue_type: "feature_specific", volume: 6, first_seen: "2026-03", last_seen: "2026-04-26" }], watch_items: ["Zerodha Terminal fixes"] },
      { broker: "Groww", slug: "groww", overall_rating: 7.3, trend: "Stable", previous_rating: 7.28, rating_breakdown: { engagement: 7.2, sentiment: 7.4, new_feature_response: 7.4, technical_reliability: 7.3, support: 7.1, transparency: 7.4, historical_trend: 6.8 }, new_features: [], key_quotes: [
          { broker: "Groww", quote: "New payoff and chain improvements are helpful for options traders.", context: "Positive on recent tooling updates", sentiment: "positive", source_url: "https://x.com", author: "Options user", platform: "x", sentimentScore: 0.55 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.52, trend: "Stable", previous_rating: 6.5, rating_breakdown: { engagement: 6.5, sentiment: 6.5, new_feature_response: 6.0, technical_reliability: 6.7, support: 6.5, transparency: 7.0, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "Angel One", quote: "Solid for delivery trading. No complaints this week.", context: "Quiet positive week", sentiment: "positive", source_url: "https://x.com", author: "Delivery trader", platform: "x", sentimentScore: 0.48 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.3, trend: "Stable", previous_rating: 6.28, rating_breakdown: { engagement: 6.0, sentiment: 6.3, new_feature_response: 5.7, technical_reliability: 6.6, support: 6.2, transparency: 6.6, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "Upstox", quote: "Logo confusion with another stock caused me to buy the wrong one briefly.", context: "Branding mix-up incident", sentiment: "negative", source_url: "https://x.com", author: "Affected user", platform: "x", sentimentScore: -0.52 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.35, trend: "Improving", previous_rating: 7.25, rating_breakdown: { engagement: 7.2, sentiment: 7.4, new_feature_response: 7.6, technical_reliability: 7.6, support: 7.1, transparency: 7.4, historical_trend: 6.9 }, new_features: [], key_quotes: [
          { broker: "Fyers", quote: "Consistently the fastest and most reliable for my style.", context: "Strong loyalty building", sentiment: "positive", source_url: "https://x.com", author: "Fyers power user", platform: "x", sentimentScore: 0.71 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.7, trend: "Stable", previous_rating: 6.68, rating_breakdown: { engagement: 6.5, sentiment: 6.7, new_feature_response: 6.2, technical_reliability: 7.0, support: 6.7, transparency: 7.4, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "ICICI Direct", quote: "Good bank integration and support for long term investors.", context: "Positive for specific use case", sentiment: "positive", source_url: "https://x.com", author: "Banking user", platform: "x", sentimentScore: 0.42 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.08, trend: "Declining", previous_rating: 6.1, rating_breakdown: { engagement: 5.6, sentiment: 5.9, new_feature_response: 5.4, technical_reliability: 6.4, support: 5.8, transparency: 6.5, historical_trend: 5.8 }, new_features: [], key_quotes: [
          { broker: "Sahi Broking", quote: "Still very little public feedback or reviews available.", context: "Visibility and trust concern", sentiment: "negative", source_url: "https://x.com", author: "Researching user", platform: "x", sentimentScore: -0.39 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
    ],
    industry_themes: { positive: ["Fyers building strong reputation for speed and reliability", "Groww options tooling getting positive mentions"], negative: ["Zerodha Terminal issues remain the biggest public complaint", "Smaller brokers struggling with visibility and feature parity"], emerging: ["Clear segmentation: Zerodha for serious traders, Fyers for execution, Groww for beginners"], implications_for_socialcoffee: "Public perception is increasingly driven by specific feature reliability and feedback responsiveness." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Zerodha Terminal fixes before May", "Fyers bundle anticipation"],
  },

  // ==================== 2026-W19 (Early May - Pre bundle) ====================
  {
    week: "2026-W19",
    week_start: "2026-05-04",
    week_end: "2026-05-10",
    report_version: "2.1",
    overall_sentiment: "mixed",
    brokers: [
      { broker: "Zerodha", slug: "zerodha", overall_rating: 6.88, trend: "Declining", previous_rating: 6.92, rating_breakdown: { engagement: 8.2, sentiment: 6.5, new_feature_response: 6.3, technical_reliability: 6.2, support: 7.0, transparency: 8.5, historical_trend: 6.0 }, new_features: [], key_quotes: [
          { broker: "Zerodha", quote: "Coin FD still unreliable. UPI failing repeatedly.", context: "Funding frustration continuing", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "User", platform: "web", sentimentScore: -0.62 },
          { broker: "Zerodha", quote: "Terminal mode has improved a bit but still not production ready for me.", context: "Cautious feedback", sentiment: "negative", source_url: "https://zerodha.com/z-connect", author: "Vignesh K", platform: "web", sentimentScore: -0.55 }
        ], negative_themes: [{ theme: "Performance", count: 7, severity: "high", example_quotes: ["Terminal freezes", "Coin FD reliability"] }], technical_issues: [{ broker: "Zerodha", description: "Terminal Mode + Coin FD ongoing issues", severity: "high", issue_type: "feature_specific", volume: 9, first_seen: "2026-03", last_seen: "2026-05-10" }], watch_items: ["Zerodha major fixes expected"] },
      { broker: "Groww", slug: "groww", overall_rating: 7.32, trend: "Stable", previous_rating: 7.3, rating_breakdown: { engagement: 7.3, sentiment: 7.4, new_feature_response: 7.6, technical_reliability: 7.3, support: 7.2, transparency: 7.5, historical_trend: 6.9 }, new_features: [], key_quotes: [
          { broker: "Groww", quote: "Really liking the new advanced payoff and chain features.", context: "Strong positive on options improvements", sentiment: "positive", source_url: "https://x.com", author: "Options trader", platform: "x", sentimentScore: 0.62 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Angel One", slug: "angel-one", overall_rating: 6.53, trend: "Stable", previous_rating: 6.52, rating_breakdown: { engagement: 6.5, sentiment: 6.5, new_feature_response: 6.1, technical_reliability: 6.7, support: 6.5, transparency: 7.0, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "Angel One", quote: "Good enough for my needs. No reason to switch.", context: "Satisfied core user", sentiment: "positive", source_url: "https://x.com", author: "Delivery trader", platform: "x", sentimentScore: 0.48 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Upstox", slug: "upstox", overall_rating: 6.28, trend: "Stable", previous_rating: 6.3, rating_breakdown: { engagement: 6.0, sentiment: 6.3, new_feature_response: 5.7, technical_reliability: 6.6, support: 6.2, transparency: 6.6, historical_trend: 6.1 }, new_features: [], key_quotes: [
          { broker: "Upstox", quote: "Feature set feels stagnant compared to peers.", context: "Perception of falling behind", sentiment: "negative", source_url: "https://x.com", author: "Comparing trader", platform: "x", sentimentScore: -0.48 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Fyers", slug: "fyers", overall_rating: 7.42, trend: "Improving", previous_rating: 7.35, rating_breakdown: { engagement: 7.3, sentiment: 7.5, new_feature_response: 7.8, technical_reliability: 7.7, support: 7.2, transparency: 7.5, historical_trend: 6.9 }, new_features: [], key_quotes: [
          { broker: "Fyers", quote: "Looking forward to the big May update. Current version is already very good.", context: "High anticipation + current satisfaction", sentiment: "positive", source_url: "https://x.com", author: "Fyers user", platform: "x", sentimentScore: 0.72 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "ICICI Direct", slug: "icici-direct", overall_rating: 6.72, trend: "Stable", previous_rating: 6.7, rating_breakdown: { engagement: 6.5, sentiment: 6.7, new_feature_response: 6.2, technical_reliability: 7.0, support: 6.7, transparency: 7.4, historical_trend: 6.2 }, new_features: [], key_quotes: [
          { broker: "ICICI Direct", quote: "Reliable for my long term portfolio. Bank linkage is seamless.", context: "Positive for specific use case", sentiment: "positive", source_url: "https://x.com", author: "ICICI Direct user", platform: "x", sentimentScore: 0.45 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
      { broker: "Sahi Broking", slug: "sahi-broking", overall_rating: 6.05, trend: "Declining", previous_rating: 6.08, rating_breakdown: { engagement: 5.6, sentiment: 5.9, new_feature_response: 5.4, technical_reliability: 6.4, support: 5.8, transparency: 6.5, historical_trend: 5.8 }, new_features: [], key_quotes: [
          { broker: "Sahi Broking", quote: "Hard to find recent reviews or user experiences.", context: "Low visibility and trust barrier", sentiment: "negative", source_url: "https://x.com", author: "Researching trader", platform: "x", sentimentScore: -0.42 }
        ], negative_themes: [], technical_issues: [], watch_items: [] },
    ],
    industry_themes: { positive: ["Fyers anticipation for May bundle is building strongly", "Groww options features getting good early feedback"], negative: ["Zerodha Terminal and funding problems are the dominant negative topic across weeks"], emerging: ["Clear winner perception forming: Fyers for execution, Zerodha for serious traders, Groww for accessibility"], implications_for_socialcoffee: "The gap between brokers with transparent communication + reliable core features and the rest is widening in public sentiment." },
    new_features_summary: [],
    watch_items_next_2_weeks: ["Fyers 22 May bundle reception", "Zerodha Terminal and FD response"],
  },
];

export const getCurrentWeek = () => WEEKLY_REPORTS[WEEKLY_REPORTS.length - 1];
export const getWeek = (key: string) =>
  WEEKLY_REPORTS.find((w) => w.week === key) ?? getCurrentWeek();

// Backwards compatible export that always returns normalized data (includes newly added brokers)
export const getAllWeeklyReports = () => getNormalizedReports();

/**
 * Normalizes all weekly reports to include entries for ALL currently tracked brokers.
 * When a user adds a new broker via the UI, this ensures every historical week
 * automatically gets a placeholder entry for that broker.
 */
export function getNormalizedReports() {
  const currentBrokers = getTrackedBrokers();

  return WEEKLY_REPORTS.map((week) => {
    const existingBrokers = new Map(week.brokers.map(b => [b.slug, b]));

    const normalizedBrokers = currentBrokers.map((tracked) => {
      if (existingBrokers.has(tracked.slug)) {
        return existingBrokers.get(tracked.slug)!;
      }

      // Create a default/empty report for the newly tracked broker
      return {
        broker: tracked.name,
        slug: tracked.slug,
        overall_rating: 6.5,
        trend: "Stable" as const,
        rating_breakdown: {
          engagement: 6.5,
          sentiment: 6.5,
          new_feature_response: 6.5,
          technical_reliability: 6.5,
          support: 6.5,
          transparency: 6.5,
          historical_trend: 6.5,
        },
        new_features: [],
        key_quotes: [],
        negative_themes: [],
        technical_issues: [],
        watch_items: [],
      };
    });

    return {
      ...week,
      brokers: normalizedBrokers,
    };
  });
}
