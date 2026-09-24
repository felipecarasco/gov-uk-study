package uk.gov.study.landregistry.order;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Optional;

@Repository
public class OrderRepository {

    private static final String INSERT = """
            INSERT INTO register_order (
                reference, title_number, document_type,
                applicant_name, applicant_email, applicant_address,
                status, amount_pence, created_at)
            VALUES (
                :reference, :titleNumber, :documentType,
                :applicantName, :applicantEmail, :applicantAddress,
                :status, :amountPence, :createdAt)
            """;

    private static final String FIND_BY_REFERENCE = """
            SELECT reference,
                   title_number,
                   document_type,
                   applicant_name,
                   applicant_email,
                   applicant_address,
                   status,
                   amount_pence,
                   created_at
            FROM register_order
            WHERE reference = :reference
            """;

    private final JdbcClient jdbcClient;

    OrderRepository(JdbcClient jdbcClient) {
        this.jdbcClient = jdbcClient;
    }

    /**
     * Saves the order. A constraint violation (duplicate reference, unknown
     * title, non-positive amount) surfaces as DataIntegrityViolationException.
     */
    public void insert(RegisterOrder order) {
        jdbcClient
                .sql(INSERT)
                .param("reference", order.reference())
                .param("titleNumber", order.titleNumber())
                // The driver cannot convert a Java enum; send its name, which is
                // exactly the value the V3 CHECK accepts.
                .param("documentType", order.documentType().name())
                .param("applicantName", order.applicantName())
                .param("applicantEmail", order.applicantEmail())
                .param("applicantAddress", order.applicantAddress())
                .param("status", order.status().name())
                .param("amountPence", order.amountPence())
                // The PostgreSQL driver maps OffsetDateTime to TIMESTAMPTZ;
                // Instant is not among the types the JDBC spec covers.
                .param("createdAt", order.createdAt().atOffset(ZoneOffset.UTC))
                .update();
    }

    public Optional<RegisterOrder> findByReference(String reference) {
        return jdbcClient
                .sql(FIND_BY_REFERENCE)
                .param("reference", reference)
                .query(OrderRepository::mapRow)
                .optional();
    }

    // The reverse of insert(): text back to enum, OffsetDateTime back to Instant.
    private static RegisterOrder mapRow(ResultSet rs, int rowNum) throws SQLException {
        return new RegisterOrder(
                rs.getString("reference"),
                rs.getString("title_number"),
                DocumentType.valueOf(rs.getString("document_type")),
                rs.getString("applicant_name"),
                rs.getString("applicant_email"),
                rs.getString("applicant_address"),
                OrderStatus.valueOf(rs.getString("status")),
                rs.getLong("amount_pence"),
                rs.getObject("created_at", OffsetDateTime.class).toInstant());
    }
}
