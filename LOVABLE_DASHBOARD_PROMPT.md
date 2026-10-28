# Lovable Prompt: BrokerWeeklyIntel Dashboard UI

**Copy and paste the entire content below into Lovable to generate the complete professional dashboard.**

---

You are an expert Next.js 15 + TypeScript + Tailwind + shadcn/ui developer. Generate a **complete, production-ready, professional dashboard** for **BrokerWeeklyIntel** — a weekly competitor intelligence platform for Indian stock brokers.

## Project Context

**Product Name:** BrokerWeeklyIntel  
**Tagline:** Weekly Competitor Intelligence for India's Leading Stock Brokers

**Purpose:**  
Every Sunday, the platform delivers deep competitive intelligence on Zerodha, Groww, Angel One, Upstox, Fyers, ICICI Direct, 5Paisa, and Kotak Securities. It analyzes social media (X, Reddit), official blogs, app updates, and user sentiment to produce actionable ratings and insights.

**Data Model (use this structure for mock data and components):**

```ts
interface WeeklyReport {
  week: string;                    // e.g. "2026-W21"
  week_start: string;
  week_end: string;
  report_version: "2.1";
  
  overall_sentiment: "positive" | "mixed" | "negative";
  
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

interface BrokerReport {
  broker: string;                  // "Zerodha", "Groww", etc.
  overall_rating: number;          // 0-10
  trend: "Improving" | "Declining" | "Stable";
  previous_rating?: number;
  
  rating_breakdown: {
    engagement: number;            // 0-10
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

interface NewFeature {
  feature_name: string;
  launch_date: string;
  user_reaction: "Positive" | "Mixed" | "Negative" | "Too early to tell";
  discussion_volume: "High" | "Medium" | "Low";
  evidence_links: string[];
}

interface KeyQuote {
  quote: string;
  context: string;
  sentiment: "positive" | "negative" | "neutral";
  source_url: string;
  author?: string;
  platform: "x" | "reddit" | "web";
}

interface NegativeTheme {
  theme: "Performance" | "Support" | "Charges" | "Reliability" | "UX" | "Features/Gaps" | "Transparency" | "Other";
  count: number;
  severity: "critical" | "high" | "medium" | "low";
  example_quotes: string[];
}

interface TechnicalIssue {
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  issue_type: "feature_specific" | "platform_wide";
  volume: number;
  first_seen: string;
  last_seen: string;
}
```

## Tech Stack & Constraints

- Next.js 15 (App Router)
- TypeScript (strict)
- Tailwind CSS + shadcn/ui (use latest components: Card, Table, Badge, Tabs, Select, Calendar, Button, etc.)
- Charts: Use Recharts or Tremor (prefer Recharts for radar + line charts)
- Icons: Lucide-react
- Dark mode support (professional finance aesthetic)
- Fully responsive (desktop-first but mobile friendly)
- Use `date-fns` for date handling

**Design Language:**
- Clean, modern, trustworthy finance/tech aesthetic
- Heavy use of cards with subtle shadows
- Professional color palette: slate/zinc base + blue-600 accents + semantic colors for sentiment (emerald, amber, rose)
- Excellent typography and spacing
- Severity badges: Critical (rose), High (orange), Medium (amber), Low (slate)
- Trend indicators: ↑ Improving (emerald), ↓ Declining (rose), → Stable (slate)

## Overall Layout

**Sidebar (fixed, collapsible on mobile):**
- Logo: "BrokerWeeklyIntel" + small tagline
- Navigation:
  - Overview
  - Brokers (with sub-links or dropdown)
  - Trends & History
  - New Features
  - Technical Issues
  - Sentiment & Quotes
  - Data Sources
- Week selector at bottom of sidebar (or in header)

**Top Header:**
- Current week display (e.g. "Week of May 19 – 25, 2026")
- Week picker (shadcn Calendar or Select with recent weeks)
- Multi-select broker filter
- "Refresh Data" button
- "Export PDF" + "Export Markdown" buttons
- User avatar / settings (placeholder)

**Main Content Area:**
Use tabs or clear sectioning with good visual hierarchy.

## Required Screens / Sections (Generate All)

### 1. Overview Dashboard (default landing page)

- **Top Summary Row (4-5 metric cards):**
  - Total Mentions (this week)
  - Average Broker Rating
  - Most Improved Broker
  - Highest Volume Platform (X / Reddit / Web)
  - Critical Issues Count

- **Broker Leaderboard Table**
  Columns: Rank | Broker | Overall Rating (big number) | Trend badge | 7 small parameter scores (or sparkline) | Change vs Last Week | Quick Actions (View Details)

- **7-Parameter Radar Chart**
  One combined radar chart showing top 3-4 brokers side-by-side.

- **Industry Themes Snapshot**
  Three cards: Positive Themes, Negative Themes, Emerging Topics + "Implications for SocialCoffee"

### 2. Per-Broker Detail View

Create a beautiful detail page/component (can be shown in a sheet, modal, or separate route `/brokers/[slug]`).

Sections:
- Header: Broker name + current rating + big trend indicator + previous week comparison
- Rating Breakdown: Beautiful horizontal bar chart or card grid for all 7 parameters with weights shown
- New Features: Clean table (Feature | Reaction | Volume | Links | Date)
- Key Quotes: Grid of quote cards (quote, context, platform badge, sentiment badge, source link)
- Sentiment & Themes: Categorized negative themes with counts and severity
- Technical Issues: Table or list with severity + issue_type badges
- Watch Items: List of items to monitor next week

### 3. Trends & Historical Comparison

- Line chart showing overall rating trend for all (or selected) brokers over last 4–8 weeks
- Table showing week-over-week changes
- "Most Improved" and "Biggest Decliner" callouts

### 4. New Features Tracking

- Main table of all new features across brokers this week
- Filters: By broker, reaction type, volume
- Ability to mark features as "Watch"

### 5. Technical Issues / Glitches

- Table with columns: Broker | Description | Severity | Type (Feature-specific / Platform-wide) | Volume | First Seen | Last Seen
- Summary cards: Critical count, Platform-wide vs Feature-specific split

### 6. Sentiment & Quotes

- Aggregated sentiment breakdown (positive / mixed / negative)
- Best and worst quotes of the week
- Theme cloud or categorized list

### 7. Data Sources Panel (sidebar or dedicated section)

Status cards for:
- Web (blogs + Firecrawl)
- X / Twitter
- Reddit (via Apify)
- Firecrawl extraction

Show last refresh time and item counts per source.

## Additional Requirements

- **Mock Data**: Include a realistic `mockData.ts` file with at least 2–3 full weeks of data for 6 brokers.
- **State Management**: Use React hooks + URL search params for filters (week, selected brokers).
- **Interactions**:
  - Clicking a broker in the leaderboard opens the detail view (use shadcn Sheet or Dialog)
  - Clicking quotes opens the source URL in new tab
  - Export buttons should trigger console logs or actual file generation (use `jsPDF` or simple markdown download for now)
- **Empty States & Loading**: Good loading skeletons and empty states.
- **Accessibility**: Proper labels, contrast, keyboard navigation.
- **Polish**: Subtle animations (framer-motion optional but nice), hover states, consistent spacing.

## File Structure Suggestion (generate this)

```
app/
├── (dashboard)/
│   ├── layout.tsx
│   ├── page.tsx                 ← Overview
│   ├── brokers/
│   │   └── [slug]/page.tsx
│   ├── trends/page.tsx
│   ├── features/page.tsx
│   ├── issues/page.tsx
│   └── sources/page.tsx
├── components/
│   ├── dashboard/
│   │   ├── broker-card.tsx
│   │   ├── rating-breakdown.tsx
│   │   ├── quotes-list.tsx
│   │   ├── new-features-table.tsx
│   │   ├── technical-issues-list.tsx
│   │   └── sentiment-themes.tsx
│   └── ui/ (shadcn components)
└── lib/
    └── mock-data.ts
```

Generate a **complete, cohesive, high-quality** dashboard experience. Prioritize clarity, scannability, and professional presentation over flashy effects.

Start by creating the main layout + overview page, then the key reusable components, then the detail views.

Use excellent component composition and TypeScript throughout.

---

**End of Prompt** — Paste everything above into Lovable.