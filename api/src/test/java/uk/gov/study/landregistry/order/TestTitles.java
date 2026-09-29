package uk.gov.study.landregistry.order;

import uk.gov.study.landregistry.title.Address;
import uk.gov.study.landregistry.title.Tenure;
import uk.gov.study.landregistry.title.TitleDetail;

import java.time.LocalDate;
import java.util.List;

final class TestTitles {

    private TestTitles() {
    }

    static TitleDetail example() {
        return new TitleDetail(
                "SGL123456", Tenure.FREEHOLD, "Title absolute",
                new Address("12 Mallow Gardens", null, "Croydon", "CR0 2QQ"),
                42_500_000L, LocalDate.of(2019, 6, 14),
                List.of(), List.of());
    }
}
