package com.cgwdev.wremail;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.SocketTimeoutException;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Properties;

import javax.net.ssl.SSLException;

import javax.mail.Address;
import javax.mail.BodyPart;
import javax.mail.Flags;
import javax.mail.Folder;
import javax.mail.Message;
import javax.mail.Multipart;
import javax.mail.Session;
import javax.mail.Store;
import javax.mail.internet.MimeUtility;

final class MailService {
    private final DataStore store;

    MailService(DataStore store) {
        this.store = store;
    }

    List<MailRow> fetchAccountRows(AccountRecord account, String protocol, int top, boolean conciseMode) throws Exception {
        List<MailRow> rows = "IMAP".equalsIgnoreCase(protocol)
                ? fetchImapRows(account, top)
                : fetchGraphRows(account, top);
        if (!conciseMode) {
            return rows;
        }
        List<MailRow> concise = new ArrayList<>();
        for (MailRow row : rows) {
            concise.add(conciseRow(row));
        }
        return concise;
    }

    MailRow fetchPhoneRow(PhoneRecord phone, boolean conciseMode) throws Exception {
        HttpResult response = requestSms(phone.apiUrl);
        if (response.status >= 400) {
            throw new IllegalStateException("短信 API 请求失败 HTTP " + response.status + ": " + Parsing.compact(response.body, 300));
        }
        Object payload = parseJson(response.body);
        String smsContent = apiDataField(payload, "code");
        if (smsContent.isEmpty()) {
            smsContent = apiDataField(payload, "message");
        }
        if (smsContent.isEmpty()) {
            smsContent = apiDataField(payload, "content");
        }
        String searchable = smsContent.isEmpty() ? searchableText(payload, response.body, phone.phone) : smsContent;
        String apiCode = apiCode(payload);
        String code = apiCode.isEmpty() ? Parsing.cleanCode(Parsing.extractCode(searchable)) : apiCode;
        String apiMessage = apiMessage(payload);
        String previewSource = searchable.isEmpty() ? apiMessage : searchable;

        MailRow row = new MailRow();
        row.account = phone.emails.isEmpty() ? phone.phone : String.join(", ", phone.emails);
        row.phone = phone.phone;
        row.protocol = "SMS";
        row.time = Parsing.fmtDate(apiDataField(payload, "code_time"));
        row.sender = phone.phone;
        row.subject = code.isEmpty() ? "未识别" : code;
        row.code = code;
        row.preview = conciseMode && !code.isEmpty() ? "" : Parsing.compact(previewSource, 900);
        row.smsContent = smsContent;
        row.codeTime = row.time;
        row.expiredDate = apiDataField(payload, "expired_date");
        row.apiMsg = optString(payload, "msg");
        row.apiStatus = optString(payload, "code");
        row.concise = conciseMode;
        return row;
    }

    private HttpResult requestSms(String apiUrl) throws Exception {
        String clean = apiUrl == null ? "" : apiUrl.trim();
        URL url;
        try {
            url = new URL(clean);
        } catch (Exception exc) {
            throw new IllegalStateException("短信 API 地址无效，请重新导入完整的 http/https 地址。", exc);
        }
        String protocol = url.getProtocol();
        if (!("http".equalsIgnoreCase(protocol) || "https".equalsIgnoreCase(protocol)) || url.getHost().isEmpty()) {
            throw new IllegalStateException("短信 API 地址无效，请重新导入完整的 http/https 地址。");
        }
        Exception last = null;
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                return request("GET", clean, null, null);
            } catch (SSLException exc) {
                throw new IllegalStateException("短信 API 安全连接失败，请检查系统时间、证书或网络拦截设置。", exc);
            } catch (SocketTimeoutException exc) {
                last = exc;
            } catch (IOException exc) {
                last = exc;
            }
            if (attempt == 0) {
                try {
                    Thread.sleep(350);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    throw new IllegalStateException("短信 API 请求已取消。", interrupted);
                }
            }
        }
        if (last instanceof SocketTimeoutException) {
            throw new IllegalStateException("短信 API 请求超时，已自动重试，请检查网络或稍后再试。", last);
        }
        throw new IllegalStateException("无法连接短信 API（" + url.getHost() + "），已自动重试；请检查网络或 API 服务状态。", last);
    }

    private List<MailRow> fetchGraphRows(AccountRecord account, int top) throws Exception {
        String token = refreshAccessToken(account, Constants.GRAPH_REFRESH_SCOPES);
        String query = "$top=" + clampTop(top)
                + "&$orderby=" + encode("receivedDateTime desc")
                + "&$select=" + encode("receivedDateTime,from,sender,subject,bodyPreview,webLink,isRead");
        HttpResult response = request(
                "GET",
                Constants.GRAPH_BASE + "/me/mailFolders/inbox/messages?" + query,
                null,
                token
        );
        if (response.status >= 400) {
            throw new IllegalStateException("Graph 请求失败 HTTP " + response.status + ": " + Parsing.compact(response.body, 500));
        }
        JSONObject json = new JSONObject(response.body);
        JSONArray values = json.optJSONArray("value");
        List<MailRow> rows = new ArrayList<>();
        if (values == null) {
            return rows;
        }
        for (int i = 0; i < values.length(); i++) {
            JSONObject message = values.getJSONObject(i);
            JSONObject senderObj = message.optJSONObject("from");
            if (senderObj == null) {
                senderObj = message.optJSONObject("sender");
            }
            JSONObject emailObj = senderObj == null ? null : senderObj.optJSONObject("emailAddress");
            MailRow row = new MailRow();
            row.account = account.email;
            row.protocol = "GRAPH";
            row.time = Parsing.fmtDate(message.optString("receivedDateTime", ""));
            row.sender = emailObj == null ? "" : firstNonEmpty(emailObj.optString("address", ""), emailObj.optString("name", ""));
            row.subject = message.optString("subject", "");
            row.read = message.optBoolean("isRead", false) ? "是" : "否";
            row.preview = message.optString("bodyPreview", "");
            row.webLink = message.optString("webLink", "");
            rows.add(row);
        }
        return rows;
    }

    private List<MailRow> fetchImapRows(AccountRecord account, int top) throws Exception {
        String token = refreshAccessToken(account, Constants.IMAP_REFRESH_SCOPES);
        Properties props = new Properties();
        props.put("mail.store.protocol", "imaps");
        props.put("mail.imaps.ssl.enable", "true");
        props.put("mail.imaps.auth.mechanisms", "XOAUTH2");
        props.put("mail.imaps.auth.login.disable", "true");
        props.put("mail.imaps.auth.plain.disable", "true");
        props.put("mail.imaps.connectiontimeout", String.valueOf(Constants.CONNECT_TIMEOUT_MS));
        props.put("mail.imaps.timeout", String.valueOf(Constants.READ_TIMEOUT_MS));

        Session session = Session.getInstance(props);
        Store mailStore = null;
        Folder inbox = null;
        try {
            mailStore = session.getStore("imaps");
            mailStore.connect(Constants.IMAP_HOST, 993, account.email, token);
            inbox = mailStore.getFolder("INBOX");
            inbox.open(Folder.READ_ONLY);
            int count = inbox.getMessageCount();
            if (count <= 0) {
                return new ArrayList<>();
            }
            int start = Math.max(1, count - clampTop(top) + 1);
            Message[] messages = inbox.getMessages(start, count);
            List<MailRow> rows = new ArrayList<>();
            for (int i = messages.length - 1; i >= 0; i--) {
                rows.add(imapRow(account.email, messages[i]));
            }
            return rows;
        } finally {
            if (inbox != null && inbox.isOpen()) {
                try {
                    inbox.close(false);
                } catch (Exception ignored) {
                }
            }
            if (mailStore != null && mailStore.isConnected()) {
                try {
                    mailStore.close();
                } catch (Exception ignored) {
                }
            }
        }
    }

    private String refreshAccessToken(AccountRecord account, List<String> scopes) throws Exception {
        if (account.clientId.isEmpty() || account.refreshToken.isEmpty()) {
            throw new IllegalStateException("缺少 client_id 或 refresh_token");
        }
        String tenant = store.config.tenant == null || store.config.tenant.isEmpty() ? "consumers" : store.config.tenant;
        String tokenUrl = Constants.AUTHORITY_BASE + "/" + tenant + "/oauth2/v2.0/token";
        List<String> errors = new ArrayList<>();
        for (String scope : scopes) {
            StringBuilder body = new StringBuilder();
            appendForm(body, "client_id", account.clientId);
            appendForm(body, "grant_type", "refresh_token");
            appendForm(body, "refresh_token", account.refreshToken);
            if (scope != null) {
                appendForm(body, "scope", scope);
            }
            try {
                HttpResult response = request("POST", tokenUrl, body.toString(), null);
                JSONObject json = response.body.isEmpty() ? new JSONObject() : new JSONObject(response.body);
                if (response.status < 400 && !json.optString("access_token", "").isEmpty()) {
                    String nextRefresh = json.optString("refresh_token", "");
                    if (!nextRefresh.isEmpty()) {
                        store.updateRefreshToken(account.email, nextRefresh);
                        account.refreshToken = nextRefresh;
                    }
                    return json.getString("access_token");
                }
                errors.add(firstNonEmpty(json.optString("error_description", ""), json.optString("error", ""), Parsing.compact(response.body, 300)));
            } catch (Exception exc) {
                errors.add(exc.getMessage());
            }
        }
        throw new IllegalStateException("刷新访问令牌失败：" + String.join(" | ", errors));
    }

    private MailRow conciseRow(MailRow row) {
        MailRow concise = new MailRow();
        concise.account = row.account;
        concise.phone = row.phone;
        concise.protocol = row.protocol;
        concise.time = row.time;
        concise.sender = row.sender;
        concise.read = row.read;
        concise.webLink = row.webLink;
        concise.code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
        concise.subject = concise.code.isEmpty() ? "未识别到验证码" : concise.code;
        concise.preview = "";
        concise.concise = true;
        return concise;
    }

    private MailRow imapRow(String account, Message message) throws Exception {
        MailRow row = new MailRow();
        row.account = account;
        row.protocol = "IMAP";
        Date received = message.getReceivedDate();
        row.time = received == null ? "" : Parsing.fmtDate(new java.text.SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss Z", Locale.US).format(received));
        row.sender = decodeAddresses(message.getFrom());
        row.subject = MimeUtility.decodeText(message.getSubject() == null ? "" : message.getSubject());
        row.read = message.isSet(Flags.Flag.SEEN) ? "是" : "否";
        row.preview = Parsing.compact(extractText(message), 800);
        return row;
    }

    private String extractText(Object part) throws Exception {
        if (part instanceof Message) {
            Message message = (Message) part;
            if (message.isMimeType("text/plain")) {
                Object content = message.getContent();
                return content == null ? "" : String.valueOf(content);
            }
            if (message.isMimeType("multipart/*")) {
                return extractText(message.getContent());
            }
            return "";
        }
        if (part instanceof Multipart) {
            Multipart multipart = (Multipart) part;
            String fallback = "";
            for (int i = 0; i < multipart.getCount(); i++) {
                BodyPart bodyPart = multipart.getBodyPart(i);
                if (bodyPart.getDisposition() != null && bodyPart.getDisposition().equalsIgnoreCase(BodyPart.ATTACHMENT)) {
                    continue;
                }
                if (bodyPart.isMimeType("text/plain")) {
                    Object content = bodyPart.getContent();
                    return content == null ? "" : String.valueOf(content);
                }
                if (bodyPart.isMimeType("multipart/*")) {
                    fallback = firstNonEmpty(fallback, extractText(bodyPart.getContent()));
                }
            }
            return fallback;
        }
        return "";
    }

    private String decodeAddresses(Address[] addresses) throws Exception {
        if (addresses == null || addresses.length == 0) {
            return "";
        }
        List<String> values = new ArrayList<>();
        for (Address address : addresses) {
            values.add(MimeUtility.decodeText(address.toString()));
        }
        return String.join(", ", values);
    }

    private HttpResult request(String method, String urlText, String body, String bearerToken) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(urlText).openConnection();
        try {
            connection.setRequestMethod(method);
            connection.setConnectTimeout(Constants.CONNECT_TIMEOUT_MS);
            connection.setReadTimeout(Constants.READ_TIMEOUT_MS);
            connection.setInstanceFollowRedirects(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", "WREmailAndroid/" + Constants.APP_VERSION);
            if (bearerToken != null && !bearerToken.isEmpty()) {
                connection.setRequestProperty("Authorization", "Bearer " + bearerToken);
                connection.setRequestProperty("Prefer", "outlook.body-content-type=\"text\"");
            }
            if (body != null) {
                byte[] data = body.getBytes(StandardCharsets.UTF_8);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=utf-8");
                connection.setRequestProperty("Content-Length", String.valueOf(data.length));
                try (OutputStream output = connection.getOutputStream()) {
                    output.write(data);
                }
            }
            int status = connection.getResponseCode();
            InputStream stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
            String response = stream == null ? "" : readAll(stream);
            return new HttpResult(status, response);
        } finally {
            connection.disconnect();
        }
    }

    private Object parseJson(String text) {
        try {
            String trimmed = text == null ? "" : text.trim();
            if (trimmed.startsWith("[")) {
                return new JSONArray(trimmed);
            }
            if (trimmed.startsWith("{")) {
                return new JSONObject(trimmed);
            }
        } catch (Exception ignored) {
        }
        return null;
    }

    private String apiCode(Object payload) {
        if (!(payload instanceof JSONObject)) {
            return "";
        }
        JSONObject json = (JSONObject) payload;
        JSONObject data = json.optJSONObject("data");
        if (data != null) {
            String code = Parsing.cleanCode(data.optString("code", ""));
            if (!code.isEmpty()) {
                return code;
            }
        }
        return Parsing.cleanCode(firstNonEmpty(json.optString("code_value", ""), json.optString("verify_code", "")));
    }

    private String apiDataField(Object payload, String key) {
        if (!(payload instanceof JSONObject)) {
            return "";
        }
        JSONObject data = ((JSONObject) payload).optJSONObject("data");
        return data == null ? "" : data.optString(key, "").trim();
    }

    private String optString(Object payload, String key) {
        if (!(payload instanceof JSONObject)) {
            return "";
        }
        Object value = ((JSONObject) payload).opt(key);
        return value == null ? "" : String.valueOf(value).trim();
    }

    private String apiMessage(Object payload) {
        if (!(payload instanceof JSONObject)) {
            return "";
        }
        JSONObject json = (JSONObject) payload;
        List<String> parts = new ArrayList<>();
        if (!json.optString("msg", "").isEmpty()) {
            parts.add(json.optString("msg", ""));
        }
        JSONObject data = json.optJSONObject("data");
        if (data != null) {
            for (String key : new String[]{"code_time", "expired_date", "message", "msg", "content"}) {
                if (!data.optString(key, "").isEmpty()) {
                    parts.add(data.optString(key, ""));
                }
            }
        }
        return String.join(" ", parts);
    }

    private String searchableText(Object payload, String fallback, String phoneNumber) {
        if (payload == null) {
            return preferPhoneText(singletonList(fallback), phoneNumber);
        }
        List<String> chunks = new ArrayList<>();
        walkJson(payload, chunks);
        if (chunks.isEmpty() && fallback != null) {
            chunks.add(fallback);
        }
        return preferPhoneText(chunks, phoneNumber);
    }

    private void walkJson(Object value, List<String> chunks) {
        if (value instanceof JSONObject) {
            JSONObject object = (JSONObject) value;
            StringBuilder chunk = new StringBuilder();
            for (Iterator<String> keys = object.keys(); keys.hasNext(); ) {
                String key = keys.next();
                Object item = object.opt(key);
                chunk.append(key).append(' ');
                if (!(item instanceof JSONObject) && !(item instanceof JSONArray) && item != null) {
                    chunk.append(item).append(' ');
                }
                walkJson(item, chunks);
            }
            String text = chunk.toString().trim();
            if (!text.isEmpty()) {
                chunks.add(text);
            }
        } else if (value instanceof JSONArray) {
            JSONArray array = (JSONArray) value;
            for (int i = 0; i < array.length(); i++) {
                walkJson(array.opt(i), chunks);
            }
        } else if (value != null) {
            chunks.add(String.valueOf(value));
        }
    }

    private String preferPhoneText(List<String> chunks, String phoneNumber) {
        String target = digits(phoneNumber);
        if (!target.isEmpty()) {
            int[] lengths = new int[]{11, 10, 8, 6};
            for (int length : lengths) {
                if (target.length() < length) {
                    continue;
                }
                String suffix = target.substring(target.length() - length);
                List<String> matched = new ArrayList<>();
                for (String chunk : chunks) {
                    if (digits(chunk).contains(suffix)) {
                        matched.add(chunk);
                    }
                }
                if (!matched.isEmpty()) {
                    return String.join(" ", matched);
                }
            }
        }
        return String.join(" ", chunks);
    }

    private String readAll(InputStream stream) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
        StringBuilder builder = new StringBuilder();
        char[] buffer = new char[4096];
        int read;
        while ((read = reader.read(buffer)) != -1) {
            builder.append(buffer, 0, read);
        }
        return builder.toString();
    }

    private void appendForm(StringBuilder builder, String key, String value) throws Exception {
        if (builder.length() > 0) {
            builder.append('&');
        }
        builder.append(encode(key)).append('=').append(encode(value));
    }

    private String encode(String value) throws Exception {
        return URLEncoder.encode(value == null ? "" : value, "UTF-8");
    }

    private int clampTop(int value) {
        return Math.max(1, Math.min(50, value));
    }

    private String digits(String value) {
        return value == null ? "" : value.replaceAll("\\D+", "");
    }

    private String firstNonEmpty(String... values) {
        if (values == null) {
            return "";
        }
        for (String value : values) {
            if (value != null && !value.isEmpty()) {
                return value;
            }
        }
        return "";
    }

    private List<String> singletonList(String value) {
        List<String> list = new ArrayList<>();
        if (value != null) {
            list.add(value);
        }
        return list;
    }

    private static final class HttpResult {
        final int status;
        final String body;

        HttpResult(int status, String body) {
            this.status = status;
            this.body = body == null ? "" : body;
        }
    }
}
