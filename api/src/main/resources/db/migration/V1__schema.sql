-- Registro de imóveis: tabelas do caminho de leitura.
-- A tabela register_order chega na V3, junto com o fluxo de pedido.

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
    'Postcode em maiúsculas e sem espaços, para busca. Ver a V2 e o TitleRepository.';

-- Índice composto: serve tanto o filtro por postcode quanto a ordenação
-- estável exigida pela paginação por keyset da fase 2.
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
