package uk.gov.study.landregistry.order;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import uk.gov.study.landregistry.title.Address;
import uk.gov.study.landregistry.title.Charge;
import uk.gov.study.landregistry.title.Proprietor;
import uk.gov.study.landregistry.title.Tenure;
import uk.gov.study.landregistry.title.TitleDetail;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class OfficialCopyRendererTest {

    private final OfficialCopyRenderer renderer = new OfficialCopyRenderer();

    private static RegisterOrder paidOrder(DocumentType type) {
        return new RegisterOrder(
                "LR-7K2M9XQ4", "SGL123456", type,
                "Alex Morgan Holloway", "alex@example.com", "12 Mallow Gardens",
                OrderStatus.PAID, 300L,
                Instant.parse("2026-09-29T13:30:00Z"),
                // 14:32 in London: British Summer Time is UTC+1 in September.
                Instant.parse("2026-09-29T13:32:00Z"));
    }

    private static TitleDetail titleWith(List<Charge> charges) {
        return new TitleDetail(
                "SGL123456", Tenure.FREEHOLD, "Title absolute",
                new Address("12 Mallow Gardens", null, "Croydon", "CR0 2QQ"),
                42_500_000L, LocalDate.of(2019, 6, 14),
                List.of(new Proprietor("ALEX MORGAN HOLLOWAY", "12 Mallow Gardens, Croydon, CR0 2QQ")),
                charges);
    }

    private static final List<Charge> ONE_CHARGE =
            List.of(new Charge("NORTHWOOD BUILDING SOCIETY", LocalDate.of(2019, 6, 14), 34_000_000L));

    private String register() {
        return PdfText.of(renderer.render(paidOrder(DocumentType.TITLE_REGISTER), titleWith(ONE_CHARGE)));
    }

    @Test
    void producesAPdf() {
        byte[] pdf = renderer.render(paidOrder(DocumentType.TITLE_REGISTER), titleWith(ONE_CHARGE));

        assertThat(new String(pdf, 0, 5, StandardCharsets.US_ASCII)).isEqualTo("%PDF-");
    }

    @Test
    void theRegisterHasItsThreeParts() {
        assertThat(register())
                .contains("A: Property register")
                .contains("B: Proprietorship register")
                .contains("C: Charges register");
    }

    @Test
    void theRegisterShowsTheTitleTheReferenceAndWhenItWasIssued() {
        assertThat(register())
                .contains("SGL123456")
                .contains("LR-7K2M9XQ4")
                .contains("29 September 2026 at 2:32pm");
    }

    @Test
    void theRegisterListsTheProprietorsThePriceAndTheCharges() {
        assertThat(register())
                .contains("12 Mallow Gardens, Croydon, CR0 2QQ")
                .contains("Freehold")
                .contains("Title absolute")
                .contains("ALEX MORGAN HOLLOWAY")
                .contains("£425,000.00")
                .contains("NORTHWOOD BUILDING SOCIETY")
                .contains("£340,000.00");
    }

    @Test
    void aRegisterWithoutChargesSaysSo() {
        String text = PdfText.of(renderer.render(paidOrder(DocumentType.TITLE_REGISTER), titleWith(List.of())));

        assertThat(text).contains("No charges are registered against this title.");
    }

    @Test
    void thePlanExplainsThereIsNoDrawing() {
        String text = PdfText.of(renderer.render(paidOrder(DocumentType.TITLE_PLAN), titleWith(ONE_CHARGE)));

        assertThat(text)
                .contains("Copy of title plan")
                .contains("SGL123456")
                .contains("no plan drawing")
                .doesNotContain("C: Charges register");
    }

    @ParameterizedTest
    @EnumSource(DocumentType.class)
    void everyCopySaysItIsNotAnOfficialDocument(DocumentType type) {
        String text = PdfText.of(renderer.render(paidOrder(type), titleWith(ONE_CHARGE)));

        assertThat(text).contains("not an official document");
    }
}
