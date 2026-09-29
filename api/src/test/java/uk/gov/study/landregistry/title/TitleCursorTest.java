package uk.gov.study.landregistry.title;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class TitleCursorTest {

    @Test
    void decodesWhatItEncoded() {
        TitleCursor cursor = TitleCursor.after("SGL123456");

        assertThat(TitleCursor.decode(cursor.encode())).isEqualTo(cursor);
    }

    @Test
    void keepsTheDirection() {
        TitleCursor decoded = TitleCursor.decode(TitleCursor.before("TGL100021").encode());

        assertThat(decoded.direction()).isEqualTo(TitleCursor.Direction.BEFORE);
        assertThat(decoded.titleNumber()).isEqualTo("TGL100021");
    }

    @Test
    void canGoInAUrlAsItIs() {
        // No +, / or = padding: the cursor travels in a query string untouched.
        assertThat(TitleCursor.after("TGL100025").encode()).matches("^[A-Za-z0-9_-]+$");
    }

    // "%%%" is not Base64. "not-a-cursor" is Base64 of meaningless bytes. ""
    // decodes to nothing. "U0dMMTIzNDU2" is "SGL123456" with no direction, and
    // "WDpTR0wxMjM0NTY" is "X:SGL123456", an unknown direction.
    @ParameterizedTest
    @ValueSource(strings = {"%%%", "not-a-cursor", "", "U0dMMTIzNDU2", "WDpTR0wxMjM0NTY"})
    void rejectsAnythingEncodeDidNotProduce(String cursor) {
        assertThatThrownBy(() -> TitleCursor.decode(cursor))
                .isInstanceOf(InvalidCursorException.class);
    }
}
