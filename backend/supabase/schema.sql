create extension if not exists pgcrypto;

create table if not exists public.plant_cycles (
  id uuid primary key default gen_random_uuid(),
  captured_at timestamptz not null default timezone('utc', now()),
  image_url text,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.sensor_readings (
  id bigserial primary key,
  cycle_id uuid not null unique references public.plant_cycles(id) on delete cascade,
  temp_c double precision,
  humidity_pct double precision,
  light_state text,
  soil_summary text,
  soil_majority text,
  temp_readings double precision[],
  hum_readings double precision[],
  soil_readings text[],
  soil_wetness_pct double precision,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.ai_analyses (
  id bigserial primary key,
  cycle_id uuid not null unique references public.plant_cycles(id) on delete cascade,
  disease text,
  plant text,
  confidence double precision,
  todos jsonb,
  recommendation jsonb,
  prompt_markdown text,
  response_markdown text,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.actuator_actions (
  id bigserial primary key,
  cycle_id uuid not null unique references public.plant_cycles(id) on delete cascade,
  actions text,
  created_at timestamptz not null default timezone('utc', now())
);

-- Migration: add multi-sensor reading columns to existing tables
alter table public.sensor_readings add column if not exists temp_readings double precision[];
alter table public.sensor_readings add column if not exists hum_readings double precision[];
alter table public.sensor_readings add column if not exists soil_readings text[];
alter table public.sensor_readings add column if not exists soil_wetness_pct double precision;
alter table public.ai_analyses add column if not exists todos jsonb;

create index if not exists idx_plant_cycles_captured_at on public.plant_cycles (captured_at desc);
create index if not exists idx_sensor_readings_cycle_id on public.sensor_readings (cycle_id);
create index if not exists idx_ai_analyses_cycle_id on public.ai_analyses (cycle_id);
create index if not exists idx_actuator_actions_cycle_id on public.actuator_actions (cycle_id);

alter table public.plant_cycles enable row level security;
alter table public.sensor_readings enable row level security;
alter table public.ai_analyses enable row level security;
alter table public.actuator_actions enable row level security;

drop policy if exists plant_cycles_read on public.plant_cycles;
create policy plant_cycles_read
on public.plant_cycles
for select
using (true);

drop policy if exists sensor_readings_read on public.sensor_readings;
create policy sensor_readings_read
on public.sensor_readings
for select
using (true);

drop policy if exists ai_analyses_read on public.ai_analyses;
create policy ai_analyses_read
on public.ai_analyses
for select
using (true);

drop policy if exists actuator_actions_read on public.actuator_actions;
create policy actuator_actions_read
on public.actuator_actions
for select
using (true);

insert into storage.buckets (id, name, public)
values ('plant-images', 'plant-images', true)
on conflict (id) do nothing;

drop policy if exists storage_public_read on storage.objects;
create policy storage_public_read
on storage.objects
for select
to public
using (bucket_id = 'plant-images');
