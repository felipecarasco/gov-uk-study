package uk.gov.study.landregistry.title;

import com.fasterxml.jackson.annotation.JsonInclude;

/** Linha 2 é opcional e pode ser null. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Address(String line1, String line2, String town, String postcode) {
}
