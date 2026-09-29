package uk.gov.study.landregistry.order;

import jakarta.validation.Valid;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderService service;

    OrderController(OrderService service) {
        this.service = service;
    }

    // Without @Valid the constraints on CreateOrderRequest are silently ignored.
    @PostMapping
    public ResponseEntity<RegisterOrder> create(@Valid @RequestBody CreateOrderRequest request) {
        RegisterOrder created = service.create(request);
        return ResponseEntity
                .created(URI.create("/api/v1/orders/" + created.reference()))
                .body(created);
    }

    @PostMapping("/{reference}/payment")
    public RegisterOrder pay(@PathVariable String reference) {
        return service.pay(reference);
    }

    @GetMapping("/{reference}")
    public RegisterOrder get(@PathVariable String reference) {
        return service.findByReference(reference);
    }

    // produces=application/pdf: a request that does not accept the PDF (say,
    // Accept: application/json) is turned away with 406 before this method
    // runs, hiding a 409 or 404 behind it. Errors are still written as
    // application/problem+json even when only the PDF was asked for; the Flask
    // client accepts both to say so explicitly.
    @GetMapping(value = "/{reference}/document", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> document(@PathVariable String reference) {
        OfficialCopy copy = service.document(reference);
        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment().filename(copy.fileName()).build().toString())
                .body(copy.content());
    }
}
