package com.cgwdev.wremail;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class ParsingTest {
    @Test
    public void stripsInternationalCallingCode() {
        assertEquals("87763590795", Parsing.phoneWithoutCountryCode("+6287763590795"));
        assertEquals("2633008723", Parsing.phoneWithoutCountryCode("+12633008723"));
    }

    @Test
    public void preservesCustomCategoryDuringImport() {
        ImportResult<ImportRecord> result = Parsing.parseAccounts(
                "user@example.com----password----client----refresh----自用----主账号"
        );

        assertEquals(1, result.records.size());
        assertEquals("自用", result.records.get(0).category);
        assertEquals("主账号", result.records.get(0).tag);
    }

    @Test
    public void fourColumnAccountImportDefaultsToUnused() {
        ImportResult<ImportRecord> result = Parsing.parseAccounts(
                "user@example.com----password----client----refresh"
        );

        assertEquals(1, result.records.size());
        assertEquals(Constants.CATEGORY_UNUSED, result.records.get(0).category);
    }
}
