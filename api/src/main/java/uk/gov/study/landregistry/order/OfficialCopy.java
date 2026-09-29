package uk.gov.study.landregistry.order;

/**
 * A rendered copy ready to download. A record with an array component compares
 * the array by reference, which is fine here: copies are sent, not compared.
 */
public record OfficialCopy(String fileName, byte[] content) {
}
