package uk.gov.study.landregistry.order;

public class OrderNotPaidException extends RuntimeException {

    private final String reference;

    public OrderNotPaidException(String reference) {
        super("Order " + reference + " has not been paid");
        this.reference = reference;
    }

    public String reference() {
        return reference;
    }
}
