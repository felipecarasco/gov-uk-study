package uk.gov.study.landregistry.title;

import org.springframework.stereotype.Service;

@Service
public class TitleService {

    private final TitleRepository repository;

    TitleService(TitleRepository repository) {
        this.repository = repository;
    }

    public TitleDetail findByTitleNumber(String titleNumber) {
        return repository.findByTitleNumber(titleNumber)
                .orElseThrow(() -> new TitleNotFoundException(titleNumber));
    }
}
