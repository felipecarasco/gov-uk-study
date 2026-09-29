package uk.gov.study.landregistry.title;

/** One row of a postcode search: enough to recognise the property and open its detail. */
public record TitleSummary(String titleNumber, Tenure tenure, Address address) {
}
