package uk.gov.study.landregistry.title;

public class InvalidCursorException extends RuntimeException {

    private final String cursor;

    public InvalidCursorException(String cursor) {
        super("Not a valid search cursor: " + cursor);
        this.cursor = cursor;
    }

    public String cursor() {
        return cursor;
    }
}
