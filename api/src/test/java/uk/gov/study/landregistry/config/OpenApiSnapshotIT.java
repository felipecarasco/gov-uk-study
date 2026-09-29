package uk.gov.study.landregistry.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import uk.gov.study.landregistry.AbstractPostgresIT;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

/**
 * Fails if the REST contract changes without api/openapi.json being updated.
 *
 * To update the snapshot after an intended change: make openapi
 */
@AutoConfigureMockMvc
class OpenApiSnapshotIT extends AbstractPostgresIT {

    // Tests run with api/ as the working directory.
    private static final Path SNAPSHOT = Path.of("openapi.json");

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JsonMapper mapper;

    @Test
    void contractMatchesTheCommittedSnapshot() throws Exception {
        String current = mockMvc.perform(get("/v3/api-docs"))
                .andReturn().getResponse().getContentAsString();

        assertThat(SNAPSHOT)
                .as("api/openapi.json does not exist; run 'make openapi' to create it")
                .exists();

        JsonNode expected = mapper.readTree(Files.readString(SNAPSHOT));
        JsonNode generated = mapper.readTree(current);

        assertThat(generated)
                .as("""
                        The REST contract changed but api/openapi.json was not updated.
                        If the change is intended, run: make openapi
                        and commit the file together with the change.""")
                .isEqualTo(expected);
    }
}
