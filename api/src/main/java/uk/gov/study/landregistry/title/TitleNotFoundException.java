package uk.gov.study.landregistry.title;

public class TitleNotFoundException extends RuntimeException {

    private final String titleNumber;

    public TitleNotFoundException(String titleNumber) {
        super("Nenhum título encontrado com o número " + titleNumber);
        this.titleNumber = titleNumber;
    }

    public String titleNumber() {
        return titleNumber;
    }
}
