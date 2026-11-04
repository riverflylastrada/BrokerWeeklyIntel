create table if not exists public.social_mentions (
  id bigserial primary key,
  category text not null check (category in ('brokers','banks')),
  entity_slug text not null,
  entity_name text,
  source text not null,
  url text not null unique,
  title text,
  text text,
  rating smallint,
  posted_at timestamptz,
  sentiment text not null check (sentiment in ('positive','neutral','negative')),
  issue_tag text,
  engagement int,
  author text,
  run_id text,
  created_at timestamptz not null default now()
);
create index if not exists social_mentions_entity_idx on public.social_mentions (category, entity_slug, posted_at desc);
create index if not exists social_mentions_posted_idx on public.social_mentions (posted_at desc);
create table if not exists public.social_alerts (
  id bigserial primary key,
  category text not null,
  entity_slug text not null,
  entity_name text,
  alert_type text not null,
  issue_tag text,
  mention_count int not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  sample_urls text[],
  created_at timestamptz not null default now(),
  unique (category, entity_slug, alert_type, window_start)
);
create table if not exists public.social_runs (
  id bigserial primary key,
  category text not null,
  run_id text,
  trigger text,
  received int, inserted int,
  created_at timestamptz not null default now()
);
alter table public.social_mentions enable row level security;
alter table public.social_alerts enable row level security;
alter table public.social_runs enable row level security;
revoke all on public.social_mentions, public.social_alerts, public.social_runs from anon, authenticated;
grant select (id, category, entity_slug, entity_name, source, url, title, text, rating, posted_at, sentiment, issue_tag, engagement, created_at) on public.social_mentions to anon, authenticated;
grant select on public.social_alerts to anon, authenticated;
drop policy if exists "public read mentions" on public.social_mentions;
create policy "public read mentions" on public.social_mentions for select to anon, authenticated using (posted_at > now() - interval '90 days' or posted_at is null);
drop policy if exists "public read alerts" on public.social_alerts;
create policy "public read alerts" on public.social_alerts for select to anon, authenticated using (created_at > now() - interval '90 days');

create or replace function public.ingest_social_mentions(p_token text, p_category text, p_run_id text, p_trigger text, p_items jsonb)
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare v_expected text; v_ins int := 0; v_alerts int := 0; v_n int;
begin
  select token_sha256 into v_expected from ingest_tokens where name = 'social-mentions';
  if v_expected is null or encode(extensions.digest(coalesce(p_token,''), 'sha256'), 'hex') <> v_expected then
    raise exception 'unauthorized' using errcode = '28000';
  end if;
  if p_category not in ('brokers','banks') or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) > 2000 then
    raise exception 'bad payload' using errcode = '22023';
  end if;
  insert into social_mentions (category, entity_slug, entity_name, source, url, title, text, rating, posted_at, sentiment, issue_tag, engagement, author, run_id)
  select p_category, left(i->>'entity_slug',80), left(i->>'entity_name',120), left(i->>'source',40), left(i->>'url',1000),
         left(i->>'title',300), left(i->>'text',2000), nullif(i->>'rating','')::numeric::smallint,
         to_timestamp(nullif(i->>'posted_utc','')::double precision),
         case when i->>'sentiment' in ('positive','neutral','negative') then i->>'sentiment' else 'neutral' end,
         left(i->>'issue_tag',40), nullif(i->>'engagement','')::numeric::int, left(i->>'author',120), left(p_run_id,60)
  from jsonb_array_elements(p_items) i
  where coalesce(i->>'url','') <> '' and coalesce(i->>'entity_slug','') <> ''
  on conflict (url) do nothing;
  get diagnostics v_ins = row_count;
  -- spike alerts: >=3 negative mentions (or >=3 outage/login/withdrawal) for one entity in the last 12h
  insert into social_alerts (category, entity_slug, entity_name, alert_type, issue_tag, mention_count, window_start, window_end, sample_urls)
  select category, entity_slug, max(entity_name), 'negative_spike', mode() within group (order by issue_tag), count(*),
         date_trunc('hour', now()) - interval '12 hours', now(), (array_agg(url order by posted_at desc))[1:5]
  from social_mentions
  where category = p_category and posted_at > now() - interval '12 hours'
    and (sentiment = 'negative' or issue_tag in ('outage','login','withdrawal'))
  group by category, entity_slug having count(*) >= 3
  on conflict (category, entity_slug, alert_type, window_start) do update set mention_count = excluded.mention_count, window_end = excluded.window_end, sample_urls = excluded.sample_urls;
  get diagnostics v_alerts = row_count;
  delete from social_mentions where posted_at < now() - interval '90 days' or (posted_at is null and created_at < now() - interval '90 days');
  delete from social_alerts where created_at < now() - interval '90 days';
  delete from social_runs where created_at < now() - interval '90 days';
  insert into social_runs (category, run_id, trigger, received, inserted) values (p_category, left(p_run_id,60), left(p_trigger,40), jsonb_array_length(p_items), v_ins);
  return jsonb_build_object('ok', true, 'received', jsonb_array_length(p_items), 'inserted', v_ins, 'alerts', v_alerts);
end $$;
revoke all on function public.ingest_social_mentions(text,text,text,text,jsonb) from public;
grant execute on function public.ingest_social_mentions(text,text,text,text,jsonb) to anon;
