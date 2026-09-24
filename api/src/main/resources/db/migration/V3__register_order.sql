-- An order for an official copy of a title's register.
-- Created as PENDING_PAYMENT when the user confirms check your answers;
-- phase 4 moves it to PAID and fills in paid_at.

CREATE TABLE register_order (
    id                BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reference         TEXT        NOT NULL UNIQUE,
    title_number      TEXT        NOT NULL REFERENCES title (title_number),
    document_type     TEXT        NOT NULL CHECK (document_type IN ('TITLE_REGISTER', 'TITLE_PLAN')),
    applicant_name    TEXT        NOT NULL,
    applicant_email   TEXT        NOT NULL,
    applicant_address TEXT        NOT NULL,
    status            TEXT        NOT NULL CHECK (status IN ('PENDING_PAYMENT', 'PAID')),
    amount_pence      BIGINT      NOT NULL CHECK (amount_pence > 0),
    created_at        TIMESTAMPTZ NOT NULL,
    paid_at           TIMESTAMPTZ
);

-- PostgreSQL indexes the referenced side of a foreign key on its own
-- (title_number is already UNIQUE), but not the referencing side. Without this
-- index, listing the orders for a title scans the whole table.
CREATE INDEX idx_register_order_title_number ON register_order (title_number);
