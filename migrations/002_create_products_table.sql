-- Create products table
create table if not exists products (
    id uuid default gen_random_uuid() primary key,
    name text not null,
    price decimal(10, 2) not null,
    aliases text[] default array[]::text[],
    category text,
    stock integer default 0,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table products enable row level security;

-- Create policy to allow read access for everyone (public catalog)
create policy "Enable read access for all users" on products
    for select using (true);

-- Create policy to allow insert/update/delete only for authenticated users
create policy "Enable write access for authenticated users only" on products
    for all using (auth.role() = 'authenticated');
