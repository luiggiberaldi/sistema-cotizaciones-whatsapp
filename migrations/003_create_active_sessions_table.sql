-- Create active_sessions table
create table if not exists active_sessions (
    client_phone text primary key,
    items jsonb default '[]'::jsonb,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table active_sessions enable row level security;

-- Create policy to allow read/write access for authenticated users (service role)
create policy "Enable all access for authenticated users" on active_sessions
    for all using (auth.role() = 'authenticated');
