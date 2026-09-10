package uk.gov.study.landregistry;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class LandRegistryApplicationTest {

    @Autowired
    private JdbcClient jdbcClient;

    @Test
    void contextoSobeEConectaNoBanco() {
        Integer resultado = jdbcClient.sql("SELECT 1").query(Integer.class).single();
        assertThat(resultado).isEqualTo(1);
    }
}
