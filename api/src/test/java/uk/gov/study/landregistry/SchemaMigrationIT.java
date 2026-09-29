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
    void createsTheThreeReadTables() {
        List<String> tables = jdbcClient.sql("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
                .query(String.class)
                .list();

        assertThat(tables).contains("title", "proprietor", "charge");
    }

    @Test
    void titleNumberIsUnique() {
        Integer constraints = jdbcClient.sql("""
                SELECT count(*)
                FROM information_schema.table_constraints
                WHERE table_name = 'title'
                  AND constraint_type = 'UNIQUE'
                """)
                .query(Integer.class)
                .single();

        assertThat(constraints).isGreaterThanOrEqualTo(1);
    }

    @Test
    void hasThePostcodeSearchIndex() {
        List<String> indexes = jdbcClient.sql("""
                SELECT indexname FROM pg_indexes WHERE tablename = 'title'
                """)
                .query(String.class)
                .list();

        assertThat(indexes).contains("idx_title_postcode_normalised");
    }
}
