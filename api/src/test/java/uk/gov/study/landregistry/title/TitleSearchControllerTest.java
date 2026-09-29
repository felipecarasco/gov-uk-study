package uk.gov.study.landregistry.title;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.hamcrest.Matchers.nullValue;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(TitleController.class)
@Import(TitleService.class)
class TitleSearchControllerTest {

    private static final String VALIDATION_FAILED =
            "https://land-registry.study/problems/validation-failed";

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private TitleRepository repository;

    private static List<TitleSummary> titles(String... numbers) {
        return Arrays.stream(numbers)
                .map(number -> new TitleSummary(number, Tenure.LEASEHOLD,
                        new Address("Flat, Riverside Court", "2 Wharf Lane", "London", "SE1 7PB")))
                .toList();
    }

    @Test
    void theFirstPageHasATotalAndANextCursorButNoPreviousOne() throws Exception {
        // limit=2 asks the repository for 3 rows; a third row means a next page exists.
        when(repository.countByPostcode("SE17PB")).thenReturn(25L);
        when(repository.findByPostcodeAfter("SE17PB", "", 3))
                .thenReturn(titles("TGL100001", "TGL100002", "TGL100003"));

        mockMvc.perform(get("/api/v1/titles").param("postcode", "SE1 7PB").param("limit", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(25))
                .andExpect(jsonPath("$.results.length()").value(2))
                .andExpect(jsonPath("$.results[0].titleNumber").value("TGL100001"))
                .andExpect(jsonPath("$.results[0].tenure").value("LEASEHOLD"))
                .andExpect(jsonPath("$.results[0].address.postcode").value("SE1 7PB"))
                .andExpect(jsonPath("$.nextCursor").value(TitleCursor.after("TGL100002").encode()))
                .andExpect(jsonPath("$.previousCursor").value(nullValue()));
    }

    @Test
    void hasNoNextCursorWhenTheLastPageIsExactlyFull() throws Exception {
        when(repository.findByPostcodeAfter("SE17PB", "", 3)).thenReturn(titles("TGL100001", "TGL100002"));

        mockMvc.perform(get("/api/v1/titles").param("postcode", "SE1 7PB").param("limit", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.results.length()").value(2))
                .andExpect(jsonPath("$.nextCursor").value(nullValue()));
    }

    @Test
    void anAfterCursorNormalisesThePostcodeAndOffersAWayBack() throws Exception {
        when(repository.findByPostcodeAfter(anyString(), anyString(), anyInt()))
                .thenReturn(titles("TGL100021", "TGL100022"));

        mockMvc.perform(get("/api/v1/titles")
                        .param("postcode", "  se1 7pb ")
                        .param("cursor", TitleCursor.after("TGL100020").encode())
                        .param("limit", "5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.previousCursor").value(TitleCursor.before("TGL100021").encode()))
                .andExpect(jsonPath("$.nextCursor").value(nullValue()));

        verify(repository).findByPostcodeAfter("SE17PB", "TGL100020", 6);
        verify(repository, never()).findByPostcodeBefore(anyString(), anyString(), anyInt());
    }

    @Test
    void aBeforeCursorReadsThePageEndingJustBeforeIt() throws Exception {
        // Only two rows come back for a limit of 2: nothing further back, so this
        // is the first page and it gets no previous cursor.
        when(repository.findByPostcodeBefore("SE17PB", "TGL100003", 3))
                .thenReturn(titles("TGL100001", "TGL100002"));

        mockMvc.perform(get("/api/v1/titles")
                        .param("postcode", "SE1 7PB")
                        .param("cursor", TitleCursor.before("TGL100003").encode())
                        .param("limit", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.results[0].titleNumber").value("TGL100001"))
                .andExpect(jsonPath("$.results[1].titleNumber").value("TGL100002"))
                .andExpect(jsonPath("$.previousCursor").value(nullValue()))
                .andExpect(jsonPath("$.nextCursor").value(TitleCursor.after("TGL100002").encode()));
    }

    @Test
    void aBeforeCursorWithMoreBehindKeepsAPreviousCursor() throws Exception {
        // Three rows for a limit of 2: the earliest one only proves there is
        // another page before, so it is dropped from this page.
        when(repository.findByPostcodeBefore("SE17PB", "TGL100004", 3))
                .thenReturn(titles("TGL100001", "TGL100002", "TGL100003"));

        mockMvc.perform(get("/api/v1/titles")
                        .param("postcode", "SE1 7PB")
                        .param("cursor", TitleCursor.before("TGL100004").encode())
                        .param("limit", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.results[0].titleNumber").value("TGL100002"))
                .andExpect(jsonPath("$.results[1].titleNumber").value("TGL100003"))
                .andExpect(jsonPath("$.previousCursor").value(TitleCursor.before("TGL100002").encode()));
    }

    @Test
    void usesAPageSizeOfTwentyByDefault() throws Exception {
        when(repository.findByPostcodeAfter(anyString(), anyString(), anyInt())).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/titles").param("postcode", "CR0 2QQ"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.results.length()").value(0))
                .andExpect(jsonPath("$.nextCursor").value(nullValue()))
                .andExpect(jsonPath("$.previousCursor").value(nullValue()));

        verify(repository).findByPostcodeAfter("CR02QQ", "", 21);
    }

    @Test
    void rejectsAPostcodeInTheWrongFormat() throws Exception {
        mockMvc.perform(get("/api/v1/titles").param("postcode", "12345"))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value(VALIDATION_FAILED))
                .andExpect(jsonPath("$.errors.postcode").value("Enter a full postcode, like CR0 2QQ"));

        verifyNoInteractions(repository);
    }

    @Test
    void rejectsAMissingPostcode() throws Exception {
        mockMvc.perform(get("/api/v1/titles"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(VALIDATION_FAILED))
                .andExpect(jsonPath("$.errors.postcode").exists());
    }

    @ParameterizedTest
    @ValueSource(strings = {"0", "51", "abc"})
    void rejectsALimitOutOfRangeOrNotANumber(String limit) throws Exception {
        mockMvc.perform(get("/api/v1/titles").param("postcode", "CR0 2QQ").param("limit", limit))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(VALIDATION_FAILED))
                .andExpect(jsonPath("$.errors.limit").exists());

        verifyNoInteractions(repository);
    }

    @Test
    void rejectsATamperedCursor() throws Exception {
        mockMvc.perform(get("/api/v1/titles").param("postcode", "CR0 2QQ").param("cursor", "not-a-cursor"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.type").value(VALIDATION_FAILED))
                .andExpect(jsonPath("$.errors.cursor").exists());

        verifyNoInteractions(repository);
    }
}
