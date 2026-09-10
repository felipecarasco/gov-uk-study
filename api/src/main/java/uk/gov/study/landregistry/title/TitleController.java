package uk.gov.study.landregistry.title;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/titles")
public class TitleController {

    private final TitleService service;

    TitleController(TitleService service) {
        this.service = service;
    }

    @GetMapping("/{titleNumber}")
    public TitleDetail get(@PathVariable String titleNumber) {
        return service.findByTitleNumber(titleNumber);
    }
}
