package uk.gov.study.landregistry;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.simple.JdbcClient;

import static org.assertj.core.api.Assertions.assertThat;

class LandRegistryApplicationTest extends AbstractPostgresIT {

    @Autowired
    private JdbcClient jdbcClient;

    @Test
    void contextStartsAndReachesTheDatabase() {
        Integer result = jdbcClient.sql("SELECT 1").query(Integer.class).single();
        assertThat(result).isEqualTo(1);
    }
}
