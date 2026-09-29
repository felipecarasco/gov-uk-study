package uk.gov.study.landregistry.order;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataIntegrityViolationException;
import uk.gov.study.landregistry.AbstractPostgresIT;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class OrderRepositoryIT extends AbstractPostgresIT {

    @Autowired
    private OrderRepository repository;

    private static RegisterOrder order(String reference) {
        return new RegisterOrder(
                reference,
                "SGL123456",
                DocumentType.TITLE_REGISTER,
                "Alex Morgan Holloway",
                "alex@example.com",
                "12 Mallow Gardens, Croydon, CR0 2QQ",
                OrderStatus.PENDING_PAYMENT,
                300L,
                Instant.now().truncatedTo(ChronoUnit.MILLIS),
                null);
    }

    @Test
    void savesAndFindsAnOrder() {
        RegisterOrder original = order("LR-AAAA2222");

        repository.insert(original);

        Optional<RegisterOrder> found = repository.findByReference("LR-AAAA2222");

        assertThat(found).isPresent();
        RegisterOrder o = found.orElseThrow();
        assertThat(o.reference()).isEqualTo("LR-AAAA2222");
        assertThat(o.titleNumber()).isEqualTo("SGL123456");
        assertThat(o.documentType()).isEqualTo(DocumentType.TITLE_REGISTER);
        assertThat(o.applicantName()).isEqualTo("Alex Morgan Holloway");
        assertThat(o.applicantEmail()).isEqualTo("alex@example.com");
        assertThat(o.applicantAddress()).isEqualTo("12 Mallow Gardens, Croydon, CR0 2QQ");
        assertThat(o.status()).isEqualTo(OrderStatus.PENDING_PAYMENT);
        assertThat(o.amountPence()).isEqualTo(300L);
        assertThat(o.createdAt()).isNotNull();
        assertThat(o.paidAt()).isNull();
    }

    @Test
    void returnsEmptyWhenReferenceDoesNotExist() {
        assertThat(repository.findByReference("LR-NOTEXIST")).isEmpty();
    }

    @Test
    void rejectsDuplicateReference() {
        repository.insert(order("LR-BBBB3333"));

        assertThatThrownBy(() -> repository.insert(order("LR-BBBB3333")))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void rejectsOrderForUnknownTitle() {
        RegisterOrder orphan = new RegisterOrder(
                "LR-CCCC4444", "ZZ000000", DocumentType.TITLE_PLAN,
                "Sam Okonkwo", "sam@example.com", "3 Bramber Lane",
                OrderStatus.PENDING_PAYMENT, 300L, Instant.now(), null);

        assertThatThrownBy(() -> repository.insert(orphan))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void rejectsZeroOrNegativeAmount() {
        RegisterOrder free = new RegisterOrder(
                "LR-DDDD5555", "SGL123456", DocumentType.TITLE_REGISTER,
                "Sam Okonkwo", "sam@example.com", "3 Bramber Lane",
                OrderStatus.PENDING_PAYMENT, 0L, Instant.now(), null);

        assertThatThrownBy(() -> repository.insert(free))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void marksAPendingOrderAsPaid() {
        repository.insert(order("LR-EEEE6666"));
        Instant paidAt = Instant.now().truncatedTo(ChronoUnit.MICROS);

        assertThat(repository.markPaid("LR-EEEE6666", paidAt)).isTrue();

        RegisterOrder paid = repository.findByReference("LR-EEEE6666").orElseThrow();
        assertThat(paid.status()).isEqualTo(OrderStatus.PAID);
        assertThat(paid.paidAt()).isEqualTo(paidAt);
    }

    @Test
    void doesNotPayAnOrderTwice() {
        repository.insert(order("LR-FFFF7777"));
        Instant first = Instant.now().truncatedTo(ChronoUnit.MICROS);

        assertThat(repository.markPaid("LR-FFFF7777", first)).isTrue();
        assertThat(repository.markPaid("LR-FFFF7777", first.plusSeconds(60))).isFalse();

        assertThat(repository.findByReference("LR-FFFF7777").orElseThrow().paidAt()).isEqualTo(first);
    }

    @Test
    void doesNotPayAnUnknownOrder() {
        assertThat(repository.markPaid("LR-GGGG8888", Instant.now())).isFalse();
    }
}
