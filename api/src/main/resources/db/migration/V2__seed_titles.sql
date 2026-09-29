-- Fictitious data for development and tests.
-- No real property, person or lender.

INSERT INTO title (title_number, tenure, class_of_title,
                   address_line_1, address_line_2, town,
                   postcode, postcode_normalised,
                   price_paid_pence, price_paid_date)
VALUES
  ('SGL123456', 'FREEHOLD',  'Title absolute',
   '12 Mallow Gardens', NULL, 'Croydon', 'CR0 2QQ', 'CR02QQ',
   42500000, DATE '2019-06-14'),
  ('SGL123457', 'LEASEHOLD', 'Title absolute',
   'Flat 4, Hazelmere Court', '18 Mallow Gardens', 'Croydon', 'CR0 2QQ', 'CR02QQ',
   28750000, DATE '2021-11-02'),
  ('SGL123458', 'FREEHOLD',  'Possessory title',
   '3 Bramber Lane', NULL, 'Croydon', 'CR0 3RD', 'CR03RD',
   NULL, NULL),
  ('MX987654', 'FREEHOLD',  'Title absolute',
   '77 Wexford Road', NULL, 'Enfield', 'EN1 4TT', 'EN14TT',
   61000000, DATE '2023-03-28'),
  ('MX987655', 'LEASEHOLD', 'Qualified title',
   'Flat 9, Carrow House', '80 Wexford Road', 'Enfield', 'EN1 4TT', 'EN14TT',
   33200000, DATE '2018-09-10');

-- Proprietors. SGL123457 has two, to exercise the grouping in the extractor.
INSERT INTO proprietor (title_id, name, address)
SELECT id, 'ALEX MORGAN HOLLOWAY', '12 Mallow Gardens, Croydon, CR0 2QQ'
FROM title WHERE title_number = 'SGL123456';

INSERT INTO proprietor (title_id, name, address)
SELECT id, 'JAMIE PATEL', 'Flat 4, Hazelmere Court, 18 Mallow Gardens, Croydon, CR0 2QQ'
FROM title WHERE title_number = 'SGL123457';

INSERT INTO proprietor (title_id, name, address)
SELECT id, 'ROWAN PATEL', 'Flat 4, Hazelmere Court, 18 Mallow Gardens, Croydon, CR0 2QQ'
FROM title WHERE title_number = 'SGL123457';

INSERT INTO proprietor (title_id, name, address)
SELECT id, 'SAM OKONKWO', '3 Bramber Lane, Croydon, CR0 3RD'
FROM title WHERE title_number = 'SGL123458';

INSERT INTO proprietor (title_id, name, address)
SELECT id, 'CASEY LINDQVIST', '77 Wexford Road, Enfield, EN1 4TT'
FROM title WHERE title_number = 'MX987654';

INSERT INTO proprietor (title_id, name, address)
SELECT id, 'DEVAN ASHWORTH', 'Flat 9, Carrow House, 80 Wexford Road, Enfield, EN1 4TT'
FROM title WHERE title_number = 'MX987655';

-- Charges. SGL123457 has two proprietors AND two charges: the case that makes
-- the JOIN a cartesian product and proves the extractor deduplicates correctly.
INSERT INTO charge (title_id, lender, charge_date, amount_pence)
SELECT id, 'NORTHWOOD BUILDING SOCIETY', DATE '2019-06-14', 34000000
FROM title WHERE title_number = 'SGL123456';

INSERT INTO charge (title_id, lender, charge_date, amount_pence)
SELECT id, 'CALDER BANK PLC', DATE '2021-11-02', 23000000
FROM title WHERE title_number = 'SGL123457';

INSERT INTO charge (title_id, lender, charge_date, amount_pence)
SELECT id, 'MERIDIAN LENDING LTD', DATE '2024-01-17', 4500000
FROM title WHERE title_number = 'SGL123457';

INSERT INTO charge (title_id, lender, charge_date, amount_pence)
SELECT id, 'NORTHWOOD BUILDING SOCIETY', DATE '2023-03-28', 45750000
FROM title WHERE title_number = 'MX987654';

-- SGL123458 and MX987655 have no charges on purpose: they exercise the LEFT JOIN
-- returning an empty list rather than null.
