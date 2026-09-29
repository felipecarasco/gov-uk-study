package uk.gov.study.landregistry.title;

import java.time.LocalDate;

/** amountPence is always in pence, never fractional pounds. */
public record Charge(String lender, LocalDate chargeDate, long amountPence) {
}
