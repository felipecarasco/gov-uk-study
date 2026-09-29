package uk.gov.study.landregistry.title;

import com.fasterxml.jackson.annotation.JsonInclude;

/** Line 2 is optional and may be null. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Address(String line1, String line2, String town, String postcode) {
}
