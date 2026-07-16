package com.cgwdev.wremail;

import com.google.i18n.phonenumbers.PhoneNumberUtil;
import com.google.i18n.phonenumbers.Phonenumber;

import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class Parsing {
    private static final Pattern EMAIL_RE = Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$");
    private static final Pattern PHONE_RE = Pattern.compile("^\\+?\\d{6,18}$");
    private static final Pattern CODE_HINT_RE = Pattern.compile(
            "(?i)(?:验证码|校验码|动态码|安全代码|verification code|security code|code|otp|pin)[^A-Z0-9]{0,24}([A-Z0-9]{4,10})"
    );
    private static final Pattern CODE_NUMBER_RE = Pattern.compile("(?<!\\d)(\\d{4,8})(?!\\d)");

    private Parsing() {
    }

    static boolean isEmail(String value) {
        return value != null && EMAIL_RE.matcher(value.trim()).matches();
    }

    static boolean isPhone(String value) {
        return value != null && PHONE_RE.matcher(value.trim()).matches();
    }

    static String phoneWithoutCountryCode(String value) {
        String text = value == null ? "" : value.trim();
        if (text.isEmpty()) {
            return "";
        }
        try {
            PhoneNumberUtil util = PhoneNumberUtil.getInstance();
            Phonenumber.PhoneNumber parsed = util.parse(text, "ZZ");
            String national = util.getNationalSignificantNumber(parsed);
            if (!national.isEmpty()) {
                return national;
            }
        } catch (Exception ignored) {
        }
        return text.replaceAll("\\D+", "");
    }

    static String normalizeCategory(String value) {
        String text = value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
        if (text.equals("plus") || text.equals("p") || text.equals("标记plus")) {
            return Constants.CATEGORY_PLUS;
        }
        if (text.equals("free") || text.equals("f") || text.equals("标记free")) {
            return Constants.CATEGORY_FREE;
        }
        if (text.equals("banned") || text.equals("ban") || text.equals("blocked")
                || text.equals("封禁") || text.equals("已封禁") || text.equals("被封禁") || text.equals("标记封禁")) {
            return Constants.CATEGORY_BANNED;
        }
        return Constants.CATEGORY_UNUSED;
    }

    static boolean isUnusedCategoryAlias(String value) {
        String text = value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
        return text.isEmpty() || text.equals("unused") || text.equals("none")
                || text.equals("未使用") || text.equals("未标记");
    }

    static String importCategoryValue(String value) {
        String raw = value == null ? "" : value.trim();
        String normalized = normalizeCategory(raw);
        if (!Constants.CATEGORY_UNUSED.equals(normalized) || isUnusedCategoryAlias(raw)) {
            return normalized;
        }
        return compact(raw, 24);
    }

    static ImportResult<ImportRecord> parseAccounts(String text) {
        ImportResult<ImportRecord> result = new ImportResult<>();
        Set<String> seen = new HashSet<>();
        if (text == null) {
            return result;
        }
        String[] lines = text.split("\\r?\\n");
        for (String raw : lines) {
            String line = stripBom(raw).trim();
            while (line.endsWith(",") || line.endsWith(";")) {
                line = line.substring(0, line.length() - 1).trim();
            }
            if (isIgnoredLine(line)) {
                continue;
            }
            String[] parts = line.split("----", -1);
            if (parts.length == 0 || !isEmail(parts[0].trim())) {
                result.invalid++;
                continue;
            }
            String key = parts[0].trim().toLowerCase(Locale.ROOT);
            if (!seen.add(key)) {
                continue;
            }
            ImportRecord record = new ImportRecord();
            record.email = parts[0].trim();
            record.password = part(parts, 1);
            record.clientId = part(parts, 2);
            record.refreshToken = part(parts, 3);

            if (parts.length > 4 && isPhone(part(parts, 4))) {
                record.category = Constants.CATEGORY_UNUSED;
                record.phone = part(parts, 4);
                record.phoneApiUrl = isHttpUrl(part(parts, 5)) ? part(parts, 5) : "";
            } else {
                record.category = importCategoryValue(part(parts, 4));
                int cursor = 5;
                String maybeTag = part(parts, cursor);
                if (!maybeTag.isEmpty() && !isPhone(maybeTag) && !isHttpUrl(maybeTag)) {
                    record.tag = compact(maybeTag, 40);
                    cursor++;
                } else if (parts.length > cursor && maybeTag.isEmpty()) {
                    cursor++;
                }
                if (parts.length > cursor && isPhone(part(parts, cursor))) {
                    record.phone = part(parts, cursor);
                    cursor++;
                }
                if (parts.length > cursor && isHttpUrl(part(parts, cursor))) {
                    record.phoneApiUrl = part(parts, cursor);
                }
            }
            result.records.add(record);
        }
        return result;
    }

    static ImportResult<PhoneImportRecord> parsePhones(String text) {
        ImportResult<PhoneImportRecord> result = new ImportResult<>();
        Set<String> seen = new HashSet<>();
        if (text == null) {
            return result;
        }
        String[] lines = text.split("\\r?\\n");
        for (String raw : lines) {
            String line = stripBom(raw).trim();
            while (line.endsWith(",") || line.endsWith(";")) {
                line = line.substring(0, line.length() - 1).trim();
            }
            if (isIgnoredLine(line)) {
                continue;
            }
            String[] parts = line.split("----", -1);
            if (parts.length < 2 || !isPhone(part(parts, 0)) || !isHttpUrl(part(parts, 1))) {
                result.invalid++;
                continue;
            }
            String phone = part(parts, 0);
            if (!seen.add(phone)) {
                continue;
            }
            PhoneImportRecord record = new PhoneImportRecord();
            record.phone = phone;
            record.apiUrl = part(parts, 1);
            if (parts.length > 2) {
                String[] emails = part(parts, 2).split("[,;，\\s]+");
                Set<String> emailSeen = new HashSet<>();
                for (String email : emails) {
                    String clean = email.trim();
                    String key = clean.toLowerCase(Locale.ROOT);
                    if (isEmail(clean) && emailSeen.add(key)) {
                        record.emails.add(clean);
                    }
                    if (record.emails.size() >= 3) {
                        break;
                    }
                }
            }
            result.records.add(record);
        }
        return result;
    }

    static String extractCode(String... parts) {
        StringBuilder builder = new StringBuilder();
        if (parts != null) {
            for (String part : parts) {
                if (part != null) {
                    builder.append(part).append(' ');
                }
            }
        }
        String text = builder.toString();
        if (text.toLowerCase(Locale.ROOT).contains("no verification code")) {
            return "";
        }
        Matcher hinted = CODE_HINT_RE.matcher(text);
        if (hinted.find()) {
            String candidate = hinted.group(1).trim();
            if (isProbableCode(candidate)) {
                return candidate;
            }
        }
        Matcher numbered = CODE_NUMBER_RE.matcher(text);
        if (numbered.find()) {
            String candidate = numbered.group(1).trim();
            if (isProbableCode(candidate)) {
                return candidate;
            }
        }
        return "";
    }

    static String cleanCode(String value) {
        if (value == null || value.trim().isEmpty()) {
            return "";
        }
        String text = value.trim();
        return isProbableCode(text) ? text : extractCode(text);
    }

    static boolean isProbableCode(String value) {
        if (value == null) {
            return false;
        }
        String text = value.trim();
        if (!text.matches("(?i)[A-Z0-9]{4,10}")) {
            return false;
        }
        String lower = text.toLowerCase(Locale.ROOT);
        if (lower.equals("code") || lower.equals("data") || lower.equals("none")
                || lower.equals("null") || lower.equals("true") || lower.equals("false")) {
            return false;
        }
        for (int i = 0; i < text.length(); i++) {
            if (Character.isDigit(text.charAt(i))) {
                return true;
            }
        }
        return false;
    }

    static String compact(String value, int limit) {
        String text = value == null ? "" : value.trim().replaceAll("\\s+", " ");
        if (text.length() <= limit) {
            return text;
        }
        return text.substring(0, Math.max(0, limit - 1)).trim() + "…";
    }

    static String shortSender(String sender) {
        String text = sender == null ? "" : sender.trim();
        int angle = text.indexOf('<');
        if (angle > 0) {
            return text.substring(0, angle).replace("\"", "").trim();
        }
        int at = text.indexOf('@');
        if (at > 0) {
            return text.substring(0, at);
        }
        return text.isEmpty() ? "(未知发件人)" : text;
    }

    static String fmtDate(String value) {
        if (value == null || value.isEmpty()) {
            return "";
        }
        try {
            String normalized = value.endsWith("Z") ? value.substring(0, value.length() - 1) + "+00:00" : value;
            return OffsetDateTime.parse(normalized)
                    .atZoneSameInstant(ZoneId.systemDefault())
                    .format(DateTimeFormatter.ofPattern("MM/dd HH:mm"));
        } catch (Exception ignored) {
            try {
                return ZonedDateTime.parse(value, DateTimeFormatter.RFC_1123_DATE_TIME)
                        .withZoneSameInstant(ZoneId.systemDefault())
                        .format(DateTimeFormatter.ofPattern("MM/dd HH:mm"));
            } catch (Exception ignoredAgain) {
                return value;
            }
        }
    }

    static String joinExportParts(Object... parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            if (i > 0) {
                builder.append("----");
            }
            builder.append(parts[i] == null ? "" : String.valueOf(parts[i]));
        }
        return builder.toString();
    }

    static String csv(String value) {
        String text = value == null ? "" : value;
        return "\"" + text.replace("\"", "\"\"") + "\"";
    }

    private static boolean isIgnoredLine(String line) {
        if (line == null || line.trim().isEmpty()) {
            return true;
        }
        if (line.trim().startsWith("#")) {
            return true;
        }
        return line.trim().replaceAll("[=\\-_ *\\t]", "").isEmpty();
    }

    private static boolean isHttpUrl(String value) {
        String text = value == null ? "" : value.trim();
        return text.startsWith("http://") || text.startsWith("https://");
    }

    private static String part(String[] parts, int index) {
        return index >= 0 && index < parts.length ? parts[index].trim() : "";
    }

    private static String stripBom(String value) {
        if (value != null && value.startsWith("\uFEFF")) {
            return value.substring(1);
        }
        return value == null ? "" : value;
    }
}
