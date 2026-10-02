package uk.gov.study.landregistry.order;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.webmvc.test.autoconfigure.MockMvcPrint;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import uk.gov.study.landregistry.title.TitleRepository;

import java.time.Instant;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

@WebMvcTest(OrderController.class)
@Import({OrderService.class, OrderReferenceGenerator.class, OfficialCopyRenderer.class})
// MockMvc's own request/response dump (bodies included) is test tooling, not
// application logging: switched off so these tests see only what the app logs.
@AutoConfigureMockMvc(print = MockMvcPrint.NONE)
@ExtendWith(OutputCaptureExtension.class)
class OrderLoggingTest {

    private static final String BODY = """
            {"titleNumber": "SGL123456", "documentType": "TITLE_REGISTER",
             "applicantName": "Alex Morgan Holloway", "applicantEmail": "alex@example.com",
             "applicantAddress": "12 Mallow Gardens, Croydon, CR0 2QQ"}
            """;

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderRepository orderRepository;

    @MockitoBean
    private TitleRepository titleRepository;

    private static RegisterOrder paidOrder() {
        return new RegisterOrder(
                "LR-AAAA2222", "SGL123456", DocumentType.TITLE_REGISTER,
                "Alex Morgan Holloway", "alex@example.com", "12 Mallow Gardens",
                OrderStatus.PAID, 300L,
                Instant.parse("2026-09-10T12:00:00Z"), Instant.parse("2026-09-10T12:05:00Z"));
    }

    private void createOrder() throws Exception {
        when(titleRepository.findByTitleNumber("SGL123456")).thenReturn(Optional.of(TestTitles.example()));
        mockMvc.perform(post("/api/v1/orders")
                .header("X-Request-ID", "web-order-1")
                .contentType(MediaType.APPLICATION_JSON)
                .content(BODY));
    }

    @Test
    void creatingAnOrderIsLoggedUnderTheRequestId(CapturedOutput output) throws Exception {
        createOrder();

        assertThat(output.getOut())
                .containsPattern("\\[web-order-1\\].*Order LR-[0-9A-Z]{8} created for title SGL123456");
    }

    @Test
    void theApplicantsDetailsNeverReachTheLog(CapturedOutput output) throws Exception {
        createOrder();

        assertThat(output.getAll())
                .doesNotContain("Alex Morgan Holloway")
                .doesNotContain("alex@example.com")
                .doesNotContain("12 Mallow Gardens");
    }

    @Test
    void aPaymentIsLoggedOnceEvenWhenRepeated(CapturedOutput output) throws Exception {
        when(orderRepository.markPaid(eq("LR-AAAA2222"), any(Instant.class))).thenReturn(true, false);
        when(orderRepository.findByReference("LR-AAAA2222")).thenReturn(Optional.of(paidOrder()));

        mockMvc.perform(post("/api/v1/orders/LR-AAAA2222/payment"));
        mockMvc.perform(post("/api/v1/orders/LR-AAAA2222/payment"));

        assertThat(output.getOut().split("Order LR-AAAA2222 paid", -1)).hasSize(2);
    }

    @Test
    void issuingACopyIsLogged(CapturedOutput output) throws Exception {
        when(orderRepository.findByReference("LR-AAAA2222")).thenReturn(Optional.of(paidOrder()));
        when(titleRepository.findByTitleNumber("SGL123456")).thenReturn(Optional.of(TestTitles.example()));

        mockMvc.perform(get("/api/v1/orders/LR-AAAA2222/document")
                .accept(MediaType.APPLICATION_PDF, MediaType.APPLICATION_PROBLEM_JSON));

        assertThat(output.getOut()).contains("Copy issued for order LR-AAAA2222");
    }
}
