package uk.gov.study.landregistry.order;

import org.springframework.stereotype.Component;

import java.security.SecureRandom;

/**
 * Generates public order references such as {@code LR-7KQ4XM2P}.
 *
 * Uniqueness is not guaranteed here: the UNIQUE constraint on
 * register_order.reference is the final arbiter of collisions.
 */
@Component
public class OrderReferenceGenerator {

    private static final String PREFIX = "LR-";
    private static final int LENGTH = 8;

    // No 0/O or 1/I/L: references are read aloud and typed by hand.
    // 31 symbols over 8 positions gives about 8.5 x 10^11 references.
    private static final String ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";

    // SecureRandom, not Random: a predictable sequence would let someone guess
    // other people's references. It is thread-safe, so one instance serves all
    // requests.
    private final SecureRandom random = new SecureRandom();

    public String next() {
        StringBuilder reference = new StringBuilder(PREFIX.length() + LENGTH).append(PREFIX);
        for (int i = 0; i < LENGTH; i++) {
            reference.append(ALPHABET.charAt(random.nextInt(ALPHABET.length())));
        }
        return reference.toString();
    }
}
