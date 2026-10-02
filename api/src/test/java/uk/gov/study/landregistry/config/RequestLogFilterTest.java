package uk.gov.study.landregistry.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.webmvc.test.autoconfigure.MockMvcPrint;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import uk.gov.study.landregistry.title.TitleController;
import uk.gov.study.landregistry.title.TitleRepository;
import uk.gov.study.landregistry.title.TitleService;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

@WebMvcTest(TitleController.class)
@Import(TitleService.class)
// MockMvc's own request dump is test tooling; these tests look only at what the app logs.
@AutoConfigureMockMvc(print = MockMvcPrint.NONE)
@ExtendWith(OutputCaptureExtension.class)
class RequestLogFilterTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private TitleRepository repository;

    @Test
    void everyRequestGetsOneLineWithItsIdMethodPathAndStatus(CapturedOutput output) throws Exception {
        when(repository.findByTitleNumber(any())).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/titles/ZZ000000").header("X-Request-ID", "web-trace-1"));

        assertThat(output.getOut()).containsPattern("\\[web-trace-1\\].*GET /api/v1/titles/ZZ000000 404 \\d+ms");
    }

    @Test
    void theQueryStringIsLeftOut(CapturedOutput output) throws Exception {
        when(repository.findByPostcodeAfter(anyString(), anyString(), anyInt())).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/titles").param("postcode", "CR0 2QQ"));

        assertThat(output.getOut())
                .containsPattern("GET /api/v1/titles 200 \\d+ms")
                .doesNotContain("CR0")
                .doesNotContain("postcode=");
    }

    @Test
    void healthChecksAreNotLogged(CapturedOutput output) throws Exception {
        // Docker and OpenShift poll this every few seconds: logging it would bury
        // everything else.
        mockMvc.perform(get("/actuator/health"));

        assertThat(output.getOut()).doesNotContain("/actuator/health");
    }
}
