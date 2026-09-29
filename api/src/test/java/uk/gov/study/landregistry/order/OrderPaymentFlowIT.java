package uk.gov.study.landregistry.order;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import uk.gov.study.landregistry.AbstractPostgresIT;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@AutoConfigureMockMvc
class OrderPaymentFlowIT extends AbstractPostgresIT {

    private static final MediaType[] PDF_OR_PROBLEM =
            {MediaType.APPLICATION_PDF, MediaType.APPLICATION_PROBLEM_JSON};

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JsonMapper mapper;

    private JsonNode json(String body) {
        return mapper.readTree(body);
    }

    @Test
    void createsPaysTwiceAndDownloadsTheCopy() throws Exception {
        String created = mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"titleNumber": "SGL123457", "documentType": "TITLE_REGISTER",
                                 "applicantName": "Jamie Patel", "applicantEmail": "jamie@example.com",
                                 "applicantAddress": "Flat 4, Hazelmere Court"}
                                """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        String reference = json(created).get("reference").asString();

        mockMvc.perform(get("/api/v1/orders/{ref}/document", reference).accept(PDF_OR_PROBLEM))
                .andExpect(status().isConflict());

        JsonNode firstPayment = json(mockMvc.perform(post("/api/v1/orders/{ref}/payment", reference))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString());
        JsonNode secondPayment = json(mockMvc.perform(post("/api/v1/orders/{ref}/payment", reference))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString());

        assertThat(firstPayment.get("status").asString()).isEqualTo("PAID");
        assertThat(secondPayment.get("paidAt").asString()).isEqualTo(firstPayment.get("paidAt").asString());

        byte[] pdf = mockMvc.perform(get("/api/v1/orders/{ref}/document", reference).accept(PDF_OR_PROBLEM))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsByteArray();

        assertThat(PdfText.of(pdf))
                .contains("SGL123457")
                .contains(reference)
                .contains("JAMIE PATEL")
                .contains("CALDER BANK PLC");
    }
}
