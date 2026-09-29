package uk.gov.study.landregistry.title;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public class TitleRepository {

    private static final String FIND_BY_TITLE_NUMBER = """
            SELECT t.title_number,
                   t.tenure,
                   t.class_of_title,
                   t.address_line_1,
                   t.address_line_2,
                   t.town,
                   t.postcode,
                   t.price_paid_pence,
                   t.price_paid_date,
                   p.id      AS proprietor_id,
                   p.name    AS proprietor_name,
                   p.address AS proprietor_address,
                   c.id           AS charge_id,
                   c.lender       AS charge_lender,
                   c.charge_date  AS charge_date,
                   c.amount_pence AS charge_amount_pence
            FROM title t
            LEFT JOIN proprietor p ON p.title_id = t.id
            LEFT JOIN charge     c ON c.title_id = t.id
            WHERE upper(t.title_number) = upper(:titleNumber)
            ORDER BY p.id, c.id
            """;

    private final JdbcClient jdbcClient;

    TitleRepository(JdbcClient jdbcClient) {
        this.jdbcClient = jdbcClient;
    }

    public Optional<TitleDetail> findByTitleNumber(String titleNumber) {
        return jdbcClient
                .sql(FIND_BY_TITLE_NUMBER)
                .param("titleNumber", titleNumber)
                .query(new TitleDetailExtractor());
    }

    /**
     * Normalises a UK postcode for comparison: upper case, no spaces.
     * Used by the postcode search in phase 2 and by the seed.
     */
    public static String normalisePostcode(String raw) {
        if (raw == null) {
            return "";
        }
        return raw.replaceAll("\\s+", "").toUpperCase();
    }
}
