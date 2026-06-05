package com.cgwdev.wremail;

import java.util.ArrayList;
import java.util.List;

final class ImportResult<T> {
    final List<T> records = new ArrayList<>();
    int invalid = 0;
}
