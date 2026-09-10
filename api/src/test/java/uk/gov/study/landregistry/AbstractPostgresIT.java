package uk.gov.study.landregistry;

import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

/**
 * Base para todo teste que toca o banco.
 *
 * O container é estático e nunca chamado com stop(): sobe uma vez por JVM de teste
 * e o Ryuk (container acessório do Testcontainers) limpa no fim. Torná-lo de
 * instância faria subir um PostgreSQL por classe de teste, o que é lento sem ganho.
 */
@SpringBootTest
public abstract class AbstractPostgresIT {

    static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:18")
                    .withDatabaseName("land_registry")
                    .withUsername("land_registry")
                    .withPassword("land_registry");

    static {
        POSTGRES.start();
    }

    @DynamicPropertySource
    static void datasourceProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }
}
