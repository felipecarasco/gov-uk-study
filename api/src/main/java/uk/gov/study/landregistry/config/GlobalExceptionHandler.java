package uk.gov.study.landregistry.config;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import uk.gov.study.landregistry.title.TitleNotFoundException;

import java.net.URI;

/**
 * Traduz exceções de domínio para respostas RFC 9457 (Problem Details).
 *
 * O Flask consome esse formato e o converte no error summary do GDS, então os
 * campos aqui são contrato entre os dois serviços — mudanças precisam ser
 * refletidas no lado Python.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final String BASE_TYPE = "https://land-registry.study/problems/";

    @ExceptionHandler(TitleNotFoundException.class)
    ProblemDetail handleTitleNotFound(TitleNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.NOT_FOUND,
                "No title exists with the number " + ex.titleNumber());

        problem.setType(URI.create(BASE_TYPE + "title-not-found"));
        problem.setTitle("Title not found");
        problem.setProperty("titleNumber", ex.titleNumber());

        return problem;
    }
}
