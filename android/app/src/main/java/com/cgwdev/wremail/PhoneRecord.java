package com.cgwdev.wremail;

import java.util.ArrayList;
import java.util.List;

final class PhoneRecord {
    String phone = "";
    String apiUrl = "";
    List<String> emails = new ArrayList<>();
    String importedAt = "";
    String lastFetchAt = "";
    String lastStatus = "未取码";
    String lastCode = "";
    String lastMessage = "";
}
