package uk.gov.study.landregistry;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.simple.JdbcClient;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class SchemaMigrationIT extends AbstractPostgresIT {

    @Autowired
    private JdbcClient jdbcClient;

    @Test
    void criaAsTresTabelasDeLeitura() {
        List<String> tabelas = jdbcClient.sql("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
                .query(String.class)
                .list();

        assertThat(tabelas).contains("title", "proprietor", "charge");
    }

    @Test
    void titleNumberEhUnico() {
        Integer restricoes = jdbcClient.sql("""
                SELECT count(*)
                FROM information_schema.table_constraints
                WHERE table_name = 'title'
                  AND constraint_type = 'UNIQUE'
                """)
                .query(Integer.class)
                .single();

        assertThat(restricoes).isGreaterThanOrEqualTo(1);
    }

    @Test
    void existeIndiceDeBuscaPorPostcode() {
        List<String> indices = jdbcClient.sql("""
                SELECT indexname FROM pg_indexes WHERE tablename = 'title'
                """)
                .query(String.class)
                .list();

        assertThat(indices).contains("idx_title_postcode_normalised");
    }
}
