package uk.gov.study.landregistry.order;

public class OrderNotFoundException extends RuntimeException {

    private final String reference;

    public OrderNotFoundException(String reference) {
        super("No order exists with the reference " + reference);
        this.reference = reference;
    }

    public String reference() {
        return reference;
    }
}
