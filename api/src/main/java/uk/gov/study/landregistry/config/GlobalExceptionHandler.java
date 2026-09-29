package uk.gov.study.landregistry.config;

import org.springframework.beans.TypeMismatchException;
import org.springframework.context.MessageSourceResolvable;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.validation.method.ParameterValidationResult;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;
import uk.gov.study.landregistry.order.OrderNotFoundException;
import uk.gov.study.landregistry.title.InvalidCursorException;
import uk.gov.study.landregistry.title.TitleNotFoundException;

import java.net.URI;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Turns domain exceptions into RFC 9457 (Problem Details) responses.
 *
 * Flask consumes this format and turns it into the GOV.UK error summary, so the
 * fields here are a contract between the two services: changes must be mirrored
 * on the Python side.
 *
 * Extends ResponseEntityExceptionHandler so that Spring Boot's own
 * ProblemDetailsExceptionHandler backs off (it is @ConditionalOnMissingBean on
 * this type). Otherwise Boot's handler, registered with @Order(0), wins every
 * Spring MVC exception, including validation, and our overrides never run.
 */
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

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

    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail handleOrderNotFound(OrderNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.NOT_FOUND,
                "No order exists with the reference " + ex.reference());

        problem.setType(URI.create(BASE_TYPE + "order-not-found"));
        problem.setTitle("Order not found");
        problem.setProperty("reference", ex.reference());

        return problem;
    }

    /**
     * Called when a @Valid request body fails its constraints. The "errors"
     * extension maps each field to one message, which is what the Flask side
     * turns into the GOV.UK error summary.
     */
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        // A plain loop rather than Collectors.toMap: a field that breaks two
        // constraints appears twice, and toMap would throw on the duplicate key,
        // turning a 400 into a 500. The first message per field wins.
        Map<String, String> errors = new LinkedHashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            errors.putIfAbsent(error.getField(), error.getDefaultMessage());
        }
        return handleExceptionInternal(ex, validationProblem(errors), headers, status, request);
    }

    /** Constraint failures on @RequestParam, such as a malformed postcode or a limit out of range. */
    @Override
    protected ResponseEntity<Object> handleHandlerMethodValidationException(
            HandlerMethodValidationException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        Map<String, String> errors = new LinkedHashMap<>();
        for (ParameterValidationResult result : ex.getParameterValidationResults()) {
            String parameter = result.getMethodParameter().getParameterName();
            for (MessageSourceResolvable error : result.getResolvableErrors()) {
                errors.putIfAbsent(parameter, error.getDefaultMessage());
            }
        }
        return handleExceptionInternal(ex, validationProblem(errors), headers, status, request);
    }

    @Override
    protected ResponseEntity<Object> handleMissingServletRequestParameter(
            MissingServletRequestParameterException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        Map<String, String> errors = Map.of(ex.getParameterName(), ex.getParameterName() + " is required");
        return handleExceptionInternal(ex, validationProblem(errors), headers, status, request);
    }

    /** A parameter that cannot be converted, such as limit=abc. */
    @Override
    protected ResponseEntity<Object> handleTypeMismatch(
            TypeMismatchException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        String parameter = (ex instanceof MethodArgumentTypeMismatchException mismatch)
                ? mismatch.getName()
                : ex.getPropertyName();
        Map<String, String> errors = Map.of(parameter, parameter + " is not valid");
        return handleExceptionInternal(ex, validationProblem(errors), headers, status, request);
    }

    @ExceptionHandler(InvalidCursorException.class)
    ProblemDetail handleInvalidCursor(InvalidCursorException ex) {
        return validationProblem(Map.of("cursor", "cursor is not valid; start again from the first page"));
    }

    private static ProblemDetail validationProblem(Map<String, String> errors) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.BAD_REQUEST,
                "The request has fields that are missing or invalid");

        problem.setType(URI.create(BASE_TYPE + "validation-failed"));
        problem.setTitle("Validation failed");
        problem.setProperty("errors", errors);

        return problem;
    }
}
