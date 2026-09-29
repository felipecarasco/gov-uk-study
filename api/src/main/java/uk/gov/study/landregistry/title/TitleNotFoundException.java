package uk.gov.study.landregistry.title;

public class TitleNotFoundException extends RuntimeException {

    private final String titleNumber;

    public TitleNotFoundException(String titleNumber) {
        super("No title found with the number " + titleNumber);
        this.titleNumber = titleNumber;
    }

    public String titleNumber() {
        return titleNumber;
    }
}
