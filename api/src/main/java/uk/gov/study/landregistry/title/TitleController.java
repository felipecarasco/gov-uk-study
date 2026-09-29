package uk.gov.study.landregistry.title;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/titles")
public class TitleController {

    // Any case, spaces anywhere between the parts: the service normalises it.
    private static final String UK_POSTCODE =
            "^\\s*[A-Za-z]{1,2}[0-9][A-Za-z0-9]?\\s*[0-9][A-Za-z]{2}\\s*$";

    private final TitleService service;

    TitleController(TitleService service) {
        this.service = service;
    }

    // Constraints on @RequestParam are checked by Spring MVC's built-in method
    // validation, which reports failures as HandlerMethodValidationException
    // (not MethodArgumentNotValidException, which is for @Valid bodies).
    @GetMapping
    public TitleSearchPage search(
            @RequestParam
            @NotBlank(message = "Enter a postcode")
            @Pattern(regexp = UK_POSTCODE, message = "Enter a full postcode, like CR0 2QQ")
            String postcode,

            @RequestParam(required = false)
            String cursor,

            @RequestParam(defaultValue = "20")
            @Min(value = 1, message = "limit must be between 1 and 50")
            @Max(value = 50, message = "limit must be between 1 and 50")
            int limit) {
        return service.search(postcode, cursor, limit);
    }

    @GetMapping("/{titleNumber}")
    public TitleDetail get(@PathVariable String titleNumber) {
        return service.findByTitleNumber(titleNumber);
    }
}
