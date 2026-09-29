package uk.gov.study.landregistry.title;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Opaque position in a postcode search: a title number and which way to read
 * from it, in URL-safe Base64.
 *
 * Clients pass it back untouched and never build one. Keeping it opaque lets
 * the sort key change later (say, to title number plus id) without breaking
 * anyone who stored a link.
 */
public record TitleCursor(Direction direction, String titleNumber) {

    public enum Direction {
        /** The page that starts just after the title. */
        AFTER,
        /** The page that ends just before the title. */
        BEFORE
    }

    private static final Pattern PAYLOAD = Pattern.compile("^([AB]):([A-Z]{2,3}\\d{4,6})$");

    public static TitleCursor after(String titleNumber) {
        return new TitleCursor(Direction.AFTER, titleNumber);
    }

    public static TitleCursor before(String titleNumber) {
        return new TitleCursor(Direction.BEFORE, titleNumber);
    }

    public String encode() {
        String payload = (direction == Direction.AFTER ? "A" : "B") + ":" + titleNumber;
        return Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(payload.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * @throws InvalidCursorException if the value did not come from encode(). A
     *     decoded value that is not a direction and a title number is rejected
     *     too: it would still compare fine in SQL and silently return a wrong page.
     */
    public static TitleCursor decode(String cursor) {
        String payload;
        try {
            payload = new String(Base64.getUrlDecoder().decode(cursor), StandardCharsets.UTF_8);
        } catch (IllegalArgumentException notBase64) {
            throw new InvalidCursorException(cursor);
        }
        Matcher parts = PAYLOAD.matcher(payload);
        if (!parts.matches()) {
            throw new InvalidCursorException(cursor);
        }
        Direction direction = parts.group(1).equals("A") ? Direction.AFTER : Direction.BEFORE;
        return new TitleCursor(direction, parts.group(2));
    }
}
