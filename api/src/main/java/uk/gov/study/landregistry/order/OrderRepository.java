package uk.gov.study.landregistry.order;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
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
                   created_at,
                   paid_at
            FROM register_order
            WHERE reference = :reference
            """;

    // The status check in the WHERE clause is what makes paying safe: two
    // requests racing to pay the same order cannot both succeed, and paying an
    // order that is already paid changes nothing. No read-then-write, so no
    // window between checking the status and changing it.
    private static final String MARK_PAID = """
            UPDATE register_order
            SET status = 'PAID',
                paid_at = :paidAt
            WHERE reference = :reference
              AND status = 'PENDING_PAYMENT'
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

    /**
     * Moves a pending order to PAID. Returns false, changing nothing, when there
     * is no such order or it is already paid.
     */
    public boolean markPaid(String reference, Instant paidAt) {
        int updated = jdbcClient
                .sql(MARK_PAID)
                .param("reference", reference)
                .param("paidAt", paidAt.atOffset(ZoneOffset.UTC))
                .update();
        return updated == 1;
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
                rs.getObject("created_at", OffsetDateTime.class).toInstant(),
                toInstant(rs.getObject("paid_at", OffsetDateTime.class)));
    }

    private static Instant toInstant(OffsetDateTime value) {
        return value == null ? null : value.toInstant();
    }
}
