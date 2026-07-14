package com.cgwdev.wremail;

import java.util.Arrays;
import java.util.List;

final class Constants {
    static final String DISPLAY_NAME = "邮件验证码助手";
    static final String APP_VERSION = "V2.0";

    static final String AUTHORITY_BASE = "https://login.microsoftonline.com";
    static final String GRAPH_BASE = "https://graph.microsoft.com/v1.0";
    static final String IMAP_HOST = "outlook.office365.com";

    static final List<String> GRAPH_REFRESH_SCOPES = Arrays.asList(
            "https://graph.microsoft.com/Mail.Read offline_access",
            "Mail.Read offline_access",
            "https://graph.microsoft.com/.default",
            null
    );

    static final List<String> IMAP_REFRESH_SCOPES = Arrays.asList(
            "https://outlook.office.com/IMAP.AccessAsUser.All offline_access",
            "IMAP.AccessAsUser.All offline_access"
    );

    static final String CATEGORY_UNUSED = "unused";
    static final String CATEGORY_PLUS = "plus";
    static final String CATEGORY_FREE = "free";
    static final String CATEGORY_BANNED = "banned";

    static final String[] CATEGORY_ORDER = {
            CATEGORY_UNUSED,
            CATEGORY_PLUS,
            CATEGORY_FREE,
            CATEGORY_BANNED
    };

    static final String[] CATEGORY_LABELS = {
            "未使用",
            "Plus",
            "Free",
            "已封禁"
    };

    static final int CONNECT_TIMEOUT_MS = 8000;
    static final int READ_TIMEOUT_MS = 22000;

    private Constants() {
    }

    static String categoryLabel(String category) {
        String normalized = Parsing.normalizeCategory(category);
        for (int i = 0; i < CATEGORY_ORDER.length; i++) {
            if (CATEGORY_ORDER[i].equals(normalized)) {
                return CATEGORY_LABELS[i];
            }
        }
        return CATEGORY_LABELS[0];
    }
}
