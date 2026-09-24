package uk.gov.study.landregistry.order;

import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

import static org.assertj.core.api.Assertions.assertThat;

class OrderReferenceGeneratorTest {

    private static final Pattern FORMAT = Pattern.compile("^LR-[0-9A-Z]{8}$");

    private final OrderReferenceGenerator generator = new OrderReferenceGenerator();

    @Test
    void generatesTheExpectedFormat() {
        assertThat(generator.next()).matches(FORMAT);
    }

    @Test
    void doesNotUseAmbiguousCharacters() {
        // References are read out over the phone and typed by hand. 0/O and
        // 1/I/L get confused, so they are left out of the alphabet.
        for (int i = 0; i < 500; i++) {
            String suffix = generator.next().substring(3);
            assertThat(suffix).doesNotContain("0")
                              .doesNotContain("O")
                              .doesNotContain("1")
                              .doesNotContain("I")
                              .doesNotContain("L");
        }
    }

    @Test
    void doesNotRepeatAtAReasonableVolume() {
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < 10_000; i++) {
            seen.add(generator.next());
        }
        assertThat(seen).hasSize(10_000);
    }
}
