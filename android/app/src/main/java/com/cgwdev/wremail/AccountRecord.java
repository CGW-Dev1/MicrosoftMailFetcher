package com.cgwdev.wremail;

final class AccountRecord {
    String email = "";
    String password = "";
    String clientId = "";
    String refreshToken = "";
    String phone = "";
    String tag = "";
    String importedAt = "";
    String lastFetchAt = "";
    String lastStatus = "未取件";
    boolean used = false;
    String category = Constants.CATEGORY_UNUSED;

    String source() {
        return !clientId.isEmpty() && !refreshToken.isEmpty() ? "OAuth令牌" : "缺少令牌";
    }

    String categoryLabel() {
        return Constants.categoryLabel(category);
    }
}
