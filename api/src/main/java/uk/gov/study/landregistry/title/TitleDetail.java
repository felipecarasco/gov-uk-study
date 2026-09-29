package uk.gov.study.landregistry.title;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.time.LocalDate;
import java.util.List;

/**
 * pricePaidPence and pricePaidDate are either both null or both set; a CHECK in
 * the database guarantees it.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TitleDetail(
        String titleNumber,
        Tenure tenure,
        String classOfTitle,
        Address address,
        Long pricePaidPence,
        LocalDate pricePaidDate,
        List<Proprietor> proprietors,
        List<Charge> charges) {
}
