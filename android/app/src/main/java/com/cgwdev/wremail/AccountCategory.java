package com.cgwdev.wremail;

final class AccountCategory {
    final String key;
    String label;
    final boolean protectedCategory;

    AccountCategory(String key, String label, boolean protectedCategory) {
        this.key = key;
        this.label = label;
        this.protectedCategory = protectedCategory;
    }
}
