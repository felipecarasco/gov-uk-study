package uk.gov.study.landregistry.order;

import org.openpdf.text.pdf.PdfReader;
import org.openpdf.text.pdf.parser.PdfTextExtractor;

import java.io.IOException;
import java.io.UncheckedIOException;

/** Reads the text back out of a PDF, so tests can assert on what a person would see. */
final class PdfText {

    private PdfText() {
    }

    static String of(byte[] pdf) {
        try {
            PdfReader reader = new PdfReader(pdf);
            try {
                PdfTextExtractor extractor = new PdfTextExtractor(reader);
                StringBuilder text = new StringBuilder();
                for (int page = 1; page <= reader.getNumberOfPages(); page++) {
                    text.append(extractor.getTextFromPage(page)).append('\n');
                }
                return text.toString();
            } finally {
                reader.close();
            }
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
