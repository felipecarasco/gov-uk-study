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
 * Monta um TitleDetail a partir do resultado do JOIN entre title, proprietor e charge.
 *
 * O JOIN produz produto cartesiano: um título com 2 proprietários e 2 ônus devolve
 * 4 linhas, cada proprietário repetido 2 vezes e cada ônus repetido 2 vezes. Por isso
 * acumulamos em mapas indexados pelo id da linha filha — a chave descarta as
 * repetições. LinkedHashMap preserva a ordem em que o banco devolveu.
 *
 * Devolve Optional, e não null: JdbcClient.query(ResultSetExtractor) rejeita um
 * retorno nulo com IllegalStateException("No result from ResultSetExtractor"),
 * então "não encontrei nada" precisa ser um valor de verdade.
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

                Date data = rs.getDate("price_paid_date");
                pricePaidDate = (data == null) ? null : data.toLocalDate();
            }

            // Em JDBC, getLong devolve 0 para NULL. wasNull() reporta sobre a
            // ÚLTIMA coluna lida, então precisa vir imediatamente depois do get —
            // é a armadilha clássica de LEFT JOIN.
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
