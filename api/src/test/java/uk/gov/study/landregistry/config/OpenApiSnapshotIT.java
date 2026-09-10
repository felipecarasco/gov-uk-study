package uk.gov.study.landregistry.config;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import uk.gov.study.landregistry.AbstractPostgresIT;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

/**
 * Falha se o contrato REST mudar sem que docs/openapi.json seja atualizado.
 *
 * Para atualizar o snapshot depois de uma mudança intencional: make openapi
 */
@AutoConfigureMockMvc
class OpenApiSnapshotIT extends AbstractPostgresIT {

    private static final Path SNAPSHOT = Path.of("..", "docs", "openapi.json");

    @Autowired
    private MockMvc mockMvc;

    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void contratoBateComOSnapshotVersionado() throws Exception {
        String atual = mockMvc.perform(get("/v3/api-docs"))
                .andReturn().getResponse().getContentAsString();

        assertThat(SNAPSHOT)
                .as("docs/openapi.json não existe — rode 'make openapi' para criá-lo")
                .exists();

        JsonNode esperado = mapper.readTree(Files.readString(SNAPSHOT));
        JsonNode gerado = mapper.readTree(atual);

        assertThat(gerado)
                .as("""
                        O contrato REST mudou mas docs/openapi.json não foi atualizado.
                        Se a mudança for intencional, rode: make openapi
                        e inclua o arquivo no mesmo commit da mudança.""")
                .isEqualTo(esperado);
    }
}
