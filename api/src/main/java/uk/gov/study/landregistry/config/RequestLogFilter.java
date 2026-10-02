package uk.gov.study.landregistry.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * One log line per request: method, path, status and duration.
 *
 * It runs inside RequestIdFilter, so the line carries the request id: a request
 * that logs nothing else, such as a title lookup, can still be followed from the
 * front end into the API.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 1)
public class RequestLogFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(RequestLogFilter.class);

    // Docker and OpenShift poll the health endpoints every few seconds.
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return request.getRequestURI().startsWith("/actuator");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        long start = System.nanoTime();
        try {
            chain.doFilter(request, response);
        } finally {
            long millis = (System.nanoTime() - start) / 1_000_000;
            // The path only, never the query string: a postcode search would put
            // the postcode in the log.
            log.atInfo()
                    .addKeyValue("http.method", request.getMethod())
                    .addKeyValue("url.path", request.getRequestURI())
                    .addKeyValue("http.status", response.getStatus())
                    .addKeyValue("durationMs", millis)
                    .log("{} {} {} {}ms", request.getMethod(), request.getRequestURI(), response.getStatus(), millis);
        }
    }
}
