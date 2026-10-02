package uk.gov.study.landregistry.order;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import uk.gov.study.landregistry.title.TitleDetail;
import uk.gov.study.landregistry.title.TitleNotFoundException;
import uk.gov.study.landregistry.title.TitleRepository;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    // £3.00, the fixed fee for an official copy in v1.
    private static final long PRICE_PENCE = 300L;

    private final OrderRepository orders;
    private final OrderReferenceGenerator references;
    private final TitleRepository titles;
    private final OfficialCopyRenderer renderer;

    OrderService(
            OrderRepository orders,
            OrderReferenceGenerator references,
            TitleRepository titles,
            OfficialCopyRenderer renderer) {
        this.orders = orders;
        this.references = references;
        this.titles = titles;
        this.renderer = renderer;
    }

    public RegisterOrder create(CreateOrderRequest request) {
        TitleDetail title = titles.findByTitleNumber(request.titleNumber())
                .orElseThrow(() -> new TitleNotFoundException(request.titleNumber()));

        RegisterOrder order = new RegisterOrder(
                references.next(),
                // The number as stored, not as typed: the lookup ignores case but
                // the foreign key on register_order does not.
                title.titleNumber(),
                request.documentType(),
                request.applicantName(),
                request.applicantEmail(),
                request.applicantAddress(),
                OrderStatus.PENDING_PAYMENT,
                PRICE_PENCE,
                // TIMESTAMPTZ keeps microseconds; truncating here makes the
                // order returned by POST identical to what a later GET reads.
                Instant.now().truncatedTo(ChronoUnit.MICROS),
                // Not paid yet: payment is a separate step.
                null);

        orders.insert(order);

        // Only the reference and what was ordered: never the applicant's name,
        // email or address. The key-value pairs become fields in the JSON logs.
        log.atInfo()
                .addKeyValue("reference", order.reference())
                .addKeyValue("titleNumber", order.titleNumber())
                .addKeyValue("documentType", order.documentType())
                .log("Order {} created for title {}", order.reference(), order.titleNumber());
        return order;
    }

    /**
     * Pays for an order. Paying an order that is already paid changes nothing
     * and returns it as it is, so a double click or a retried request can never
     * take the money twice.
     */
    public RegisterOrder pay(String reference) {
        boolean paidNow = orders.markPaid(reference, Instant.now().truncatedTo(ChronoUnit.MICROS));
        if (paidNow) {
            log.atInfo().addKeyValue("reference", reference).log("Order {} paid", reference);
        }
        // Whether or not this call was the one that paid, the order as stored is
        // the answer; an unknown reference throws OrderNotFoundException here.
        return findByReference(reference);
    }

    public RegisterOrder findByReference(String reference) {
        return orders.findByReference(reference)
                .orElseThrow(() -> new OrderNotFoundException(reference));
    }

    public OfficialCopy document(String reference) {
        RegisterOrder order = findByReference(reference);
        if (order.status() != OrderStatus.PAID) {
            throw new OrderNotPaidException(reference);
        }
        TitleDetail title = titles.findByTitleNumber(order.titleNumber())
                .orElseThrow(() -> new TitleNotFoundException(order.titleNumber()));

        log.atInfo()
                .addKeyValue("reference", order.reference())
                .addKeyValue("documentType", order.documentType())
                .log("Copy issued for order {}", order.reference());

        String kind = order.documentType() == DocumentType.TITLE_REGISTER ? "title-register" : "title-plan";
        return new OfficialCopy(order.reference() + "-" + kind + ".pdf", renderer.render(order, title));
    }
}
