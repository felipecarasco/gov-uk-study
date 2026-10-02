package uk.gov.study.landregistry.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import uk.gov.study.landregistry.title.TitleController;
import uk.gov.study.landregistry.title.TitleRepository;
import uk.gov.study.landregistry.title.TitleService;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TitleController.class)
@Import(TitleService.class)
class RequestIdFilterTest {

    private static final String UUID_PATTERN =
            "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$";

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private TitleRepository repository;

    private String responseId(String incoming) throws Exception {
        when(repository.findByTitleNumber(any())).thenReturn(Optional.empty());
        var request = get("/api/v1/titles/ZZ000000");
        if (incoming != null) {
            request.header("X-Request-ID", incoming);
        }
        return mockMvc.perform(request).andReturn().getResponse().getHeader("X-Request-ID");
    }

    @Test
    void echoesAValidIncomingId() throws Exception {
        assertThat(responseId("web-3f2a9c")).isEqualTo("web-3f2a9c");
    }

    @Test
    void createsAnIdWhenThereIsNone() throws Exception {
        assertThat(responseId(null)).matches(UUID_PATTERN);
    }

    // An id is written into every log line, so anything that is not short and
    // plain could forge log lines or fields.
    @ParameterizedTest
    @ValueSource(strings = {"has spaces", "line\nbreak", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"})
    void replacesAnUnsafeId(String unsafe) throws Exception {
        assertThat(responseId(unsafe)).matches(UUID_PATTERN);
    }

    @Test
    void errorResponsesCarryTheIdToo() throws Exception {
        when(repository.findByTitleNumber(any())).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/titles/ZZ000000").header("X-Request-ID", "web-404"))
                .andExpect(status().isNotFound())
                .andExpect(header().string("X-Request-ID", "web-404"));
    }

    @Test
    void doesNotLeakTheIdIntoWhateverRunsNextOnTheThread() throws Exception {
        responseId("web-leak-check");

        assertThat(MDC.get("requestId")).isNull();
    }
}
