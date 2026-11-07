-- Қаржы ботының схемасы (Supabase Postgres).
-- Қайта іске қосуға қауіпсіз: бәрі "if not exists".

create table if not exists public.users (
    id            uuid primary key default gen_random_uuid(),
    telegram_id   bigint not null unique,          -- unique өзі индекс құрады
    name          text,
    reminder_hour int not null default 9 check (reminder_hour between 0 and 23),
    created_at    timestamptz not null default now()
);

create table if not exists public.obligations (
    id                 uuid primary key default gen_random_uuid(),
    user_id            uuid not null references public.users(id) on delete cascade,
    title              text not null,
    amount             numeric(14,2) not null check (amount > 0),
    day_of_month       int not null check (day_of_month between 1 and 31),
    remind_days_before int[] not null default '{7,2,0}',
    active             boolean not null default true,
    created_at         timestamptz not null default now()
);

create table if not exists public.transactions (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references public.users(id) on delete cascade,
    type       text not null check (type in ('income', 'expense')),
    amount     numeric(14,2) not null check (amount > 0),
    category   text not null default 'Басқа',
    note       text not null default '',
    created_at timestamptz not null default now()
);

create index if not exists users_reminder_hour_idx   on public.users (reminder_hour);
create index if not exists obligations_user_idx      on public.obligations (user_id) where active;
create index if not exists transactions_user_date_idx on public.transactions (user_id, created_at desc);

-- Қауіпсіздік: Supabase-тің жария API-і арқылы бұл кестелерге ешкім кіре алмасын.
-- Бот тікелей Postgres арқылы қосылады, сондықтан RLS оған кедергі емес.
alter table public.users        enable row level security;
alter table public.obligations  enable row level security;
alter table public.transactions enable row level security;
