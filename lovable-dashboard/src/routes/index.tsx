import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { DashboardHeader } from "@/components/dashboard/header";
import { useWeek } from "@/hooks/use-week";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Leaderboard } from "@/components/dashboard/leaderboard";
import { BrokerRadar } from "@/components/dashboard/radar-chart";
import { BrokerDetailSheet } from "@/components/dashboard/broker-detail";
import { TrendIndicator, SentimentDot } from "@/components/dashboard/shared";
import { FeaturesTable } from "@/components/dashboard/features-table";
import { Activity, MessageSquare, Sparkles, AlertOctagon, TrendingUp } from "lucide-react";

export const Route = createFileRoute("/")({
  component: Overview,
});

function Metric({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
            {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="h-4 w-4" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Overview() {
  const { week, setWeek, report } = useWeek();
  const [selected, setSelected] = useState<string | null>(null);

  const avg = (
    report.brokers.reduce((s, b) => s + b.overall_rating, 0) / report.brokers.length
  ).toFixed(1);
  const mostImproved = [...report.brokers].sort(
    (a, b) =>
      (b.overall_rating - (b.previous_rating ?? 0)) -
      (a.overall_rating - (a.previous_rating ?? 0)),
  )[0];
  const criticalCount = report.brokers.reduce(
    (s, b) => s + b.technical_issues.filter((i) => i.severity === "critical").length,
    0,
  );
  const totalMentions = report.brokers.reduce(
    (s, b) => s + b.negative_themes.reduce((a, t) => a + t.count, 0),
    0,
  );

  const selectedBroker = report.brokers.find((b) => b.slug === selected) ?? null;

  return (
    <>
      <DashboardHeader week={week} onWeekChange={setWeek} />
      <main className="space-y-6 p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
          <p className="text-sm text-muted-foreground">
            Weekly snapshot across {report.brokers.length} brokers · Report v{report.report_version}
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="Total Mentions" value={totalMentions.toLocaleString()} hint="across X, Reddit, web" icon={MessageSquare} />
          <Metric label="Avg Broker Rating" value={`${avg}/10`} hint="weighted average" icon={Activity} />
          <Metric label="Most Improved" value={mostImproved.broker} hint={`+${(mostImproved.overall_rating - (mostImproved.previous_rating ?? 0)).toFixed(1)} vs last week`} icon={TrendingUp} />
          <Metric label="Top Platform" value="X / Reddit" hint="highest discussion volume" icon={Sparkles} />
          <Metric label="Critical Issues" value={String(criticalCount)} hint="open this week" icon={AlertOctagon} />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Leaderboard brokers={report.brokers} onSelect={setSelected} />
          </div>
          <BrokerRadar brokers={report.brokers} />
        </div>

        <FeaturesTable
          brokers={report.brokers}
          subtitle="Mandatory consolidated cross-broker launches with evidence links"
        />

        <div className="grid gap-4 md:grid-cols-3">
          <ThemeCard title="Positive Themes" items={report.industry_themes.positive} tone="positive" />
          <ThemeCard title="Negative Themes" items={report.industry_themes.negative} tone="negative" />
          <ThemeCard title="Emerging Topics" items={report.industry_themes.emerging} tone="neutral" />
        </div>

        {report.industry_themes.implications_for_socialcoffee && (
          <Card className="border-primary/30 bg-primary/5">
            <CardHeader>
              <CardTitle className="text-base">Implications for SocialCoffee</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">
                {report.industry_themes.implications_for_socialcoffee}
              </p>
            </CardContent>
          </Card>
        )}
      </main>

      <BrokerDetailSheet
        broker={selectedBroker}
        open={!!selectedBroker}
        onOpenChange={(o) => !o && setSelected(null)}
      />
    </>
  );
}

function ThemeCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "negative" | "neutral";
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <SentimentDot sentiment={tone} />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm">
          {items.map((it) => (
            <li key={it} className="flex gap-2">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
              <span className="text-foreground/90">{it}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
