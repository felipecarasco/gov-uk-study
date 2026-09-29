-- Land register: tables for the read path.
-- The register_order table arrives in V3, with the order flow.

CREATE TABLE title (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title_number        TEXT   NOT NULL UNIQUE,
    tenure              TEXT   NOT NULL CHECK (tenure IN ('FREEHOLD', 'LEASEHOLD')),
    class_of_title      TEXT   NOT NULL,
    address_line_1      TEXT   NOT NULL,
    address_line_2      TEXT,
    town                TEXT   NOT NULL,
    postcode            TEXT   NOT NULL,
    postcode_normalised TEXT   NOT NULL,
    price_paid_pence    BIGINT,
    price_paid_date     DATE,
    CONSTRAINT price_paid_juntos CHECK (
        (price_paid_pence IS NULL) = (price_paid_date IS NULL)
    )
);

COMMENT ON COLUMN title.postcode_normalised IS
    'Postcode in upper case with no spaces, for searching. See V2 and TitleRepository.';

-- Composite index: serves both the postcode filter and the stable ordering
-- that keyset pagination in phase 2 needs.
CREATE INDEX idx_title_postcode_normalised
    ON title (postcode_normalised, title_number);

CREATE TABLE proprietor (
    id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title_id BIGINT NOT NULL REFERENCES title (id) ON DELETE CASCADE,
    name     TEXT   NOT NULL,
    address  TEXT   NOT NULL
);

CREATE INDEX idx_proprietor_title_id ON proprietor (title_id);

CREATE TABLE charge (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title_id     BIGINT NOT NULL REFERENCES title (id) ON DELETE CASCADE,
    lender       TEXT   NOT NULL,
    charge_date  DATE   NOT NULL,
    amount_pence BIGINT NOT NULL CHECK (amount_pence > 0)
);

CREATE INDEX idx_charge_title_id ON charge (title_id);
