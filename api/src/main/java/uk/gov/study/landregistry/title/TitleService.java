package uk.gov.study.landregistry.title;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TitleService {

    private final TitleRepository repository;

    TitleService(TitleRepository repository) {
        this.repository = repository;
    }

    public TitleDetail findByTitleNumber(String titleNumber) {
        return repository.findByTitleNumber(titleNumber)
                .orElseThrow(() -> new TitleNotFoundException(titleNumber));
    }

    public TitleSearchPage search(String postcode, String cursor, int limit) {
        String normalised = TitleRepository.normalisePostcode(postcode);
        TitleCursor position = (cursor == null) ? null : TitleCursor.decode(cursor);
        long total = repository.countByPostcode(normalised);

        // Each read asks for one row more than the page needs. If it comes back,
        // there is another page in that direction, and no extra query is needed
        // to know it. It also means a page that is exactly full never links to
        // an empty page.
        List<TitleSummary> page;
        boolean hasPrevious;
        boolean hasNext;

        if (position != null && position.direction() == TitleCursor.Direction.BEFORE) {
            List<TitleSummary> rows =
                    repository.findByPostcodeBefore(normalised, position.titleNumber(), limit + 1);
            hasPrevious = rows.size() > limit;
            page = hasPrevious ? rows.subList(1, rows.size()) : rows;
            // The cursor's own title comes after this page.
            hasNext = true;
        } else {
            String after = (position == null) ? "" : position.titleNumber();
            List<TitleSummary> rows = repository.findByPostcodeAfter(normalised, after, limit + 1);
            hasNext = rows.size() > limit;
            page = hasNext ? rows.subList(0, limit) : rows;
            // Only the first page is reached without a cursor.
            hasPrevious = position != null;
        }

        if (page.isEmpty()) {
            return new TitleSearchPage(List.of(), total, null, null);
        }
        return new TitleSearchPage(
                List.copyOf(page),
                total,
                hasPrevious ? TitleCursor.before(page.getFirst().titleNumber()).encode() : null,
                hasNext ? TitleCursor.after(page.getLast().titleNumber()).encode() : null);
    }
}
