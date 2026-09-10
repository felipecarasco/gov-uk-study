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
                // Sem um server explícito, o springdoc gera um a partir da URL da
                // requisição: "http://localhost:8080" no servidor real, mas
                // "http://localhost" sob MockMvc. Isso torna o spec dependente do
                // ambiente e faz o teste de snapshot falhar sem que o contrato
                // tenha mudado. Uma URL relativa é válida em OpenAPI 3 e é a
                // resposta certa: o contrato descreve caminhos, não onde a API mora.
                .servers(List.of(new Server().url("/").description("Este servidor")))
                .info(new Info()
                .title("Land Registry API")
                .description("""
                        API de consulta ao registro de imóveis. Projeto de estudo — \
                        os dados são fictícios e não representam imóveis reais.""")
                .version("v1")
                .license(new License().name("MIT")));
    }
}
