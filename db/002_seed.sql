-- GoDoc Booking System — seed data (stands in for login/onboarding)

insert into public.doctors (name, specialty) values
  ('Dr. Amelia Tan', 'General Practitioner'),
  ('Dr. Benjamin Lim', 'Cardiology'),
  ('Dr. Chloe Wong', 'Dermatology'),
  ('Dr. Darren Ng', 'Pediatrics'),
  ('Dr. Evelyn Koh', 'Psychiatry');

insert into public.patients (name, email) values
  ('Alice Chen', 'alice@example.com'),
  ('Bob Kumar', 'bob@example.com'),
  ('Carmen Ortiz', 'carmen@example.com'),
  ('Daniel Osei', 'daniel@example.com'),
  ('Ela Yilmaz', 'ela@example.com'),
  ('Farid Rahman', 'farid@example.com');

-- Hourly slots 09:00-16:00 (start times) for the next 3 days, per doctor.
insert into public.slots (doctor_id, start_time, end_time)
select d.id, ts, ts + interval '1 hour'
from public.doctors d
cross join generate_series(
  date_trunc('day', now()) + interval '1 day' + interval '9 hours',
  date_trunc('day', now()) + interval '3 day' + interval '16 hours',
  interval '1 hour'
) as ts
where extract(hour from ts) between 9 and 16;
