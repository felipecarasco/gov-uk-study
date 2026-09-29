package uk.gov.study.landregistry.title;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import uk.gov.study.landregistry.AbstractPostgresIT;

import java.time.LocalDate;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

class TitleRepositoryIT extends AbstractPostgresIT {

    @Autowired
    private TitleRepository repository;

    @Test
    void findsATitleWithItsProprietorAndCharge() {
        Optional<TitleDetail> found = repository.findByTitleNumber("SGL123456");

        assertThat(found).isPresent();
        TitleDetail t = found.orElseThrow();

        assertThat(t.titleNumber()).isEqualTo("SGL123456");
        assertThat(t.tenure()).isEqualTo(Tenure.FREEHOLD);
        assertThat(t.classOfTitle()).isEqualTo("Title absolute");
        assertThat(t.address().line1()).isEqualTo("12 Mallow Gardens");
        assertThat(t.address().line2()).isNull();
        assertThat(t.address().town()).isEqualTo("Croydon");
        assertThat(t.address().postcode()).isEqualTo("CR0 2QQ");
        assertThat(t.pricePaidPence()).isEqualTo(42_500_000L);
        assertThat(t.pricePaidDate()).isEqualTo(LocalDate.of(2019, 6, 14));
        assertThat(t.proprietors()).singleElement()
                .extracting(Proprietor::name).isEqualTo("ALEX MORGAN HOLLOWAY");
        assertThat(t.charges()).singleElement()
                .extracting(Charge::lender).isEqualTo("NORTHWOOD BUILDING SOCIETY");
    }

    @Test
    void doesNotDuplicateWhenSeveralProprietorsMeetSeveralCharges() {
        // SGL123457 has 2 proprietors and 2 charges. A naive JOIN returns 4 rows;
        // the extractor has to deduplicate by id and produce 2 and 2.
        TitleDetail t = repository.findByTitleNumber("SGL123457").orElseThrow();

        assertThat(t.proprietors()).hasSize(2)
                .extracting(Proprietor::name)
                .containsExactlyInAnyOrder("JAMIE PATEL", "ROWAN PATEL");
        assertThat(t.charges()).hasSize(2)
                .extracting(Charge::lender)
                .containsExactlyInAnyOrder("CALDER BANK PLC", "MERIDIAN LENDING LTD");
    }

    @Test
    void returnsEmptyListsWhenThereAreNoCharges() {
        TitleDetail t = repository.findByTitleNumber("SGL123458").orElseThrow();

        assertThat(t.proprietors()).hasSize(1);
        assertThat(t.charges()).isEmpty();
        assertThat(t.pricePaidPence()).isNull();
        assertThat(t.pricePaidDate()).isNull();
    }

    @Test
    void returnsEmptyWhenTheTitleDoesNotExist() {
        assertThat(repository.findByTitleNumber("ZZ000000")).isEmpty();
    }

    @Test
    void lookupIgnoresCase() {
        assertThat(repository.findByTitleNumber("sgl123456")).isPresent();
    }

    @Test
    void normalisesPostcodeByRemovingSpacesAndUpperCasing() {
        assertThat(TitleRepository.normalisePostcode(" cr0 2qq ")).isEqualTo("CR02QQ");
        assertThat(TitleRepository.normalisePostcode("EN1  4TT")).isEqualTo("EN14TT");
        assertThat(TitleRepository.normalisePostcode(null)).isEqualTo("");
    }
}
