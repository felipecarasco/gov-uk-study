package uk.gov.study.landregistry.title;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
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

    // Keyset pagination. Instead of an OFFSET, which reads and throws away every
    // skipped row, each page starts from the last title number already shown.
    // The database seeks straight to it through idx_title_postcode_normalised
    // (postcode_normalised, title_number); with the postcode fixed by equality,
    // ordering by title_number alone follows the index.
    private static final String FIND_BY_POSTCODE_AFTER = """
            SELECT title_number, tenure, address_line_1, address_line_2, town, postcode
            FROM title
            WHERE postcode_normalised = :postcode
              AND title_number > :after
            ORDER BY title_number
            LIMIT :limit
            """;

    // The same index read backwards: the rows just before :before, nearest first.
    private static final String FIND_BY_POSTCODE_BEFORE = """
            SELECT title_number, tenure, address_line_1, address_line_2, town, postcode
            FROM title
            WHERE postcode_normalised = :postcode
              AND title_number < :before
            ORDER BY title_number DESC
            LIMIT :limit
            """;

    // Cheap here: an equality on the index's first column, over the few dozen
    // addresses a postcode can hold. The cost keyset avoids is counting or
    // skipping rows of an unbounded list, not this.
    private static final String COUNT_BY_POSTCODE = """
            SELECT count(*) FROM title WHERE postcode_normalised = :postcode
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
     * Up to {@code limit} titles in a postcode, in title number order, starting
     * after {@code afterTitleNumber} ("" for the first page, since every title
     * number sorts after it).
     */
    public List<TitleSummary> findByPostcodeAfter(String normalisedPostcode, String afterTitleNumber, int limit) {
        return jdbcClient
                .sql(FIND_BY_POSTCODE_AFTER)
                .param("postcode", normalisedPostcode)
                .param("after", afterTitleNumber)
                .param("limit", limit)
                .query(TitleRepository::mapSummary)
                .list();
    }

    /**
     * Up to {@code limit} titles that come just before {@code beforeTitleNumber},
     * returned in ascending order like any other page.
     */
    public List<TitleSummary> findByPostcodeBefore(String normalisedPostcode, String beforeTitleNumber, int limit) {
        List<TitleSummary> nearestFirst = jdbcClient
                .sql(FIND_BY_POSTCODE_BEFORE)
                .param("postcode", normalisedPostcode)
                .param("before", beforeTitleNumber)
                .param("limit", limit)
                .query(TitleRepository::mapSummary)
                .list();
        return nearestFirst.reversed();
    }

    public long countByPostcode(String normalisedPostcode) {
        return jdbcClient
                .sql(COUNT_BY_POSTCODE)
                .param("postcode", normalisedPostcode)
                .query(Long.class)
                .single();
    }

    private static TitleSummary mapSummary(ResultSet rs, int rowNum) throws SQLException {
        return new TitleSummary(
                rs.getString("title_number"),
                Tenure.valueOf(rs.getString("tenure")),
                new Address(
                        rs.getString("address_line_1"),
                        rs.getString("address_line_2"),
                        rs.getString("town"),
                        rs.getString("postcode")));
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
