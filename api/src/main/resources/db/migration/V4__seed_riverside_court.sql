-- A block of 25 flats in one postcode, so that postcode search has more than
-- one page of results. generate_series builds the rows instead of 25 INSERTs.
-- Fictitious, like the rest of the seed.

INSERT INTO title (title_number, tenure, class_of_title,
                   address_line_1, address_line_2, town,
                   postcode, postcode_normalised,
                   price_paid_pence, price_paid_date)
SELECT 'TGL1000' || lpad(n::text, 2, '0'),
       'LEASEHOLD',
       'Title absolute',
       'Flat ' || n || ', Riverside Court',
       '2 Wharf Lane',
       'London',
       'SE1 7PB',
       'SE17PB',
       NULL,
       NULL
FROM generate_series(1, 25) AS n;

-- One proprietor per flat, cycling through five names.
INSERT INTO proprietor (title_id, name, address)
SELECT t.id,
       (ARRAY['ASHA KAUR', 'BEN OKAFOR', 'CHLOE WREN', 'DEV MISTRY', 'ELLA QUINN'])
           [1 + (right(t.title_number, 2)::int % 5)],
       t.address_line_1 || ', ' || t.address_line_2
FROM title t
WHERE t.postcode_normalised = 'SE17PB';
