package uk.gov.study.landregistry.title;

import java.util.List;

/**
 * One page of a postcode search. A cursor is null when there is no page in
 * that direction: previousCursor on the first page, nextCursor on the last.
 */
public record TitleSearchPage(
        List<TitleSummary> results,
        long total,
        String previousCursor,
        String nextCursor) {
}
