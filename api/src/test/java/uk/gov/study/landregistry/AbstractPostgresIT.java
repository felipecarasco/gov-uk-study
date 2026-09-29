package uk.gov.study.landregistry;

import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

/**
 * Base class for every test that touches the database.
 *
 * The container is static and never stop()ped: it starts once per test JVM and
 * Ryuk (Testcontainers' sidecar container) cleans up at the end. Making it an
 * instance field would start one PostgreSQL per test class, which is slow for
 * no gain.
 *
 * There is no rollback between tests: rows a test writes stay visible to every
 * later test in the run. Never count rows or reuse a literal key across tests.
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
