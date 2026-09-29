package uk.gov.study.landregistry.title;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(TitleController.class)
@Import(TitleService.class)
class TitleControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private TitleRepository repository;

    private static TitleDetail example() {
        return new TitleDetail(
                "SGL123456",
                Tenure.FREEHOLD,
                "Title absolute",
                new Address("12 Mallow Gardens", null, "Croydon", "CR0 2QQ"),
                42_500_000L,
                LocalDate.of(2019, 6, 14),
                List.of(new Proprietor("ALEX MORGAN HOLLOWAY",
                        "12 Mallow Gardens, Croydon, CR0 2QQ")),
                List.of(new Charge("NORTHWOOD BUILDING SOCIETY",
                        LocalDate.of(2019, 6, 14), 34_000_000L)));
    }

    @Test
    void returnsTheTitleAsJson() throws Exception {
        when(repository.findByTitleNumber("SGL123456")).thenReturn(Optional.of(example()));

        mockMvc.perform(get("/api/v1/titles/SGL123456").accept("application/json"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith("application/json"))
                .andExpect(jsonPath("$.titleNumber").value("SGL123456"))
                .andExpect(jsonPath("$.tenure").value("FREEHOLD"))
                .andExpect(jsonPath("$.address.postcode").value("CR0 2QQ"))
                .andExpect(jsonPath("$.address.line2").doesNotExist())
                .andExpect(jsonPath("$.pricePaidPence").value(42500000))
                .andExpect(jsonPath("$.pricePaidDate").value("2019-06-14"))
                .andExpect(jsonPath("$.proprietors.length()").value(1))
                .andExpect(jsonPath("$.proprietors[0].name").value("ALEX MORGAN HOLLOWAY"))
                .andExpect(jsonPath("$.charges[0].amountPence").value(34000000));
    }

    @Test
    void acceptsALowerCaseTitleNumber() throws Exception {
        when(repository.findByTitleNumber(any())).thenReturn(Optional.of(example()));

        mockMvc.perform(get("/api/v1/titles/sgl123456").accept("application/json"))
                .andExpect(status().isOk());
    }

    @Test
    void returnsAProblemDetailWhenTheTitleDoesNotExist() throws Exception {
        when(repository.findByTitleNumber("ZZ000000")).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/titles/ZZ000000").accept("application/json"))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.type").value("https://land-registry.study/problems/title-not-found"))
                .andExpect(jsonPath("$.title").value("Title not found"))
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.detail").value("No title exists with the number ZZ000000"))
                .andExpect(jsonPath("$.instance").value("/api/v1/titles/ZZ000000"))
                .andExpect(jsonPath("$.titleNumber").value("ZZ000000"));
    }
}
