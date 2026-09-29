package uk.gov.study.landregistry.order;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * Body of POST /api/v1/orders.
 *
 * The messages follow GOV.UK wording (imperative, no "please", no full stop)
 * because the Flask front end may show them in the error summary as they are.
 */
public record CreateOrderRequest(
        @NotBlank(message = "Enter a title number")
        String titleNumber,

        @NotNull(message = "Select a document type")
        DocumentType documentType,

        @NotBlank(message = "Enter your full name")
        String applicantName,

        @NotBlank(message = "Enter your email address")
        @Email(message = "Enter an email address in the correct format, like name@example.com")
        String applicantEmail,

        @NotBlank(message = "Enter your address")
        String applicantAddress) {
}
