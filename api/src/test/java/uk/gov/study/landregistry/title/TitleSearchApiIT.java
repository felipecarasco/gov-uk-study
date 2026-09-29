package uk.gov.study.landregistry.title;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import uk.gov.study.landregistry.AbstractPostgresIT;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@AutoConfigureMockMvc
class TitleSearchApiIT extends AbstractPostgresIT {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JsonMapper mapper;

    private JsonNode search(String cursor) throws Exception {
        var request = get("/api/v1/titles").param("postcode", "se1 7pb");
        if (cursor != null) {
            request.param("cursor", cursor);
        }
        String body = mockMvc.perform(request)
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return mapper.readTree(body);
    }

    private static String first(JsonNode page) {
        return page.get("results").get(0).get("titleNumber").asString();
    }

    @Test
    void goesForwardToTheLastPageAndBackToTheFirst() throws Exception {
        JsonNode first = search(null);
        assertThat(first.get("total").asLong()).isEqualTo(25);
        assertThat(first.get("results")).hasSize(20);
        assertThat(first.get("previousCursor").isNull()).isTrue();

        JsonNode last = search(first.get("nextCursor").asString());
        assertThat(last.get("results")).hasSize(5);
        assertThat(first(last)).isEqualTo("TGL100021");
        assertThat(last.get("nextCursor").isNull()).isTrue();

        JsonNode backAgain = search(last.get("previousCursor").asString());
        assertThat(backAgain.get("results")).hasSize(20);
        assertThat(first(backAgain)).isEqualTo("TGL100001");
        assertThat(backAgain.get("previousCursor").isNull()).isTrue();
        assertThat(backAgain.get("nextCursor").isNull()).isFalse();
    }
}
