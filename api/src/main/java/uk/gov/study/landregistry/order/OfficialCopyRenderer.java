package uk.gov.study.landregistry.order;

import org.openpdf.text.Document;
import org.openpdf.text.Font;
import org.openpdf.text.FontFactory;
import org.openpdf.text.PageSize;
import org.openpdf.text.Paragraph;
import org.openpdf.text.pdf.PdfWriter;
import org.springframework.stereotype.Component;
import uk.gov.study.landregistry.title.Address;
import uk.gov.study.landregistry.title.Charge;
import uk.gov.study.landregistry.title.Proprietor;
import uk.gov.study.landregistry.title.TitleDetail;

import java.io.ByteArrayOutputStream;
import java.text.NumberFormat;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Draws the PDF copy of a title's register or plan.
 *
 * The register follows the three parts of a real register of title: A (the
 * property), B (who owns it) and C (charges against it). Every copy says it
 * comes from a study project: the data is fictitious, and a PDF that looks like
 * an official copy must not be mistaken for one.
 */
@Component
public class OfficialCopyRenderer {

    private static final ZoneId LONDON = ZoneId.of("Europe/London");
    private static final DateTimeFormatter DATE = DateTimeFormatter.ofPattern("d MMMM yyyy", Locale.UK);
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("h:mma", Locale.UK);

    private static final Font TITLE = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 18);
    private static final Font HEADING = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 13);
    private static final Font BODY = FontFactory.getFont(FontFactory.HELVETICA, 11);
    private static final Font NOTE = FontFactory.getFont(FontFactory.HELVETICA_OBLIQUE, 9);

    private static final String NOT_OFFICIAL =
            "Produced by a study project: this is not an official document, and all data in it is fictitious.";

    public byte[] render(RegisterOrder order, TitleDetail title) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        Document document = new Document(PageSize.A4, 56, 56, 56, 56);
        PdfWriter.getInstance(document, out);
        document.open();

        if (order.documentType() == DocumentType.TITLE_REGISTER) {
            document.addTitle("Copy of register of title " + title.titleNumber());
            writeHeader(document, "Copy of register of title", order, title);
            writeRegister(document, title);
        } else {
            document.addTitle("Copy of title plan " + title.titleNumber());
            writeHeader(document, "Copy of title plan", order, title);
            writePlan(document, title);
        }

        document.add(spaced(new Paragraph(NOT_OFFICIAL, NOTE)));
        document.close();
        return out.toByteArray();
    }

    private void writeHeader(Document document, String heading, RegisterOrder order, TitleDetail title) {
        document.add(new Paragraph(heading, TITLE));
        document.add(spaced(new Paragraph("Title number: " + title.titleNumber(), BODY)));
        document.add(new Paragraph("Order reference: " + order.reference(), BODY));
        document.add(new Paragraph("Issued on " + issuedOn(order.paidAt()), BODY));
    }

    private void writeRegister(Document document, TitleDetail title) {
        section(document, "A: Property register");
        line(document, "Property: " + address(title.address()));
        line(document, "Tenure: " + capitalise(title.tenure().name()));

        section(document, "B: Proprietorship register");
        line(document, "Class of title: " + title.classOfTitle());
        for (Proprietor proprietor : title.proprietors()) {
            line(document, "Registered proprietor: " + proprietor.name() + ", " + proprietor.address());
        }
        if (title.pricePaidPence() != null) {
            line(document, "Price paid: " + pounds(title.pricePaidPence()) + " on " + date(title.pricePaidDate()));
        }

        section(document, "C: Charges register");
        if (title.charges().isEmpty()) {
            line(document, "No charges are registered against this title.");
        }
        for (Charge charge : title.charges()) {
            line(document, "Registered charge dated " + date(charge.chargeDate())
                    + " in favour of " + charge.lender()
                    + ", securing " + pounds(charge.amountPence()) + ".");
        }
    }

    private void writePlan(Document document, TitleDetail title) {
        section(document, "Property");
        line(document, address(title.address()));
        line(document, "This study service does not hold boundary data, so no plan drawing is included.");
    }

    private static void section(Document document, String heading) {
        document.add(spaced(new Paragraph(heading, HEADING)));
    }

    private static void line(Document document, String text) {
        document.add(new Paragraph(text, BODY));
    }

    private static Paragraph spaced(Paragraph paragraph) {
        paragraph.setSpacingBefore(12);
        return paragraph;
    }

    private static String address(Address address) {
        return Stream.of(address.line1(), address.line2(), address.town(), address.postcode())
                .filter(part -> part != null && !part.isBlank())
                .collect(Collectors.joining(", "));
    }

    private static String issuedOn(Instant paidAt) {
        var local = paidAt.atZone(LONDON);
        return DATE.format(local) + " at " + TIME.format(local);
    }

    private static String date(LocalDate date) {
        return DATE.format(date);
    }

    // Integer pence to pounds for display only; money is never a double in the model.
    private static String pounds(long pence) {
        return NumberFormat.getCurrencyInstance(Locale.UK).format(pence / 100.0);
    }

    private static String capitalise(String value) {
        return value.charAt(0) + value.substring(1).toLowerCase(Locale.UK);
    }
}
