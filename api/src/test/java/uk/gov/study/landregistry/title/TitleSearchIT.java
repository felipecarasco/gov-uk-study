package uk.gov.study.landregistry.title;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import uk.gov.study.landregistry.AbstractPostgresIT;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class TitleSearchIT extends AbstractPostgresIT {

    @Autowired
    private TitleRepository repository;

    private static List<String> numbers(List<TitleSummary> titles) {
        return titles.stream().map(TitleSummary::titleNumber).toList();
    }

    @Test
    void returnsTheTitlesInAPostcodeInTitleNumberOrder() {
        List<TitleSummary> page = repository.findByPostcodeAfter("CR02QQ", "", 10);

        assertThat(numbers(page)).containsExactly("SGL123456", "SGL123457");
        assertThat(page.getFirst().tenure()).isEqualTo(Tenure.FREEHOLD);
        assertThat(page.getFirst().address().postcode()).isEqualTo("CR0 2QQ");
    }

    @Test
    void keepsTheOptionalSecondAddressLine() {
        List<TitleSummary> page = repository.findByPostcodeAfter("CR02QQ", "", 10);

        assertThat(page.get(0).address().line2()).isNull();
        assertThat(page.get(1).address().line2()).isEqualTo("18 Mallow Gardens");
    }

    @Test
    void startsAfterTheGivenTitleNumber() {
        assertThat(numbers(repository.findByPostcodeAfter("SE17PB", "TGL100020", 10)))
                .containsExactly("TGL100021", "TGL100022", "TGL100023", "TGL100024", "TGL100025");
    }

    @Test
    void endsJustBeforeTheGivenTitleNumberInAscendingOrder() {
        assertThat(numbers(repository.findByPostcodeBefore("SE17PB", "TGL100021", 5)))
                .containsExactly("TGL100016", "TGL100017", "TGL100018", "TGL100019", "TGL100020");
    }

    @Test
    void pagesForwardThroughABlockWithoutGapsOrRepeats() {
        List<String> seen = new ArrayList<>();
        String after = "";
        int pages = 0;

        while (true) {
            List<TitleSummary> page = repository.findByPostcodeAfter("SE17PB", after, 10);
            if (page.isEmpty()) {
                break;
            }
            pages++;
            seen.addAll(numbers(page));
            after = page.getLast().titleNumber();
        }

        assertThat(pages).isEqualTo(3);
        assertThat(seen).hasSize(25).doesNotHaveDuplicates().isSorted();
    }

    @Test
    void pagesBackwardFromTheEndToTheStart() {
        List<String> seen = new ArrayList<>();
        // A value that sorts after every title number in the block.
        String before = "TGL999999";

        while (true) {
            List<TitleSummary> page = repository.findByPostcodeBefore("SE17PB", before, 10);
            if (page.isEmpty()) {
                break;
            }
            seen.addAll(0, numbers(page));
            before = page.getFirst().titleNumber();
        }

        assertThat(seen).hasSize(25).doesNotHaveDuplicates().isSorted();
        assertThat(seen.getFirst()).isEqualTo("TGL100001");
    }

    @Test
    void countsTheTitlesInAPostcode() {
        assertThat(repository.countByPostcode("SE17PB")).isEqualTo(25);
        assertThat(repository.countByPostcode("CR02QQ")).isEqualTo(2);
        assertThat(repository.countByPostcode("ZZ99ZZ")).isZero();
    }

    @Test
    void returnsAnEmptyListForAPostcodeWithNoTitles() {
        assertThat(repository.findByPostcodeAfter("ZZ99ZZ", "", 10)).isEmpty();
        assertThat(repository.findByPostcodeBefore("ZZ99ZZ", "TGL999999", 10)).isEmpty();
    }
}
