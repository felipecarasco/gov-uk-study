package uk.gov.study.landregistry.order;

import java.time.Instant;

/**
 * An order for an official copy of a title's register.
 *
 * No validation in the constructor, on purpose: the rules (positive amount,
 * existing title, unique reference) live in V3 constraints, which hold for
 * anyone who writes to the table. Validating user input is the HTTP layer's
 * job (see CreateOrderRequest).
 *
 * paidAt is null until the order is paid.
 */
public record RegisterOrder(
        String reference,
        String titleNumber,
        DocumentType documentType,
        String applicantName,
        String applicantEmail,
        String applicantAddress,
        OrderStatus status,
        long amountPence,
        Instant createdAt,
        Instant paidAt) {
}
