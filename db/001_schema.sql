-- GoDoc Booking System — schema
-- Applied to Supabase via MCP; kept here for reproducibility.

-- Drop stale Prisma-era objects
drop table if exists public.bookings cascade;
drop table if exists public.slots cascade;
drop table if exists public.patients cascade;
drop table if exists public.doctors cascade;
drop table if exists public._prisma_migrations cascade;
drop type if exists public."BookingStatus";
drop type if exists public.booking_status;

-- Booking lifecycle states
create type public.booking_status as enum ('pending','confirmed','cancelled','completed');

create table public.doctors (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  specialty text
);

create table public.patients (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text
);

create table public.slots (
  id uuid primary key default gen_random_uuid(),
  doctor_id uuid not null references public.doctors(id) on delete cascade,
  start_time timestamptz not null,
  end_time timestamptz not null,
  constraint slot_time_valid check (end_time > start_time)
);
create index slots_doctor_start_idx on public.slots (doctor_id, start_time);

create table public.bookings (
  id uuid primary key default gen_random_uuid(),
  slot_id uuid not null references public.slots(id),
  patient_id uuid not null references public.patients(id),
  status public.booking_status not null default 'confirmed',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Let the database own updated_at on every UPDATE.
create extension if not exists moddatetime schema extensions;
create trigger bookings_set_updated_at
  before update on public.bookings
  for each row execute function extensions.moddatetime(updated_at);

-- Correctness guarantee: at most one active (pending/confirmed) booking per slot.
-- Two concurrent inserts for the same slot serialize on this partial unique index;
-- exactly one commits, the other raises 23505 (unique_violation) -> mapped to HTTP 409.
create unique index one_active_booking_per_slot
  on public.bookings (slot_id)
  where status in ('pending','confirmed');
create index bookings_patient_idx on public.bookings (patient_id);
