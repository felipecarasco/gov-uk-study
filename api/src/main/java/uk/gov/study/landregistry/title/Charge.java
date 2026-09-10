package uk.gov.study.landregistry.title;

import java.time.LocalDate;

/** amountPence é sempre em pence — nunca libras fracionárias. */
public record Charge(String lender, LocalDate chargeDate, long amountPence) {
}
