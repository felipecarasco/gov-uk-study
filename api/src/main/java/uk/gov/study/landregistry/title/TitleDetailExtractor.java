package uk.gov.study.landregistry.title;

import org.springframework.jdbc.core.ResultSetExtractor;

import java.sql.Date;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Builds a TitleDetail from the JOIN of title, proprietor and charge.
 *
 * The JOIN is a cartesian product: a title with 2 proprietors and 2 charges
 * returns 4 rows, each proprietor repeated twice and each charge repeated twice.
 * So rows are collected into maps keyed by the child row's id, and the key drops
 * the repeats. LinkedHashMap keeps the order the database returned.
 *
 * Returns Optional, not null: JdbcClient.query(ResultSetExtractor) rejects a null
 * result with IllegalStateException("No result from ResultSetExtractor"), so
 * "found nothing" has to be a real value.
 */
class TitleDetailExtractor implements ResultSetExtractor<Optional<TitleDetail>> {

    @Override
    public Optional<TitleDetail> extractData(ResultSet rs) throws SQLException {
        Map<Long, Proprietor> proprietors = new LinkedHashMap<>();
        Map<Long, Charge> charges = new LinkedHashMap<>();

        String titleNumber = null;
        Tenure tenure = null;
        String classOfTitle = null;
        Address address = null;
        Long pricePaidPence = null;
        LocalDate pricePaidDate = null;

        while (rs.next()) {
            if (titleNumber == null) {
                titleNumber = rs.getString("title_number");
                tenure = Tenure.valueOf(rs.getString("tenure"));
                classOfTitle = rs.getString("class_of_title");
                address = new Address(
                        rs.getString("address_line_1"),
                        rs.getString("address_line_2"),
                        rs.getString("town"),
                        rs.getString("postcode"));

                long pence = rs.getLong("price_paid_pence");
                pricePaidPence = rs.wasNull() ? null : pence;

                Date saleDate = rs.getDate("price_paid_date");
                pricePaidDate = (saleDate == null) ? null : saleDate.toLocalDate();
            }

            // In JDBC, getLong returns 0 for NULL. wasNull() reports on the LAST
            // column read, so it must come right after the get. This is the
            // classic LEFT JOIN pitfall.
            long proprietorId = rs.getLong("proprietor_id");
            if (!rs.wasNull() && !proprietors.containsKey(proprietorId)) {
                proprietors.put(proprietorId, new Proprietor(
                        rs.getString("proprietor_name"),
                        rs.getString("proprietor_address")));
            }

            long chargeId = rs.getLong("charge_id");
            if (!rs.wasNull() && !charges.containsKey(chargeId)) {
                charges.put(chargeId, new Charge(
                        rs.getString("charge_lender"),
                        rs.getDate("charge_date").toLocalDate(),
                        rs.getLong("charge_amount_pence")));
            }
        }

        if (titleNumber == null) {
            return Optional.empty();
        }

        return Optional.of(new TitleDetail(titleNumber, tenure, classOfTitle, address,
                pricePaidPence, pricePaidDate,
                List.copyOf(proprietors.values()),
                List.copyOf(charges.values())));
    }
}
