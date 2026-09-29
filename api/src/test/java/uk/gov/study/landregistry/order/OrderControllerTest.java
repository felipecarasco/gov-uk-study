package uk.gov.study.landregistry.order;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.json.JsonMapper;
import uk.gov.study.landregistry.title.TitleRepository;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import static org.hamcrest.Matchers.matchesPattern;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(OrderController.class)
@Import({OrderService.class, OrderReferenceGenerator.class})
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    // Jackson 3 (tools.jackson), which is what Spring Boot 4 registers. The
    // Jackson 2 ObjectMapper also compiles, because springdoc drags it onto the
    // classpath, but there is no bean of that type and the context fails to start.
    @Autowired
    private JsonMapper mapper;

    @MockitoBean
    private OrderRepository orderRepository;

    @MockitoBean
    private TitleRepository titleRepository;

    private static final Map<String, Object> VALID_BODY = Map.of(
            "titleNumber", "SGL123456",
            "documentType", "TITLE_REGISTER",
            "applicantName", "Alex Morgan Holloway",
            "applicantEmail", "alex@example.com",
            "applicantAddress", "12 Mallow Gardens, Croydon, CR0 2QQ");

    private String json(Map<String, Object> body) {
        return mapper.writeValueAsString(body);
    }

    @Test
    void createsTheOrderAndReturns201() throws Exception {
        when(titleRepository.findByTitleNumber("SGL123456"))
                .thenReturn(Optional.of(TestTitles.example()));

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(VALID_BODY)))
                .andExpect(status().isCreated())
                .andExpect(header().exists("Location"))
                .andExpect(jsonPath("$.reference").value(matchesPattern("^LR-[0-9A-Z]{8}$")))
                .andExpect(jsonPath("$.titleNumber").value("SGL123456"))
                .andExpect(jsonPath("$.documentType").value("TITLE_REGISTER"))
                .andExpect(jsonPath("$.status").value("PENDING_PAYMENT"))
                .andExpect(jsonPath("$.amountPence").value(300))
                .andExpect(jsonPath("$.applicantName").value("Alex Morgan Holloway"))
                .andExpect(jsonPath("$.createdAt").exists());
    }

    @Test
    void storesTheCanonicalTitleNumberWhateverTheCaseTyped() throws Exception {
        // The title lookup ignores case, but the foreign key does not: storing
        // what the user typed would violate it and turn a valid order into a 500.
        when(titleRepository.findByTitleNumber("sgl123456"))
                .thenReturn(Optional.of(TestTitles.example()));

        Map<String, Object> lowerCase = new HashMap<>(VALID_BODY);
        lowerCase.put("titleNumber", "sgl123456");

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(lowerCase)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.titleNumber").value("SGL123456"));
    }

    @Test
    void rejectsAnOrderForAnUnknownTitle() throws Exception {
        when(titleRepository.findByTitleNumber(any())).thenReturn(Optional.empty());

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(VALID_BODY)))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value("https://land-registry.study/problems/title-not-found"));
    }

    @Test
    void rejectsABodyWithoutAName() throws Exception {
        when(titleRepository.findByTitleNumber(any()))
                .thenReturn(Optional.of(TestTitles.example()));

        Map<String, Object> noName = new HashMap<>(VALID_BODY);
        noName.put("applicantName", "");

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(noName)))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value("https://land-registry.study/problems/validation-failed"))
                .andExpect(jsonPath("$.errors.applicantName").exists());
    }

    @Test
    void rejectsAMalformedEmail() throws Exception {
        when(titleRepository.findByTitleNumber(any()))
                .thenReturn(Optional.of(TestTitles.example()));

        Map<String, Object> badEmail = new HashMap<>(VALID_BODY);
        badEmail.put("applicantEmail", "not-an-email");

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(badEmail)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors.applicantEmail").exists());
    }

    @Test
    void returnsTheOrderByReference() throws Exception {
        RegisterOrder existing = new RegisterOrder(
                "LR-AAAA2222", "SGL123456", DocumentType.TITLE_PLAN,
                "Sam Okonkwo", "sam@example.com", "3 Bramber Lane",
                OrderStatus.PENDING_PAYMENT, 300L, Instant.parse("2026-09-10T12:00:00Z"));

        when(orderRepository.findByReference("LR-AAAA2222")).thenReturn(Optional.of(existing));

        mockMvc.perform(get("/api/v1/orders/LR-AAAA2222").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.reference").value("LR-AAAA2222"))
                .andExpect(jsonPath("$.documentType").value("TITLE_PLAN"))
                .andExpect(jsonPath("$.status").value("PENDING_PAYMENT"));
    }

    @Test
    void returnsAProblemDetailWhenTheReferenceDoesNotExist() throws Exception {
        when(orderRepository.findByReference(any())).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/orders/LR-NOTEXIST").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value("https://land-registry.study/problems/order-not-found"))
                .andExpect(jsonPath("$.reference").value("LR-NOTEXIST"));
    }
}
