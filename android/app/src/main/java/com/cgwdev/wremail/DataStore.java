package com.cgwdev.wremail;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

final class DataStore {
    static final int MAX_EMAILS_PER_PHONE = 3;

    final List<AccountRecord> accounts = new ArrayList<>();
    final List<PhoneRecord> phones = new ArrayList<>();
    final List<PhoneRecord> standalonePhones = new ArrayList<>();
    final List<AccountCategory> categories = new ArrayList<>();
    final AppConfig config = new AppConfig();

    private final Context context;
    private final CryptoStore crypto;

    DataStore(Context context) {
        this.context = context.getApplicationContext();
        this.crypto = new CryptoStore(context);
    }

    synchronized void load() {
        loadCategories();
        loadAccounts();
        loadPhones();
        loadStandalonePhones();
        loadConfig();
        syncAccountPhoneFields(false);
    }

    synchronized int[] upsertAccounts(List<ImportRecord> records) {
        int added = 0;
        int updated = 0;
        int skipped = 0;
        String now = Instant.now().toString();
        for (ImportRecord record : records) {
            AccountRecord current = getAccount(record.email);
            if (current == null) {
                AccountRecord account = new AccountRecord();
                account.email = record.email;
                account.password = record.password;
                account.clientId = record.clientId;
                account.refreshToken = record.refreshToken;
                account.tag = cleanTag(record.tag);
                account.importedAt = now;
                account.category = resolveOrAddCategory(record.category);
                account.used = !Constants.CATEGORY_UNUSED.equals(account.category);
                account.lastStatus = record.refreshToken.isEmpty() ? "未取件" : "已导入";
                accounts.add(account);
                added++;
                continue;
            }
            boolean changed = false;
            changed |= setIfPresent(current, "password", record.password);
            changed |= setIfPresent(current, "clientId", record.clientId);
            changed |= setIfPresent(current, "refreshToken", record.refreshToken);
            if (!record.tag.isEmpty() && !current.tag.equals(cleanTag(record.tag))) {
                current.tag = cleanTag(record.tag);
                changed = true;
            }
            String category = resolveOrAddCategory(record.category);
            if (!Constants.CATEGORY_UNUSED.equals(category) && !current.category.equals(category)) {
                current.category = category;
                current.used = true;
                changed = true;
            }
            if (changed) {
                updated++;
            } else {
                skipped++;
            }
        }
        sortAccounts();
        saveAccounts();
        return new int[]{added, updated, skipped};
    }

    synchronized int[] upsertPhones(List<PhoneImportRecord> records, boolean standalone) {
        List<PhoneRecord> target = standalone ? standalonePhones : phones;
        int added = 0;
        int updated = 0;
        int skipped = 0;
        String now = Instant.now().toString();
        for (PhoneImportRecord record : records) {
            PhoneRecord current = findPhone(target, record.phone);
            if (current == null) {
                current = new PhoneRecord();
                current.phone = record.phone;
                current.apiUrl = record.apiUrl;
                current.importedAt = now;
                current.lastStatus = "已导入";
                target.add(current);
                added++;
            } else if (!current.apiUrl.equals(record.apiUrl)) {
                current.apiUrl = record.apiUrl;
                current.lastStatus = "已更新";
                updated++;
            } else {
                skipped++;
            }
            if (!standalone && !record.emails.isEmpty()) {
                bindEmails(record.phone, new HashSet<>(record.emails), false);
            }
        }
        sortPhones(target);
        if (standalone) {
            saveStandalonePhones();
        } else {
            savePhones();
            saveAccounts();
        }
        return new int[]{added, updated, skipped};
    }

    synchronized AccountRecord getAccount(String email) {
        String key = email == null ? "" : email.trim().toLowerCase(Locale.ROOT);
        for (AccountRecord account : accounts) {
            if (account.email.toLowerCase(Locale.ROOT).equals(key)) {
                return account;
            }
        }
        return null;
    }

    synchronized PhoneRecord getPhone(String phone) {
        return findPhone(phones, phone);
    }

    synchronized PhoneRecord getStandalonePhone(String phone) {
        return findPhone(standalonePhones, phone);
    }

    synchronized void markAccount(String email, String status, boolean fetched) {
        AccountRecord account = getAccount(email);
        if (account == null) {
            return;
        }
        account.lastStatus = status;
        if (fetched) {
            account.lastFetchAt = Instant.now().toString();
        }
        saveAccounts();
    }

    synchronized void updateRefreshToken(String email, String refreshToken) {
        AccountRecord account = getAccount(email);
        if (account != null && refreshToken != null && !refreshToken.isEmpty() && !account.refreshToken.equals(refreshToken)) {
            account.refreshToken = refreshToken;
            saveAccounts();
        }
    }

    synchronized int setCategory(Set<String> emails, String category) {
        String normalized = resolveCategory(category);
        if (normalized == null) {
            normalized = Constants.CATEGORY_UNUSED;
        }
        int changed = 0;
        for (AccountRecord account : accounts) {
            if (emails.contains(account.email) && !account.category.equals(normalized)) {
                account.category = normalized;
                account.used = !Constants.CATEGORY_UNUSED.equals(normalized);
                changed++;
            }
        }
        if (changed > 0) {
            saveAccounts();
        }
        return changed;
    }

    synchronized boolean setTag(String email, String tag) {
        AccountRecord account = getAccount(email);
        if (account == null) {
            return false;
        }
        account.tag = cleanTag(tag);
        saveAccounts();
        return true;
    }

    synchronized int removeAccounts(Set<String> emails) {
        int before = accounts.size();
        accounts.removeIf(account -> emails.contains(account.email));
        for (PhoneRecord phone : phones) {
            phone.emails.removeIf(emails::contains);
        }
        saveAccounts();
        savePhones();
        return before - accounts.size();
    }

    synchronized int clearAccounts() {
        int total = accounts.size();
        accounts.clear();
        for (PhoneRecord phone : phones) {
            phone.emails.clear();
        }
        saveAccounts();
        savePhones();
        return total;
    }

    synchronized int bindEmails(String phoneNumber, Set<String> emails, boolean save) {
        PhoneRecord phone = getPhone(phoneNumber);
        if (phone == null) {
            return 0;
        }
        int bound = 0;
        for (String email : sortedStrings(emails)) {
            AccountRecord account = getAccount(email);
            if (account == null || phone.emails.contains(account.email)) {
                continue;
            }
            if (phone.emails.size() >= MAX_EMAILS_PER_PHONE) {
                break;
            }
            removeEmailFromOtherPhones(account.email, phone.phone);
            phone.emails.add(account.email);
            account.phone = phone.phone;
            bound++;
        }
        sortStrings(phone.emails);
        if (save && bound > 0) {
            savePhones();
            saveAccounts();
        }
        return bound;
    }

    synchronized void setPhoneBindings(String phoneNumber, List<String> emails) {
        PhoneRecord phone = getPhone(phoneNumber);
        if (phone == null) {
            return;
        }
        Set<String> selected = new HashSet<>();
        for (String email : emails) {
            AccountRecord account = getAccount(email);
            if (account != null && selected.size() < MAX_EMAILS_PER_PHONE) {
                selected.add(account.email);
            }
        }
        for (AccountRecord account : accounts) {
            if (account.phone.equals(phoneNumber) && !selected.contains(account.email)) {
                account.phone = "";
            }
        }
        phone.emails.clear();
        for (String email : sortedStrings(selected)) {
            removeEmailFromOtherPhones(email, phoneNumber);
            phone.emails.add(email);
            AccountRecord account = getAccount(email);
            if (account != null) {
                account.phone = phoneNumber;
            }
        }
        savePhones();
        saveAccounts();
    }

    synchronized int unbindEmails(Set<String> emails) {
        int removed = 0;
        for (PhoneRecord phone : phones) {
            int before = phone.emails.size();
            phone.emails.removeIf(emails::contains);
            removed += before - phone.emails.size();
        }
        for (String email : emails) {
            AccountRecord account = getAccount(email);
            if (account != null) {
                account.phone = "";
            }
        }
        if (removed > 0) {
            savePhones();
            saveAccounts();
        }
        return removed;
    }

    synchronized boolean removePhone(String phoneNumber) {
        PhoneRecord phone = getPhone(phoneNumber);
        if (phone == null) {
            return false;
        }
        for (String email : phone.emails) {
            AccountRecord account = getAccount(email);
            if (account != null) {
                account.phone = "";
            }
        }
        phones.remove(phone);
        savePhones();
        saveAccounts();
        return true;
    }

    synchronized void clearPhoneBindings(String phoneNumber) {
        PhoneRecord phone = getPhone(phoneNumber);
        if (phone == null) {
            return;
        }
        Set<String> emails = new HashSet<>(phone.emails);
        phone.emails.clear();
        for (String email : emails) {
            AccountRecord account = getAccount(email);
            if (account != null) {
                account.phone = "";
            }
        }
        savePhones();
        saveAccounts();
    }

    synchronized void markPhone(PhoneRecord phone, String status, String code, String message, boolean standalone) {
        phone.lastStatus = status;
        phone.lastCode = code == null ? "" : code;
        phone.lastMessage = message == null ? "" : Parsing.compact(message, 500);
        phone.lastFetchAt = Instant.now().toString();
        if (standalone) {
            saveStandalonePhones();
        } else {
            savePhones();
        }
    }

    synchronized void clearStandalonePhones() {
        standalonePhones.clear();
        saveStandalonePhones();
    }

    synchronized boolean removeStandalonePhone(String phoneNumber) {
        PhoneRecord phone = getStandalonePhone(phoneNumber);
        if (phone == null) {
            return false;
        }
        standalonePhones.remove(phone);
        saveStandalonePhones();
        return true;
    }

    synchronized void saveConfig() {
        try {
            JSONObject json = new JSONObject();
            json.put("client_id", config.clientId);
            json.put("tenant", config.tenant);
            json.put("top", config.top);
            json.put("protocol", config.protocol);
            json.put("auto_fetch_after_import", config.autoFetchAfterImport);
            json.put("concise_mode", config.conciseMode);
            json.put("dark_theme", config.darkTheme);
            Files.write(configFile().toPath(), json.toString(2).getBytes(StandardCharsets.UTF_8));
        } catch (Exception exc) {
            throw new IllegalStateException("保存配置失败：" + exc.getMessage(), exc);
        }
    }

    synchronized List<AccountCategory> categorySnapshot() {
        List<AccountCategory> snapshot = new ArrayList<>();
        for (AccountCategory category : categories) {
            snapshot.add(new AccountCategory(category.key, category.label, category.protectedCategory));
        }
        return snapshot;
    }

    synchronized String categoryLabel(String key) {
        String resolved = resolveCategory(key);
        if (resolved != null) {
            for (AccountCategory category : categories) {
                if (category.key.equals(resolved)) {
                    return category.label;
                }
            }
        }
        return "未使用";
    }

    synchronized String resolveCategory(String value) {
        String raw = value == null ? "" : value.trim();
        if (raw.isEmpty()) {
            return Constants.CATEGORY_UNUSED;
        }
        for (AccountCategory category : categories) {
            if (category.key.equalsIgnoreCase(raw) || category.label.equalsIgnoreCase(raw)) {
                return category.key;
            }
        }
        String legacy = Parsing.normalizeCategory(raw);
        boolean knownLegacy = !Constants.CATEGORY_UNUSED.equals(legacy) || Parsing.isUnusedCategoryAlias(raw);
        if (knownLegacy) {
            for (AccountCategory category : categories) {
                if (category.key.equals(legacy)) {
                    return category.key;
                }
            }
        }
        return null;
    }

    synchronized String resolveOrAddCategory(String value) {
        String resolved = resolveCategory(value);
        if (resolved != null) {
            return resolved;
        }
        AccountCategory added = addCategory(value);
        return added == null ? Constants.CATEGORY_UNUSED : added.key;
    }

    synchronized AccountCategory addCategory(String label) {
        String clean = cleanCategoryLabel(label);
        if (clean.isEmpty()) {
            return null;
        }
        for (AccountCategory category : categories) {
            if (category.label.equalsIgnoreCase(clean)) {
                return category;
            }
        }
        String key = "custom_" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        AccountCategory category = new AccountCategory(key, clean, false);
        categories.add(category);
        saveCategories();
        return category;
    }

    synchronized boolean renameCategory(String key, String label) {
        String clean = cleanCategoryLabel(label);
        if (clean.isEmpty()) {
            return false;
        }
        for (AccountCategory category : categories) {
            if (!category.key.equals(key) && category.label.equalsIgnoreCase(clean)) {
                return false;
            }
        }
        for (AccountCategory category : categories) {
            if (category.key.equals(key) && !category.protectedCategory) {
                category.label = clean;
                saveCategories();
                return true;
            }
        }
        return false;
    }

    synchronized int deleteCategory(String key) {
        AccountCategory target = null;
        for (AccountCategory category : categories) {
            if (category.key.equals(key)) {
                target = category;
                break;
            }
        }
        if (target == null || target.protectedCategory) {
            return -1;
        }
        int moved = 0;
        for (AccountRecord account : accounts) {
            if (account.category.equals(target.key)) {
                account.category = Constants.CATEGORY_UNUSED;
                account.used = false;
                moved++;
            }
        }
        categories.remove(target);
        saveCategories();
        saveAccounts();
        return moved;
    }

    synchronized String exportAccountsText() {
        StringBuilder builder = new StringBuilder();
        String currentCategory = "";
        List<AccountRecord> sorted = new ArrayList<>(accounts);
        sorted.sort((left, right) -> {
            int category = Integer.compare(categoryIndex(left.category), categoryIndex(right.category));
            if (category != 0) {
                return category;
            }
            return left.email.compareToIgnoreCase(right.email);
        });
        for (AccountRecord account : sorted) {
            String label = categoryLabel(account.category);
            if (!account.category.equals(currentCategory)) {
                if (builder.length() > 0) {
                    builder.append("\n\n");
                }
                builder.append("# ===== ").append(label).append(" =====\n");
                currentCategory = account.category;
            }
            PhoneRecord phone = account.phone.isEmpty() ? null : getPhone(account.phone);
            builder
                    .append(Parsing.joinExportParts(
                            account.email,
                            account.password,
                            account.clientId,
                            account.refreshToken,
                            label,
                            account.tag,
                            account.phone,
                            phone == null ? "" : phone.apiUrl
                    ))
                    .append('\n');
        }
        return builder.toString();
    }

    synchronized String exportPhonesText() {
        StringBuilder builder = new StringBuilder();
        List<PhoneRecord> sorted = new ArrayList<>(phones);
        sortPhones(sorted);
        for (PhoneRecord phone : sorted) {
            builder.append(Parsing.joinExportParts(phone.phone, phone.apiUrl, String.join(",", phone.emails))).append('\n');
        }
        return builder.toString();
    }

    private void loadAccounts() {
        accounts.clear();
        try {
            String text = crypto.readText("accounts.sec");
            if (text.isEmpty()) {
                return;
            }
            JSONArray array = new JSONObject(text).optJSONArray("accounts");
            if (array == null) {
                return;
            }
            for (int i = 0; i < array.length(); i++) {
                accounts.add(accountFromJson(array.getJSONObject(i)));
            }
            sortAccounts();
        } catch (Exception ignored) {
            accounts.clear();
        }
    }

    private void loadCategories() {
        categories.clear();
        File file = categoriesFile();
        if (file.exists()) {
            try {
                JSONArray array = new JSONObject(new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8))
                        .optJSONArray("categories");
                if (array != null) {
                    Set<String> keys = new HashSet<>();
                    Set<String> labels = new HashSet<>();
                    for (int i = 0; i < array.length(); i++) {
                        JSONObject json = array.optJSONObject(i);
                        if (json == null) {
                            continue;
                        }
                        String key = json.optString("key", "").trim();
                        String label = cleanCategoryLabel(json.optString("label", ""));
                        String lowerKey = key.toLowerCase(Locale.ROOT);
                        String lowerLabel = label.toLowerCase(Locale.ROOT);
                        if (key.isEmpty() || label.isEmpty() || keys.contains(lowerKey) || labels.contains(lowerLabel)) {
                            continue;
                        }
                        boolean protectedCategory = Constants.CATEGORY_UNUSED.equals(key);
                        categories.add(new AccountCategory(key, label, protectedCategory));
                        keys.add(lowerKey);
                        labels.add(lowerLabel);
                    }
                }
            } catch (Exception ignored) {
                categories.clear();
            }
        }
        ensureDefaultCategories();
        saveCategories();
    }

    private void ensureDefaultCategories() {
        if (categories.isEmpty()) {
            for (int i = 0; i < Constants.CATEGORY_ORDER.length; i++) {
                String key = Constants.CATEGORY_ORDER[i];
                categories.add(new AccountCategory(key, Constants.CATEGORY_LABELS[i], Constants.CATEGORY_UNUSED.equals(key)));
            }
            return;
        }
        boolean hasUnused = false;
        for (AccountCategory category : categories) {
            if (Constants.CATEGORY_UNUSED.equals(category.key)) {
                hasUnused = true;
                break;
            }
        }
        if (!hasUnused) {
            categories.add(0, new AccountCategory(Constants.CATEGORY_UNUSED, "未使用", true));
        }
        for (int i = 0; i < categories.size(); i++) {
            if (Constants.CATEGORY_UNUSED.equals(categories.get(i).key) && i != 0) {
                AccountCategory unused = categories.remove(i);
                categories.add(0, unused);
                break;
            }
        }
    }

    private void saveCategories() {
        try {
            JSONArray array = new JSONArray();
            for (AccountCategory category : categories) {
                JSONObject json = new JSONObject();
                json.put("key", category.key);
                json.put("label", category.label);
                json.put("protected", category.protectedCategory);
                array.put(json);
            }
            JSONObject root = new JSONObject().put("categories", array);
            Files.write(categoriesFile().toPath(), root.toString(2).getBytes(StandardCharsets.UTF_8));
        } catch (Exception exc) {
            throw new IllegalStateException("保存分类失败：" + exc.getMessage(), exc);
        }
    }

    private void loadPhones() {
        phones.clear();
        try {
            String text = crypto.readText("phones.sec");
            if (text.isEmpty()) {
                return;
            }
            JSONArray array = new JSONObject(text).optJSONArray("phones");
            if (array == null) {
                return;
            }
            for (int i = 0; i < array.length(); i++) {
                phones.add(phoneFromJson(array.getJSONObject(i), false));
            }
            sortPhones(phones);
        } catch (Exception ignored) {
            phones.clear();
        }
    }

    private void loadStandalonePhones() {
        standalonePhones.clear();
        try {
            String text = crypto.readText("standalone_phones.sec");
            if (text.isEmpty()) {
                return;
            }
            JSONArray array = new JSONObject(text).optJSONArray("phones");
            if (array == null) {
                return;
            }
            for (int i = 0; i < array.length(); i++) {
                standalonePhones.add(phoneFromJson(array.getJSONObject(i), true));
            }
            sortPhones(standalonePhones);
        } catch (Exception ignored) {
            standalonePhones.clear();
        }
    }

    private void loadConfig() {
        try {
            File file = configFile();
            if (!file.exists()) {
                return;
            }
            JSONObject json = new JSONObject(new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8));
            config.clientId = json.optString("client_id", "");
            config.tenant = json.optString("tenant", "consumers");
            config.top = Math.max(1, Math.min(50, json.optInt("top", 10)));
            config.protocol = json.optString("protocol", "Graph").equalsIgnoreCase("IMAP") ? "IMAP" : "Graph";
            config.autoFetchAfterImport = json.optBoolean("auto_fetch_after_import", true);
            config.conciseMode = json.optBoolean("concise_mode", false);
            config.darkTheme = json.optBoolean("dark_theme", false);
        } catch (Exception ignored) {
            config.protocol = "Graph";
        }
    }

    private void saveAccounts() {
        try {
            JSONArray array = new JSONArray();
            for (AccountRecord account : accounts) {
                array.put(accountToJson(account));
            }
            crypto.writeText("accounts.sec", new JSONObject().put("accounts", array).toString());
        } catch (Exception exc) {
            throw new IllegalStateException("保存账号失败：" + exc.getMessage(), exc);
        }
    }

    private void savePhones() {
        try {
            JSONArray array = new JSONArray();
            for (PhoneRecord phone : phones) {
                array.put(phoneToJson(phone));
            }
            crypto.writeText("phones.sec", new JSONObject().put("phones", array).toString());
        } catch (Exception exc) {
            throw new IllegalStateException("保存手机号失败：" + exc.getMessage(), exc);
        }
    }

    private void saveStandalonePhones() {
        try {
            JSONArray array = new JSONArray();
            for (PhoneRecord phone : standalonePhones) {
                array.put(phoneToJson(phone));
            }
            crypto.writeText("standalone_phones.sec", new JSONObject().put("phones", array).toString());
        } catch (Exception exc) {
            throw new IllegalStateException("保存独立手机号失败：" + exc.getMessage(), exc);
        }
    }

    private AccountRecord accountFromJson(JSONObject json) {
        AccountRecord account = new AccountRecord();
        account.email = json.optString("email", "");
        account.password = json.optString("password", "");
        account.clientId = json.optString("client_id", "");
        account.refreshToken = json.optString("refresh_token", "");
        account.phone = json.optString("phone", "");
        account.tag = json.optString("tag", "");
        account.importedAt = json.optString("imported_at", Instant.now().toString());
        account.lastFetchAt = json.optString("last_fetch_at", "");
        account.lastStatus = json.optString("last_status", "未取件");
        account.used = json.optBoolean("used", false);
        String storedCategory = json.optString("category", account.used ? Constants.CATEGORY_PLUS : Constants.CATEGORY_UNUSED);
        String resolvedCategory = resolveCategory(storedCategory);
        account.category = resolvedCategory == null ? Constants.CATEGORY_UNUSED : resolvedCategory;
        return account;
    }

    private JSONObject accountToJson(AccountRecord account) throws Exception {
        JSONObject json = new JSONObject();
        json.put("email", account.email);
        json.put("password", account.password);
        json.put("client_id", account.clientId);
        json.put("refresh_token", account.refreshToken);
        json.put("phone", account.phone);
        json.put("tag", account.tag);
        json.put("imported_at", account.importedAt);
        json.put("last_fetch_at", account.lastFetchAt);
        json.put("last_status", account.lastStatus);
        json.put("used", account.used);
        json.put("category", account.category);
        return json;
    }

    private PhoneRecord phoneFromJson(JSONObject json, boolean standalone) {
        PhoneRecord phone = new PhoneRecord();
        phone.phone = json.optString("phone", "");
        phone.apiUrl = json.optString("api_url", "");
        phone.importedAt = json.optString("imported_at", Instant.now().toString());
        phone.lastFetchAt = json.optString("last_fetch_at", "");
        phone.lastStatus = json.optString("last_status", standalone ? "已导入" : "未取码");
        phone.lastCode = json.optString("last_code", "");
        phone.lastMessage = json.optString("last_message", "");
        JSONArray emails = json.optJSONArray("emails");
        if (!standalone && emails != null) {
            for (int i = 0; i < emails.length() && phone.emails.size() < MAX_EMAILS_PER_PHONE; i++) {
                String email = emails.optString(i, "");
                if (Parsing.isEmail(email) && !phone.emails.contains(email)) {
                    phone.emails.add(email);
                }
            }
        }
        return phone;
    }

    private JSONObject phoneToJson(PhoneRecord phone) throws Exception {
        JSONObject json = new JSONObject();
        json.put("phone", phone.phone);
        json.put("api_url", phone.apiUrl);
        json.put("emails", new JSONArray(phone.emails));
        json.put("imported_at", phone.importedAt);
        json.put("last_fetch_at", phone.lastFetchAt);
        json.put("last_status", phone.lastStatus);
        json.put("last_code", phone.lastCode);
        json.put("last_message", phone.lastMessage);
        return json;
    }

    private void syncAccountPhoneFields(boolean saveAccounts) {
        for (AccountRecord account : accounts) {
            account.phone = "";
        }
        for (PhoneRecord phone : phones) {
            phone.emails.removeIf(email -> getAccount(email) == null);
            for (String email : phone.emails) {
                AccountRecord account = getAccount(email);
                if (account != null) {
                    account.phone = phone.phone;
                }
            }
        }
        if (saveAccounts) {
            saveAccounts();
        }
    }

    private void removeEmailFromOtherPhones(String email, String exceptPhone) {
        for (PhoneRecord phone : phones) {
            if (!phone.phone.equals(exceptPhone)) {
                phone.emails.removeIf(item -> item.equalsIgnoreCase(email));
            }
        }
    }

    private PhoneRecord findPhone(List<PhoneRecord> target, String phoneNumber) {
        String key = phoneNumber == null ? "" : phoneNumber.trim();
        for (PhoneRecord phone : target) {
            if (phone.phone.equals(key)) {
                return phone;
            }
        }
        return null;
    }

    private void sortAccounts() {
        accounts.sort(Comparator.comparing(account -> account.email.toLowerCase(Locale.ROOT)));
    }

    private void sortPhones(List<PhoneRecord> target) {
        target.sort(Comparator.comparing(phone -> phone.phone.toLowerCase(Locale.ROOT)));
    }

    private static void sortStrings(List<String> values) {
        values.sort(String::compareToIgnoreCase);
    }

    private static List<String> sortedStrings(Set<String> values) {
        List<String> sorted = new ArrayList<>(values);
        sortStrings(sorted);
        return sorted;
    }

    private int categoryIndex(String category) {
        String resolved = resolveCategory(category);
        for (int i = 0; i < categories.size(); i++) {
            if (categories.get(i).key.equals(resolved)) {
                return i;
            }
        }
        return 99;
    }

    private String cleanTag(String tag) {
        return Parsing.compact(tag == null ? "" : tag.replaceAll("\\s+", " "), 40);
    }

    private String cleanCategoryLabel(String label) {
        String clean = label == null ? "" : label.trim().replaceAll("\\s+", " ");
        if (clean.startsWith("#") || clean.contains("----")) {
            return "";
        }
        return Parsing.compact(clean, 24);
    }

    private boolean setIfPresent(AccountRecord account, String field, String value) {
        if (value == null || value.isEmpty()) {
            return false;
        }
        switch (field) {
            case "password":
                if (!account.password.equals(value)) {
                    account.password = value;
                    return true;
                }
                return false;
            case "clientId":
                if (!account.clientId.equals(value)) {
                    account.clientId = value;
                    return true;
                }
                return false;
            case "refreshToken":
                if (!account.refreshToken.equals(value)) {
                    account.refreshToken = value;
                    return true;
                }
                return false;
            default:
                return false;
        }
    }

    private File configFile() {
        return new File(context.getFilesDir(), "config.json");
    }

    private File categoriesFile() {
        return new File(context.getFilesDir(), "categories.json");
    }
}
