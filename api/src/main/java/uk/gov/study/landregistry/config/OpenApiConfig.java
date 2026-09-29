package uk.gov.study.landregistry.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI landRegistryOpenApi() {
        return new OpenAPI()
                // Without an explicit server, springdoc derives one from the
                // request URL: "http://localhost:8080" on the real server but
                // "http://localhost" under MockMvc. That makes the spec depend on
                // the environment and fails the snapshot test without the contract
                // changing. A relative URL is valid in OpenAPI 3 and is the right
                // answer: the contract describes paths, not where the API lives.
                .servers(List.of(new Server().url("/").description("This server")))
                .info(new Info()
                .title("Land Registry API")
                .description("""
                        Land register lookup API. Study project: \
                        the data is fictitious and does not describe real properties.""")
                .version("v1")
                .license(new License().name("MIT")));
    }
}
