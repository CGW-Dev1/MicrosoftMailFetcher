package com.cgwdev.wremail;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputType;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final int REQ_IMPORT_ACCOUNTS = 1001;
    private static final int REQ_EXPORT_ACCOUNTS = 1002;
    private static final int REQ_EXPORT_RESULTS = 1003;
    private static final int REQ_IMPORT_PHONES = 1004;
    private static final int REQ_EXPORT_PHONES = 1005;
    private static final int REQ_IMPORT_STANDALONE = 1006;

    private DataStore store;
    private MailService mailService;
    private ExecutorService executor;
    private Handler mainHandler;

    private LinearLayout root;
    private ViewGroup tabBar;
    private FrameLayout content;
    private TextView statusView;
    private LinearLayout progressBox;
    private TextView progressText;
    private ProgressBar progressBar;

    private String page = "fetch";
    private String currentCategory = Constants.CATEGORY_UNUSED;
    private String accountQuery = "";
    private String resultKeyword = "";
    private String resultSender = "";
    private String resultProtocolFilter = "全部";
    private String phoneQuery = "";
    private String standaloneQuery = "";

    private final Set<String> selectedEmails = new HashSet<>();
    private final Set<String> selectedStandalonePhones = new HashSet<>();
    private final List<MailRow> mailRows = new ArrayList<>();

    private LinearLayout accountListBox;
    private LinearLayout latestCodeBox;
    private LinearLayout resultListBox;
    private TextView resultStats;
    private LinearLayout phoneListBox;
    private LinearLayout standaloneListBox;

    private boolean fetchRunning = false;
    private volatile boolean stopRequested = false;
    private String pendingExportText = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mainHandler = new Handler(Looper.getMainLooper());
        executor = Executors.newFixedThreadPool(4);
        store = new DataStore(this);
        store.load();
        mailService = new MailService(store);
        buildShell();
        showPage("fetch");
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        Uri uri = data.getData();
        try {
            if (requestCode == REQ_IMPORT_ACCOUNTS) {
                handleAccountImport(readText(uri));
            } else if (requestCode == REQ_IMPORT_PHONES) {
                handlePhoneImport(readText(uri), false);
            } else if (requestCode == REQ_IMPORT_STANDALONE) {
                handlePhoneImport(readText(uri), true);
            } else if (requestCode == REQ_EXPORT_ACCOUNTS
                    || requestCode == REQ_EXPORT_RESULTS
                    || requestCode == REQ_EXPORT_PHONES) {
                writeText(uri, pendingExportText);
                toast("导出完成");
            }
        } catch (Exception exc) {
            showStatus("文件处理失败：" + exc.getMessage());
            toast("文件处理失败");
        }
    }

    private void buildShell() {
        configureSystemBars();
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(colorBg());
        root.setPadding(dp(12), dp(10), dp(12), dp(8));
        applySystemBarInsets(root);
        setContentView(root);

        root.addView(buildHeader(), matchWrap());
        root.addView(buildProgress(), matchWrap());

        content = new FrameLayout(this);
        root.addView(content, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        root.addView(buildTabs(), matchWrap());
    }

    private void configureSystemBars() {
        Window window = getWindow();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false);
        }
        window.setStatusBarColor(Color.TRANSPARENT);
        window.setNavigationBarColor(colorBg());
        int flags = View.SYSTEM_UI_FLAG_LAYOUT_STABLE;
        if (!store.config.darkTheme) {
            flags |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            }
        }
        window.getDecorView().setSystemUiVisibility(flags);
    }

    private void applySystemBarInsets(View view) {
        final int baseLeft = dp(12);
        final int baseTop = dp(10);
        final int baseRight = dp(12);
        final int baseBottom = dp(8);
        view.setOnApplyWindowInsetsListener((target, insets) -> {
            int left;
            int top;
            int right;
            int bottom;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                left = bars.left;
                top = bars.top;
                right = bars.right;
                bottom = bars.bottom;
            } else {
                left = insets.getSystemWindowInsetLeft();
                top = insets.getSystemWindowInsetTop();
                right = insets.getSystemWindowInsetRight();
                bottom = insets.getSystemWindowInsetBottom();
            }
            target.setPadding(baseLeft + left, baseTop + top, baseRight + right, baseBottom + bottom);
            return insets;
        });
        view.post(view::requestApplyInsets);
    }

    private View buildHeader() {
        LinearLayout header = horizontal();
        header.setPadding(dp(12), dp(9), dp(10), dp(9));
        header.setBackground(cardBg());

        ImageView icon = new ImageView(this);
        icon.setImageDrawable(getApplicationInfo().loadIcon(getPackageManager()));
        icon.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        icon.setContentDescription("应用图标");
        header.addView(icon, new LinearLayout.LayoutParams(dp(42), dp(42)));

        LinearLayout identity = vertical();
        TextView title = label(Constants.DISPLAY_NAME, 17, Typeface.BOLD);
        title.setSingleLine(true);
        title.setEllipsize(TextUtils.TruncateAt.END);
        TextView subtitle = label("移动取件工作台 · " + Constants.APP_VERSION, 11, Typeface.NORMAL);
        subtitle.setTextColor(colorMuted());
        subtitle.setSingleLine(true);
        subtitle.setEllipsize(TextUtils.TruncateAt.END);
        identity.addView(title, matchWrap());
        identity.addView(subtitle, matchWrap());
        LinearLayout.LayoutParams identityParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        identityParams.leftMargin = dp(10);
        header.addView(identity, identityParams);

        statusView = badge("就绪", colorBlue());
        float density = getResources().getDisplayMetrics().density;
        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels / density);
        statusView.setMaxWidth(dp(widthDp < 360 ? 86 : 132));
        statusView.setSingleLine(true);
        statusView.setEllipsize(TextUtils.TruncateAt.END);
        LinearLayout.LayoutParams statusParams = wrapWrap();
        statusParams.leftMargin = dp(8);
        header.addView(statusView, statusParams);
        return header;
    }

    private View buildTabs() {
        LinearLayout bar = horizontal();
        bar.setPadding(dp(4), dp(8), dp(4), dp(8));
        bar.setBackground(bottomNavBg());
        tabBar = bar;
        addTab("取件", "fetch");
        addTab("邮箱", "mailboxes");
        addTab("结果", "results");
        addTab("设置", "settings");
        return tabBar;
    }

    private View buildProgress() {
        LinearLayout box = vertical();
        progressBox = box;
        box.setPadding(dp(10), dp(6), dp(10), dp(8));
        box.setVisibility(View.GONE);
        progressText = label("等待任务", 12, Typeface.NORMAL);
        progressText.setTextColor(colorMuted());
        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        progressBar.setProgress(0);
        progressBar.setProgressTintList(android.content.res.ColorStateList.valueOf(colorBlue()));
        progressBar.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(colorBorder()));
        progressBar.setVisibility(View.GONE);
        box.addView(progressText, matchWrap());
        LinearLayout.LayoutParams barParams = matchWrap();
        barParams.topMargin = dp(5);
        box.addView(progressBar, barParams);
        return box;
    }

    private void addTab(String label, String target) {
        Button button = button(label, target.equals(page) ? "nav-active" : "nav");
        button.setOnClickListener(v -> showPage(target));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(48), 1);
        params.leftMargin = dp(3);
        params.rightMargin = dp(3);
        tabBar.addView(button, params);
    }

    private void refreshTabs() {
        tabBar.removeAllViews();
        addTab("取件", "fetch");
        addTab("邮箱", "mailboxes");
        addTab("结果", "results");
        addTab("设置", "settings");
    }

    private void showPage(String target) {
        page = target;
        if (tabBar != null) {
            refreshTabs();
        }
        content.removeAllViews();
        if ("results".equals(target)) {
            renderResultsPage();
        } else if ("mailboxes".equals(target)) {
            renderMailboxesPage();
        } else if ("phones".equals(target)) {
            renderPhonesPage();
        } else if ("standalone".equals(target)) {
            renderStandalonePage();
        } else if ("settings".equals(target)) {
            renderSettingsPage();
        } else {
            renderFetchPage();
        }
    }

    private void renderFetchPage() {
        LinearLayout pageBox = vertical();
        pageBox.setPadding(0, 0, 0, dp(16));
        content.addView(scroll(pageBox), matchMatch());
        latestCodeBox = null;

        pageBox.addView(pageHeader("取件", "选择邮箱与通道，验证码会集中显示在结果页"), matchWrap());

        pageBox.addView(statsCard(), spaced());

        latestCodeBox = vertical();
        latestCodeBox.addView(latestCodeCard(), matchWrap());
        pageBox.addView(latestCodeBox, spaced());

        pageBox.addView(fetchDeskCard(), spaced());

        pageBox.addView(fetchSearchCard(), spaced());

        pageBox.addView(recentResultsCard(), spaced());
    }

    private void renderMailboxesPage() {
        String resolvedCategory = store.resolveCategory(currentCategory);
        currentCategory = resolvedCategory == null ? Constants.CATEGORY_UNUSED : resolvedCategory;
        LinearLayout pageBox = vertical();
        pageBox.setPadding(0, 0, 0, dp(16));
        content.addView(scroll(pageBox), matchMatch());

        pageBox.addView(pageHeader("邮箱库", "分类、标签与手机号绑定统一管理"), matchWrap());

        pageBox.addView(mailboxHeaderCard(), spaced());

        EditText search = edit("搜索邮箱、标签、状态或手机号");
        search.setText(accountQuery);
        search.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                accountQuery = editable.toString();
                renderAccountList();
            }
        });
        pageBox.addView(search, spaced());

        pageBox.addView(categoryBar(), spaced());

        pageBox.addView(accountManageCard(), spaced());

        accountListBox = vertical();
        pageBox.addView(accountListBox, matchWrap());
        renderAccountList();
    }

    private View statsCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(11), dp(12), dp(10));
        card.setBackground(cardBg());

        TextView title = label("取件概览", 15, Typeface.BOLD);
        card.addView(title, matchWrap());

        LinearLayout row = horizontal();
        row.setPadding(0, dp(8), 0, 0);
        row.addView(statCell("邮箱", String.valueOf(store.accounts.size()), colorBlue()), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.addView(statCell("Graph", String.valueOf(countRows("GRAPH")), colorGreen()), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.addView(statCell("IMAP", String.valueOf(countRows("IMAP")), colorBlue()), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.addView(statCell("SMS", String.valueOf(countRows("SMS")), colorGreen()), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        card.addView(row, matchWrap());
        return card;
    }

    private View statCell(String title, String value, int accent) {
        LinearLayout cell = vertical();
        cell.setGravity(Gravity.CENTER);
        TextView number = label(value, 19, Typeface.BOLD);
        number.setTextColor(accent);
        number.setGravity(Gravity.CENTER);
        TextView name = label(title, 11, Typeface.NORMAL);
        name.setTextColor(colorMuted());
        name.setGravity(Gravity.CENTER);
        cell.addView(number, matchWrap());
        cell.addView(name, matchWrap());
        return cell;
    }

    private View fetchSearchCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(12), dp(12), dp(12));
        card.setBackground(cardBg());
        TextView title = label("搜索条件", 15, Typeface.BOLD);
        card.addView(title, matchWrap());

        EditText email = edit("邮箱搜索");
        email.setText(accountQuery);
        email.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                accountQuery = editable.toString();
            }
        });
        card.addView(email, spaced());

        EditText sender = edit("发件人搜索");
        sender.setText(resultSender);
        sender.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                resultSender = editable.toString();
            }
        });
        card.addView(sender, spaced());
        return card;
    }

    private View fetchConfigCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(8), dp(12), dp(8));
        card.setBackground(softCardBg());
        card.addView(settingRow("每次取件", store.config.top + " 封", v -> chooseTopCount()), matchWrap());
        card.addView(settingRow("协议", store.config.protocol.equalsIgnoreCase("IMAP") ? "IMAP 优先" : "Graph 优先", v -> chooseProtocol()), matchWrap());
        return card;
    }

    private View settingRow(String title, String value, View.OnClickListener listener) {
        LinearLayout row = horizontal();
        row.setPadding(dp(2), dp(8), dp(2), dp(8));
        row.setOnClickListener(listener);
        TextView left = label(title, 14, Typeface.BOLD);
        row.addView(left, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        TextView right = label(value + "  >", 14, Typeface.NORMAL);
        right.setTextColor(colorMuted());
        row.addView(right, wrapWrap());
        return row;
    }

    private View pageHeader(String title, String subtitle) {
        LinearLayout box = vertical();
        box.setPadding(dp(2), dp(14), dp(2), dp(4));
        TextView heading = label(title, 21, Typeface.BOLD);
        TextView supporting = label(subtitle, 12, Typeface.NORMAL);
        supporting.setTextColor(colorMuted());
        supporting.setPadding(0, dp(2), 0, 0);
        box.addView(heading, matchWrap());
        box.addView(supporting, matchWrap());
        return box;
    }

    private View actionGrid(Button... buttons) {
        LinearLayout grid = vertical();
        for (int i = 0; i < buttons.length; i += 2) {
            LinearLayout row = horizontal();
            row.addView(buttons[i], equalButtonParams(2, 0));
            if (i + 1 < buttons.length) {
                row.addView(buttons[i + 1], equalButtonParams(2, 1));
            } else {
                View spacer = new View(this);
                row.addView(spacer, equalButtonParams(2, 1));
            }
            if (i > 0) {
                LinearLayout.LayoutParams rowParams = matchWrap();
                rowParams.topMargin = dp(8);
                grid.addView(row, rowParams);
            } else {
                grid.addView(row, matchWrap());
            }
        }
        return grid;
    }

    private View mailboxHeaderCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(12), dp(12), dp(8));
        card.setBackground(cardBg());
        LinearLayout top = horizontal();
        TextView title = label("邮箱池", 19, Typeface.BOLD);
        top.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        top.addView(button("导入", "primary", v -> showPasteDialog("批量导入邮箱", true, false)), wrapWrap());
        card.addView(top, matchWrap());

        TextView meta = label("全部 " + store.accounts.size() + " · 已选 " + selectedEmails.size(), 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        card.addView(meta, spaced());

        ViewGroup actions = horizontalWrap();
        actions.addView(button("文件导入", "secondary", v -> openTextFile(REQ_IMPORT_ACCOUNTS)), buttonParams());
        actions.addView(button("导出邮箱", "secondary", v -> exportAccounts()), buttonParams());
        card.addView(actions, spaced());
        return card;
    }

    private View recentResultsCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(12), dp(12), dp(8));
        card.setBackground(cardBg());
        LinearLayout top = horizontal();
        TextView title = label("最近结果", 16, Typeface.BOLD);
        top.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        top.addView(button("全部", "secondary", v -> showPage("results")), wrapWrap());
        card.addView(top, matchWrap());

        List<MailRow> rows = recentRows(3);
        if (rows.isEmpty()) {
            TextView empty = label("暂无结果", 14, Typeface.NORMAL);
            empty.setTextColor(colorMuted());
            empty.setGravity(Gravity.CENTER);
            empty.setPadding(0, dp(18), 0, dp(16));
            card.addView(empty, matchWrap());
            return card;
        }
        for (MailRow row : rows) {
            card.addView(compactResultRow(row), spaced());
        }
        return card;
    }

    private View compactResultRow(MailRow row) {
        LinearLayout item = horizontal();
        item.setPadding(dp(2), dp(6), dp(2), dp(6));
        String code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
        TextView codeView = label(code.isEmpty() ? "未识别" : code, 20, Typeface.BOLD);
        codeView.setTextColor(code.isEmpty() ? colorMuted() : colorBlue());
        item.addView(codeView, new LinearLayout.LayoutParams(dp(96), ViewGroup.LayoutParams.WRAP_CONTENT));
        LinearLayout text = vertical();
        TextView account = label(Parsing.compact(firstNonEmpty(row.account, row.phone), 42), 13, Typeface.BOLD);
        TextView meta = label(row.protocol + " · " + row.time, 11, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        text.addView(account, matchWrap());
        text.addView(meta, matchWrap());
        item.addView(text, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button copy = button("复制", code.isEmpty() ? "disabled" : "secondary", v -> copy(code, "已复制验证码"));
        copy.setEnabled(!code.isEmpty());
        item.addView(copy, wrapWrap());
        return item;
    }

    private void renderLatestCodeBox() {
        if (latestCodeBox == null) {
            return;
        }
        latestCodeBox.removeAllViews();
        latestCodeBox.addView(latestCodeCard(), matchWrap());
    }

    private View latestCodeCard() {
        MailRow row = latestCodeRow();
        LinearLayout card = vertical();
        card.setPadding(dp(14), dp(13), dp(14), dp(13));
        card.setBackground(row == null ? cardBg() : heroCardBg());

        if (row == null) {
            TextView title = label("最新验证码", 16, Typeface.BOLD);
            card.addView(title, matchWrap());
            TextView hint = label("取邮箱或手机号验证码后，会直接显示在这里。", 13, Typeface.NORMAL);
            hint.setTextColor(colorMuted());
            LinearLayout.LayoutParams hintParams = matchWrap();
            hintParams.topMargin = dp(6);
            card.addView(hint, hintParams);
            ViewGroup actions = horizontalWrap();
            actions.addView(button("导入账号", "primary", v -> showPasteDialog("批量导入邮箱", true, false)), buttonParams());
            actions.addView(button("手机号取码", "secondary", v -> showPage("phones")), buttonParams());
            LinearLayout.LayoutParams actionParams = matchWrap();
            actionParams.topMargin = dp(10);
            card.addView(actions, actionParams);
            return card;
        }

        String code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
        TextView eyebrow = label(row.protocol + " · " + firstNonEmpty(row.time, "刚刚"), 12, Typeface.BOLD);
        eyebrow.setTextColor(Color.WHITE);
        card.addView(eyebrow, matchWrap());

        TextView codeView = label(code.isEmpty() ? "未识别" : code, 34, Typeface.BOLD);
        codeView.setTextColor(Color.WHITE);
        codeView.setTextIsSelectable(true);
        LinearLayout.LayoutParams codeParams = matchWrap();
        codeParams.topMargin = dp(6);
        card.addView(codeView, codeParams);

        String metaText = firstNonEmpty(row.account, row.phone);
        if (!row.sender.isEmpty()) {
            metaText += " · " + Parsing.shortSender(row.sender);
        }
        TextView meta = label(Parsing.compact(metaText, 96), 12, Typeface.NORMAL);
        meta.setTextColor(Color.argb(220, 255, 255, 255));
        card.addView(meta, matchWrap());

        ViewGroup actions = horizontalWrap();
        Button copyCode = button(code.isEmpty() ? "无验证码" : "复制验证码", code.isEmpty() ? "disabled" : "hero", v -> copy(code, "已复制验证码"));
        copyCode.setEnabled(!code.isEmpty());
        actions.addView(copyCode, buttonParams());
        actions.addView(button("查看详情", "hero-soft", v -> showRowDetail(row)), buttonParams());
        actions.addView(button("全部结果", "hero-soft", v -> showPage("results")), buttonParams());
        LinearLayout.LayoutParams actionParams = matchWrap();
        actionParams.topMargin = dp(10);
        card.addView(actions, actionParams);
        return card;
    }

    private MailRow latestCodeRow() {
        MailRow fallback = null;
        synchronized (mailRows) {
            for (MailRow row : mailRows) {
                if (fallback == null) {
                    fallback = row;
                }
                String code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
                if (!code.isEmpty()) {
                    return row;
                }
            }
        }
        return fallback;
    }

    private View fetchDeskCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(12), dp(12), dp(10));
        card.setBackground(cardBg());

        TextView title = label("取件工作台", 16, Typeface.BOLD);
        card.addView(title, matchWrap());

        int selected = 0;
        for (String email : selectedEmails) {
            if (store.getAccount(email) != null) {
                selected++;
            }
        }
        TextView meta = label("已选 " + selected + " 个 · 匹配 " + fetchCandidateAccounts().size() + " 个 · 全部 " + store.accounts.size() + " 个", 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        card.addView(meta, matchWrap());

        LinearLayout.LayoutParams topSettingParams = matchWrap();
        topSettingParams.topMargin = dp(8);
        card.addView(settingRow("每次取件", store.config.top + " 封", v -> chooseTopCount()), topSettingParams);
        card.addView(settingRow("协议", store.config.protocol.equalsIgnoreCase("IMAP") ? "IMAP 优先" : "Graph 优先", v -> chooseProtocol()), matchWrap());

        View primaryActions = actionGrid(
                button("全部取件", "primary", v -> fetchAccounts(emailsOf(store.accounts))),
                button("取选中", "primary", v -> fetchSelected()),
                button("选择邮箱", "secondary", v -> showFetchAccountPicker()),
                button("停止", "danger", v -> requestStop())
        );
        LinearLayout.LayoutParams primaryParams = matchWrap();
        primaryParams.topMargin = dp(12);
        card.addView(primaryActions, primaryParams);
        return card;
    }

    private View accountManageCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(10), dp(12), dp(6));
        card.setBackground(softCardBg());

        TextView title = label("账号管理", 14, Typeface.BOLD);
        card.addView(title, matchWrap());

        ViewGroup actions = horizontalWrap();
        actions.addView(button("移动分类", "secondary", v -> showMoveDialog()), buttonParams());
        actions.addView(button("管理分类", "secondary", v -> showCategoryManager()), buttonParams());
        actions.addView(button("导出账号", "secondary", v -> exportAccounts()), buttonParams());
        actions.addView(button("删除选中", "danger", v -> deleteSelectedAccounts()), buttonParams());
        actions.addView(button("清空账号", "danger", v -> clearAccounts()), buttonParams());
        LinearLayout.LayoutParams actionParams = matchWrap();
        actionParams.topMargin = dp(6);
        card.addView(actions, actionParams);
        return card;
    }

    private View categoryBar() {
        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        LinearLayout row = horizontal();
        List<AccountCategory> categories = store.categorySnapshot();
        for (AccountCategory category : categories) {
            String text = category.label + "  " + countCategory(category.key);
            Button button = button(text, category.key.equals(currentCategory) ? "segment-active" : "segment");
            button.setOnClickListener(v -> {
                currentCategory = category.key;
                showPage("mailboxes");
            });
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(42));
            params.rightMargin = dp(8);
            row.addView(button, params);
        }
        scroll.addView(row, new HorizontalScrollView.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return scroll;
    }

    private void renderAccountList() {
        if (accountListBox == null) {
            return;
        }
        accountListBox.removeAllViews();
        List<AccountRecord> accounts = filteredAccounts();
        TextView count = label("当前 " + store.categoryLabel(currentCategory) + "：" + accounts.size() + " 个账号", 13, Typeface.BOLD);
        count.setTextColor(colorMuted());
        accountListBox.addView(count, spaced());
        if (accounts.isEmpty()) {
            accountListBox.addView(emptyText("没有匹配的账号"), spaced());
            return;
        }
        for (AccountRecord account : accounts) {
            accountListBox.addView(accountCard(account), spaced());
        }
    }

    private View accountCard(AccountRecord account) {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(cardBg());

        LinearLayout top = horizontal();
        CheckBox check = new CheckBox(this);
        check.setChecked(selectedEmails.contains(account.email));
        check.setButtonTintList(android.content.res.ColorStateList.valueOf(colorBlue()));
        check.setOnCheckedChangeListener((buttonView, checked) -> {
            if (checked) {
                selectedEmails.add(account.email);
            } else {
                selectedEmails.remove(account.email);
            }
        });
        top.addView(check, new LinearLayout.LayoutParams(dp(42), ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout textBox = vertical();
        TextView email = label(account.email, 15, Typeface.BOLD);
        textBox.addView(email, matchWrap());
        String phone = account.phone.isEmpty() ? "" : " · " + account.phone;
        String tag = account.tag.isEmpty() ? "" : " · 标签:" + account.tag;
        TextView meta = label(store.categoryLabel(account.category) + " · " + account.source() + phone + tag + " · " + account.lastStatus, 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        textBox.addView(meta, matchWrap());
        top.addView(textBox, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        card.addView(top, matchWrap());

        Button mailButton = button("邮件取件", "primary", v -> fetchAccounts(singleton(account.email)));
        Button phoneButton = button("手机取码", account.phone.isEmpty() ? "disabled" : "primary", v -> fetchAccountPhone(account.email));
        phoneButton.setEnabled(!account.phone.isEmpty());
        String tagButtonText = account.tag.isEmpty() ? "标签" : Parsing.compact(account.tag, 8);
        String tagButtonRole = account.tag.isEmpty() ? "secondary" : "tagged";
        View actions = actionGrid(
                mailButton,
                phoneButton,
                button("复制邮箱", "secondary", v -> copy(account.email, "已复制邮箱")),
                button(tagButtonText, tagButtonRole, v -> editTag(account))
        );
        LinearLayout.LayoutParams params = matchWrap();
        params.topMargin = dp(8);
        card.addView(actions, params);
        return card;
    }

    private void renderResultsPage() {
        LinearLayout pageBox = vertical();
        content.addView(scroll(pageBox), matchMatch());

        LinearLayout header = horizontal();
        header.addView(pageHeader("验证码与邮件", "按通道筛选、搜索并复制结果"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        header.addView(button("导出", "primary", v -> exportResultsCsv()), wrapWrap());
        pageBox.addView(header, matchWrap());

        pageBox.addView(resultFilterBar(), spaced());

        LinearLayout searchRow = vertical();
        EditText keyword = edit("搜索邮件内容、账号、验证码");
        keyword.setText(resultKeyword);
        keyword.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                resultKeyword = editable.toString();
                renderResultsList();
            }
        });
        searchRow.addView(keyword, matchWrap());
        EditText sender = edit("按发件人搜索");
        sender.setText(resultSender);
        sender.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                resultSender = editable.toString();
                renderResultsList();
            }
        });
        searchRow.addView(sender, spaced());
        LinearLayout.LayoutParams searchParams = matchWrap();
        searchParams.topMargin = dp(10);
        pageBox.addView(searchRow, searchParams);

        ViewGroup actions = horizontalWrap();
        actions.addView(button("复制全部", "secondary", v -> copyAllCodes()), buttonParams());
        actions.addView(button("清空结果", "danger", v -> {
            mailRows.clear();
            renderResultsList();
            showStatus("已清空结果");
        }), buttonParams());
        pageBox.addView(actions, spaced());

        resultStats = label("", 13, Typeface.BOLD);
        resultStats.setTextColor(colorMuted());
        pageBox.addView(resultStats, spaced());

        resultListBox = vertical();
        pageBox.addView(resultListBox, matchWrap());
        renderResultsList();
    }

    private View resultFilterBar() {
        LinearLayout row = horizontal();
        renderResultFilterButtons(row);
        return row;
    }

    private void renderResultFilterButtons(LinearLayout row) {
        row.removeAllViews();
        String[] filters = {"全部", "GRAPH", "IMAP", "SMS"};
        for (int i = 0; i < filters.length; i++) {
            String filter = filters[i];
            String label = "GRAPH".equals(filter) ? "Graph" : filter;
            Button button = button(label, resultProtocolFilter.equals(filter) ? "primary" : "secondary", v -> {
                resultProtocolFilter = filter;
                renderResultFilterButtons(row);
                renderResultsList();
            });
            row.addView(button, equalButtonParams(filters.length, i));
        }
    }

    private void renderResultsList() {
        if (resultListBox == null) {
            return;
        }
        resultListBox.removeAllViews();
        List<MailRow> rows = filteredRows();
        int graph = 0;
        int imap = 0;
        int sms = 0;
        for (MailRow row : rows) {
            if ("GRAPH".equals(row.protocol)) {
                graph++;
            } else if ("IMAP".equals(row.protocol)) {
                imap++;
            } else if ("SMS".equals(row.protocol)) {
                sms++;
            }
        }
        if (resultStats != null) {
            resultStats.setText("共 " + rows.size() + " 条 · Graph " + graph + " · IMAP " + imap + " · SMS " + sms);
        }
        if (rows.isEmpty()) {
            resultListBox.addView(emptyText("没有取件结果"), spaced());
            return;
        }
        for (MailRow row : rows) {
            resultListBox.addView(resultCard(row), spaced());
        }
    }

    private View resultCard(MailRow row) {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(cardBg());

        String code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
        LinearLayout top = horizontal();
        TextView sender = label(Parsing.shortSender(row.sender), 14, Typeface.BOLD);
        top.addView(sender, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        TextView badge = badge(row.protocol, "SMS".equals(row.protocol) ? colorBlue() : colorGreen());
        top.addView(badge, wrapWrap());
        card.addView(top, matchWrap());

        TextView codeTitle = label(code.isEmpty() ? "未识别验证码" : code, 28, Typeface.BOLD);
        codeTitle.setTextColor(code.isEmpty() ? colorMuted() : colorBlue());
        codeTitle.setTextIsSelectable(true);
        LinearLayout.LayoutParams codeTitleParams = matchWrap();
        codeTitleParams.topMargin = dp(8);
        card.addView(codeTitle, codeTitleParams);

        TextView subject = label(firstNonEmpty(row.subject, "(无主题)"), 14, Typeface.BOLD);
        subject.setTextColor(colorText());
        LinearLayout.LayoutParams subjectParams = matchWrap();
        subjectParams.topMargin = dp(3);
        card.addView(subject, subjectParams);

        TextView preview = label(row.concise && row.preview.isEmpty() ? "简洁模式：仅展示验证码" : Parsing.compact(row.preview, 180), 12, Typeface.NORMAL);
        preview.setTextColor(colorMuted());
        card.addView(preview, matchWrap());

        TextView meta = label(row.time + " · " + row.account + (row.phone.isEmpty() ? "" : " · " + row.phone), 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        card.addView(meta, matchWrap());

        ViewGroup actions = horizontalWrap();
        Button copyCode = button(code.isEmpty() ? "无验证码" : "复制 " + code, code.isEmpty() ? "disabled" : "primary", v -> copy(code, "已复制验证码"));
        copyCode.setEnabled(!code.isEmpty());
        actions.addView(copyCode, buttonParams());
        actions.addView(button("详情", "secondary", v -> showRowDetail(row)), buttonParams());
        if (!row.webLink.isEmpty()) {
            actions.addView(button("打开网页", "secondary", v -> openUrl(row.webLink)), buttonParams());
        }
        LinearLayout.LayoutParams params = matchWrap();
        params.topMargin = dp(8);
        card.addView(actions, params);
        return card;
    }

    private void renderPhonesPage() {
        LinearLayout pageBox = vertical();
        content.addView(scroll(pageBox), matchMatch());

        pageBox.addView(pageHeader("手机号管理", "维护 API、邮箱绑定和验证码状态"), matchWrap());

        EditText search = edit("搜索手机号、API、绑定邮箱或状态");
        search.setText(phoneQuery);
        search.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                phoneQuery = editable.toString();
                renderPhoneList();
            }
        });
        pageBox.addView(search, spaced());

        ViewGroup actions = horizontalWrap();
        actions.addView(button("粘贴导入", "primary", v -> showPasteDialog("导入手机号", false, false)), buttonParams());
        actions.addView(button("文件导入", "secondary", v -> openTextFile(REQ_IMPORT_PHONES)), buttonParams());
        actions.addView(button("导出手机号", "secondary", v -> exportPhones()), buttonParams());
        pageBox.addView(actions, spaced());

        phoneListBox = vertical();
        pageBox.addView(phoneListBox, matchWrap());
        renderPhoneList();
    }

    private void renderPhoneList() {
        if (phoneListBox == null) {
            return;
        }
        phoneListBox.removeAllViews();
        List<PhoneRecord> phones = filteredPhones(false);
        TextView count = label("手机号：" + phones.size() + " 个", 13, Typeface.BOLD);
        count.setTextColor(colorMuted());
        phoneListBox.addView(count, spaced());
        if (phones.isEmpty()) {
            phoneListBox.addView(emptyText("没有手机号"), spaced());
            return;
        }
        for (PhoneRecord phone : phones) {
            phoneListBox.addView(phoneCard(phone), spaced());
        }
    }

    private View phoneCard(PhoneRecord phone) {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(cardBg());
        TextView title = label(phone.phone, 16, Typeface.BOLD);
        card.addView(title, matchWrap());
        TextView meta = label(phone.emails.size() + "/3 · " + (phone.emails.isEmpty() ? "未绑定" : String.join(", ", phone.emails)) + " · " + phone.lastStatus, 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        card.addView(meta, matchWrap());
        if (!phone.lastCode.isEmpty()) {
            TextView code = label("验证码：" + phone.lastCode, 14, Typeface.BOLD);
            code.setTextColor(colorBlue());
            card.addView(code, matchWrap());
        }
        Button clearBindings = button("清空绑定", "secondary", v -> {
            store.clearPhoneBindings(phone.phone);
            showStatus("已清空绑定：" + phone.phone);
            renderPhoneList();
            if ("mailboxes".equals(page)) {
                renderAccountList();
            }
        });
        View actions = actionGrid(
                button("获取验证码", "primary", v -> fetchPhone(phone, false, true)),
                button("绑定邮箱", "secondary", v -> showBindDialog(phone)),
                button("复制手机号", "secondary", v -> copy(phone.phone, "已复制手机号")),
                clearBindings,
                button("删除手机号", "danger", v -> confirm("删除手机号", "确定删除 " + phone.phone + " 吗？", () -> {
                    store.removePhone(phone.phone);
                    renderPhoneList();
                    showStatus("已删除手机号");
                }))
        );
        LinearLayout.LayoutParams params = matchWrap();
        params.topMargin = dp(8);
        card.addView(actions, params);
        return card;
    }

    private void renderStandalonePage() {
        LinearLayout pageBox = vertical();
        content.addView(scroll(pageBox), matchMatch());

        pageBox.addView(pageHeader("手机号取码", "独立于邮箱账号，批量获取并复制短信验证码"), matchWrap());

        EditText search = edit("搜索手机号、验证码、短信内容或状态");
        search.setText(standaloneQuery);
        search.addTextChangedListener(new SimpleWatcher() {
            @Override
            public void afterTextChanged(Editable editable) {
                standaloneQuery = editable.toString();
                renderStandaloneList();
            }
        });
        pageBox.addView(search, spaced());

        ViewGroup importRow = horizontalWrap();
        importRow.addView(button("粘贴导入", "primary", v -> showPasteDialog("独立导入手机号", false, true)), buttonParams());
        importRow.addView(button("文件导入", "secondary", v -> openTextFile(REQ_IMPORT_STANDALONE)), buttonParams());
        importRow.addView(button("清空列表", "danger", v -> confirm("清空列表", "确定清空独立取码列表吗？", () -> {
            store.clearStandalonePhones();
            selectedStandalonePhones.clear();
            renderStandaloneList();
        })), buttonParams());
        pageBox.addView(importRow, spaced());

        ViewGroup fetchRow = horizontalWrap();
        fetchRow.addView(button("取选中", "primary", v -> fetchStandalone(false)), buttonParams());
        fetchRow.addView(button("全部取码", "primary", v -> fetchStandalone(true)), buttonParams());
        fetchRow.addView(button("停止", "danger", v -> requestStop()), buttonParams());
        pageBox.addView(fetchRow, spaced());

        standaloneListBox = vertical();
        pageBox.addView(standaloneListBox, matchWrap());
        renderStandaloneList();
    }

    private void renderStandaloneList() {
        if (standaloneListBox == null) {
            return;
        }
        standaloneListBox.removeAllViews();
        List<PhoneRecord> phones = filteredPhones(true);
        TextView count = label("独立取码：" + phones.size() + " 个手机号", 13, Typeface.BOLD);
        count.setTextColor(colorMuted());
        standaloneListBox.addView(count, spaced());
        if (phones.isEmpty()) {
            standaloneListBox.addView(emptyText("没有独立取码手机号"), spaced());
            return;
        }
        for (PhoneRecord phone : phones) {
            standaloneListBox.addView(standaloneCard(phone), spaced());
        }
    }

    private View standaloneCard(PhoneRecord phone) {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setBackground(cardBg());
        LinearLayout top = horizontal();
        CheckBox check = new CheckBox(this);
        check.setChecked(selectedStandalonePhones.contains(phone.phone));
        check.setButtonTintList(android.content.res.ColorStateList.valueOf(colorBlue()));
        check.setOnCheckedChangeListener((buttonView, checked) -> {
            if (checked) {
                selectedStandalonePhones.add(phone.phone);
            } else {
                selectedStandalonePhones.remove(phone.phone);
            }
        });
        top.addView(check, new LinearLayout.LayoutParams(dp(42), ViewGroup.LayoutParams.WRAP_CONTENT));
        LinearLayout text = vertical();
        text.addView(label(phone.phone, 16, Typeface.BOLD), matchWrap());
        TextView meta = label(phone.lastStatus + (phone.lastCode.isEmpty() ? "" : " · " + phone.lastCode), 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        text.addView(meta, matchWrap());
        top.addView(text, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        card.addView(top, matchWrap());
        if (!phone.lastMessage.isEmpty()) {
            TextView message = label(Parsing.compact(phone.lastMessage, 180), 12, Typeface.NORMAL);
            message.setTextColor(colorMuted());
            card.addView(message, matchWrap());
        }
        Button fetch = button("获取验证码", "primary", v -> fetchPhone(phone, true, false));
        Button copyCode = button("复制码", phone.lastCode.isEmpty() ? "disabled" : "secondary", v -> copy(phone.lastCode, "已复制验证码"));
        copyCode.setEnabled(!phone.lastCode.isEmpty());
        Button copySms = button("复制短信", phone.lastMessage.isEmpty() ? "disabled" : "secondary", v -> copy(phone.lastMessage, "已复制短信"));
        copySms.setEnabled(!phone.lastMessage.isEmpty());
        View actions = actionGrid(
                fetch,
                copyCode,
                button("复制手机号", "secondary", v -> copy(Parsing.phoneWithoutCountryCode(phone.phone), "已复制手机号")),
                copySms,
                button("删除手机号", "danger", v -> confirm("删除手机号", "确定删除 " + phone.phone + " 吗？", () -> {
                    store.removeStandalonePhone(phone.phone);
                    selectedStandalonePhones.remove(phone.phone);
                    renderStandaloneList();
                }))
        );
        LinearLayout.LayoutParams params = matchWrap();
        params.topMargin = dp(8);
        card.addView(actions, params);
        return card;
    }

    private void renderSettingsPage() {
        LinearLayout pageBox = vertical();
        pageBox.setPadding(0, 0, 0, dp(12));
        content.addView(scroll(pageBox), matchMatch());

        pageBox.addView(pageHeader("设置", "配置取件协议、显示模式与常用入口"), matchWrap());

        pageBox.addView(settingsEntryCard(), spaced());

        LinearLayout connectionCard = vertical();
        connectionCard.setPadding(dp(12), dp(12), dp(12), dp(12));
        connectionCard.setBackground(cardBg());
        connectionCard.addView(label("连接与取件", 15, Typeface.BOLD), matchWrap());

        EditText clientId = edit("全局 Client ID（可空）");
        clientId.setText(store.config.clientId);
        connectionCard.addView(clientId, spaced());

        EditText tenant = edit("Tenant，例如 consumers");
        tenant.setText(store.config.tenant);
        connectionCard.addView(tenant, spaced());

        TextView protocolLabel = label("协议", 13, Typeface.BOLD);
        protocolLabel.setTextColor(colorMuted());
        connectionCard.addView(protocolLabel, spaced());
        String[] draftProtocol = {"IMAP".equalsIgnoreCase(store.config.protocol) ? "IMAP" : "Graph"};
        LinearLayout protocol = horizontal();
        Runnable[] renderProtocol = new Runnable[1];
        renderProtocol[0] = () -> {
            protocol.removeAllViews();
            Button graph = button("Graph 令牌", "Graph".equals(draftProtocol[0]) ? "segment-active" : "segment", v -> {
                draftProtocol[0] = "Graph";
                renderProtocol[0].run();
            });
            Button imap = button("IMAP 令牌", "IMAP".equals(draftProtocol[0]) ? "segment-active" : "segment", v -> {
                draftProtocol[0] = "IMAP";
                renderProtocol[0].run();
            });
            protocol.addView(graph, equalButtonParams(2, 0));
            protocol.addView(imap, equalButtonParams(2, 1));
        };
        renderProtocol[0].run();
        connectionCard.addView(protocol, spaced());

        TextView topLabel = label("每个账号读取封数", 13, Typeface.BOLD);
        topLabel.setTextColor(colorMuted());
        connectionCard.addView(topLabel, spaced());
        int[] draftTop = {store.config.top};
        Button top = button(draftTop[0] + " 封", "secondary");
        top.setOnClickListener(v -> {
            String[] values = {"1 封", "5 封", "10 封", "20 封", "30 封", "50 封"};
            int[] numbers = {1, 5, 10, 20, 30, 50};
            AlertDialog dialog = new AlertDialog.Builder(this)
                    .setTitle("每个账号读取封数")
                    .setItems(values, (opened, which) -> {
                        draftTop[0] = numbers[which];
                        top.setText(values[which]);
                    })
                    .create();
            showThemedDialog(dialog);
        });
        connectionCard.addView(top, spaced());
        pageBox.addView(connectionCard, spaced());

        LinearLayout displayCard = vertical();
        displayCard.setPadding(dp(12), dp(12), dp(12), dp(12));
        displayCard.setBackground(cardBg());
        displayCard.addView(label("体验偏好", 15, Typeface.BOLD), matchWrap());
        CheckBox autoFetch = checkbox("导入后自动取件", store.config.autoFetchAfterImport);
        displayCard.addView(autoFetch, spaced());
        CheckBox concise = checkbox("简洁模式：只提取最新验证码", store.config.conciseMode);
        displayCard.addView(concise, spaced());
        CheckBox dark = checkbox("深色模式", store.config.darkTheme);
        displayCard.addView(dark, spaced());
        pageBox.addView(displayCard, spaced());

        Button save = button("保存设置", "primary", v -> {
            boolean themeChanged = store.config.darkTheme != dark.isChecked();
            store.config.clientId = clientId.getText().toString().trim();
            store.config.tenant = tenant.getText().toString().trim().isEmpty() ? "consumers" : tenant.getText().toString().trim();
            store.config.protocol = draftProtocol[0];
            store.config.top = draftTop[0];
            store.config.autoFetchAfterImport = autoFetch.isChecked();
            store.config.conciseMode = concise.isChecked();
            store.config.darkTheme = dark.isChecked();
            store.saveConfig();
            showStatus("设置已保存");
            if (themeChanged) {
                buildShell();
                showPage("settings");
            }
        });
        pageBox.addView(save, spaced());
    }

    private View settingsEntryCard() {
        LinearLayout card = vertical();
        card.setPadding(dp(12), dp(12), dp(12), dp(8));
        card.setBackground(cardBg());
        TextView title = label("功能入口", 15, Typeface.BOLD);
        card.addView(title, matchWrap());

        ViewGroup actions = horizontalWrap();
        actions.addView(button("手机号管理", "secondary", v -> showPage("phones")), buttonParams());
        actions.addView(button("短信取码", "secondary", v -> showPage("standalone")), buttonParams());
        actions.addView(button("导入邮箱", "secondary", v -> showPasteDialog("批量导入邮箱", true, false)), buttonParams());
        actions.addView(button("导出邮箱", "secondary", v -> exportAccounts()), buttonParams());
        actions.addView(button("导出结果", "secondary", v -> exportResultsCsv()), buttonParams());
        card.addView(actions, spaced());
        return card;
    }

    private void handleAccountImport(String text) {
        ImportResult<ImportRecord> parsed = Parsing.parseAccounts(text);
        if (parsed.records.isEmpty()) {
            toast("没有识别到有效邮箱");
            return;
        }
        int[] accountStats = store.upsertAccounts(parsed.records);
        List<PhoneImportRecord> phoneRecords = new ArrayList<>();
        List<ImportRecord> phoneOnly = new ArrayList<>();
        for (ImportRecord record : parsed.records) {
            selectedEmails.add(record.email);
            if (!record.phone.isEmpty() && !record.phoneApiUrl.isEmpty()) {
                PhoneImportRecord phone = new PhoneImportRecord();
                phone.phone = record.phone;
                phone.apiUrl = record.phoneApiUrl;
                phone.emails.add(record.email);
                phoneRecords.add(phone);
            } else if (!record.phone.isEmpty()) {
                phoneOnly.add(record);
            }
        }
        int phoneTouched = 0;
        if (!phoneRecords.isEmpty()) {
            int[] phoneStats = store.upsertPhones(phoneRecords, false);
            phoneTouched += phoneStats[0] + phoneStats[1];
        }
        for (ImportRecord record : phoneOnly) {
            Set<String> one = new HashSet<>();
            one.add(record.email);
            phoneTouched += store.bindEmails(record.phone, one, true);
        }
        showStatus("导入完成：新增 " + accountStats[0] + "，更新 " + accountStats[1] + "，重复 " + accountStats[2]
                + (phoneTouched > 0 ? "，手机号 " + phoneTouched : "")
                + (parsed.invalid > 0 ? "，无效 " + parsed.invalid : ""));
        showPage("mailboxes");
        if (store.config.autoFetchAfterImport) {
            fetchAccounts(emailsFromImports(parsed.records));
        }
    }

    private void handlePhoneImport(String text, boolean standalone) {
        ImportResult<PhoneImportRecord> parsed = Parsing.parsePhones(text);
        if (parsed.records.isEmpty()) {
            toast("没有识别到有效手机号");
            return;
        }
        int[] stats = store.upsertPhones(parsed.records, standalone);
        showStatus("导入完成：新增 " + stats[0] + "，更新 " + stats[1] + "，重复 " + stats[2]
                + (parsed.invalid > 0 ? "，无效 " + parsed.invalid : ""));
        showPage(standalone ? "standalone" : "phones");
    }

    private void fetchSelected() {
        List<String> emails = new ArrayList<>();
        for (String email : selectedEmails) {
            AccountRecord account = store.getAccount(email);
            if (account != null) {
                emails.add(account.email);
            }
        }
        if (emails.isEmpty()) {
            toast("请先选择账号");
            return;
        }
        fetchAccounts(emails);
    }

    private void fetchAccounts(List<String> emails) {
        if (fetchRunning) {
            showStatus("正在取件，请稍后");
            return;
        }
        List<AccountRecord> accounts = new ArrayList<>();
        for (String email : emails) {
            AccountRecord account = store.getAccount(email);
            if (account != null) {
                accounts.add(account);
            }
        }
        if (accounts.isEmpty()) {
            toast("请先导入账号");
            return;
        }
        fetchRunning = true;
        stopRequested = false;
        mailRows.clear();
        renderLatestCodeBox();
        renderResultsList();
        showProgressPanel();
        progressBar.setMax(accounts.size());
        progressBar.setProgress(0);
        progressBar.setVisibility(View.VISIBLE);
        progressText.setText("准备取件…");
        showStatus("取件中 0/" + accounts.size());
        executor.execute(() -> {
            int success = 0;
            int totalMessages = 0;
            int done = 0;
            int top = store.config.conciseMode ? 1 : store.config.top;
            for (AccountRecord account : accounts) {
                if (stopRequested) {
                    break;
                }
                try {
                    List<MailRow> rows = mailService.fetchAccountRows(account, store.config.protocol, top, store.config.conciseMode);
                    store.markAccount(account.email, "成功 " + rows.size() + " 封", true);
                    synchronized (mailRows) {
                        mailRows.addAll(rows);
                    }
                    success++;
                    totalMessages += rows.size();
                } catch (Exception exc) {
                    store.markAccount(account.email, "获取失败", false);
                    final String error = account.email + "：" + exc.getMessage();
                    mainHandler.post(() -> showStatus("取件失败：" + Parsing.compact(error, 120)));
                }
                done++;
                int finalDone = done;
                int finalTotalMessages = totalMessages;
                mainHandler.post(() -> {
                    progressBar.setProgress(finalDone);
                    progressText.setText("[" + finalDone + "/" + accounts.size() + "] 已取 " + finalTotalMessages + " 条");
                    renderLatestCodeBox();
                    renderResultsList();
                    if ("fetch".equals(page)) {
                        showPage("fetch");
                    } else if ("mailboxes".equals(page)) {
                        renderAccountList();
                    }
                });
            }
            int finalSuccess = success;
            int finalTotalMessages = totalMessages;
            boolean stopped = stopRequested;
            mainHandler.post(() -> {
                fetchRunning = false;
                progressBar.setProgress(accounts.size());
                progressBar.setVisibility(View.GONE);
                hideProgressPanel();
                progressText.setText(stopped ? "已停止" : "完成");
                showStatus((stopped ? "已停止" : "完成") + " " + finalSuccess + "/" + accounts.size() + " | " + finalTotalMessages + " 条");
                renderLatestCodeBox();
                renderRecentResultsIfVisible();
                renderResultsList();
            });
        });
    }

    private void fetchAccountPhone(String email) {
        AccountRecord account = store.getAccount(email);
        if (account == null || account.phone.isEmpty()) {
            toast("该邮箱未绑定手机号");
            return;
        }
        PhoneRecord phone = store.getPhone(account.phone);
        if (phone == null) {
            toast("绑定的手机号不存在");
            return;
        }
        fetchPhone(phone, false, true);
    }

    private void fetchPhone(PhoneRecord phone, boolean standalone, boolean addToResults) {
        if (fetchRunning) {
            showStatus("正在执行任务，请稍后");
            return;
        }
        fetchRunning = true;
        showProgressPanel();
        progressBar.setMax(1);
        progressBar.setProgress(0);
        progressBar.setVisibility(View.VISIBLE);
        progressText.setText("正在取码：" + phone.phone);
        executor.execute(() -> {
            try {
                MailRow row = mailService.fetchPhoneRow(phone, false);
                String code = Parsing.cleanCode(row.code);
                String message = firstNonEmpty(row.smsContent, row.preview);
                store.markPhone(phone, code.isEmpty() ? "未识别验证码" : "成功", code, message, standalone);
                if (addToResults) {
                    synchronized (mailRows) {
                        mailRows.clear();
                        mailRows.add(row);
                    }
                }
                mainHandler.post(() -> {
                    fetchRunning = false;
                    progressBar.setProgress(1);
                    progressBar.setVisibility(View.GONE);
                    hideProgressPanel();
                    progressText.setText("取码完成");
                    showStatus("手机号验证码：" + firstNonEmpty(code, "未识别"));
                    renderLatestCodeBox();
                    renderRecentResultsIfVisible();
                    renderResultsList();
                    if (addToResults && "mailboxes".equals(page)) {
                        renderAccountList();
                    } else if (standalone) {
                        renderStandaloneList();
                    } else {
                        renderPhoneList();
                    }
                });
            } catch (Exception exc) {
                store.markPhone(phone, "获取失败", "", exc.getMessage(), standalone);
                mainHandler.post(() -> {
                    fetchRunning = false;
                    progressBar.setVisibility(View.GONE);
                    hideProgressPanel();
                    progressText.setText("取码失败");
                    showStatus("手机号取码失败：" + Parsing.compact(exc.getMessage(), 120));
                    if (standalone) {
                        renderStandaloneList();
                    } else {
                        renderPhoneList();
                    }
                });
            }
        });
    }

    private void fetchStandalone(boolean all) {
        if (fetchRunning) {
            showStatus("正在执行任务，请稍后");
            return;
        }
        List<PhoneRecord> targets = new ArrayList<>();
        if (all) {
            targets.addAll(filteredPhones(true));
        } else {
            for (String phone : selectedStandalonePhones) {
                PhoneRecord record = store.getStandalonePhone(phone);
                if (record != null) {
                    targets.add(record);
                }
            }
        }
        if (targets.isEmpty()) {
            toast("请先选择手机号");
            return;
        }
        fetchRunning = true;
        stopRequested = false;
        showProgressPanel();
        progressBar.setMax(targets.size());
        progressBar.setProgress(0);
        progressBar.setVisibility(View.VISIBLE);
        progressText.setText("准备取码…");
        executor.execute(() -> {
            int success = 0;
            int done = 0;
            for (PhoneRecord phone : targets) {
                if (stopRequested) {
                    break;
                }
                try {
                    MailRow row = mailService.fetchPhoneRow(phone, false);
                    String code = Parsing.cleanCode(row.code);
                    String message = firstNonEmpty(row.smsContent, row.preview);
                    store.markPhone(phone, code.isEmpty() ? "未识别验证码" : "成功", code, message, true);
                    if (!code.isEmpty()) {
                        success++;
                    }
                } catch (Exception exc) {
                    store.markPhone(phone, "失败：" + Parsing.compact(exc.getMessage(), 80), "", exc.getMessage(), true);
                }
                done++;
                int finalDone = done;
                mainHandler.post(() -> {
                    progressBar.setProgress(finalDone);
                    progressText.setText("[" + finalDone + "/" + targets.size() + "] 独立取码");
                    renderStandaloneList();
                });
            }
            int finalSuccess = success;
            boolean stopped = stopRequested;
            mainHandler.post(() -> {
                fetchRunning = false;
                progressBar.setVisibility(View.GONE);
                hideProgressPanel();
                progressText.setText(stopped ? "已停止" : "取码完成");
                showStatus((stopped ? "已停止" : "取码完成") + "：" + finalSuccess + "/" + targets.size());
                renderStandaloneList();
            });
        });
    }

    private void requestStop() {
        stopRequested = true;
        showProgressPanel();
        progressText.setText("正在停止…");
        showStatus("正在停止任务");
    }

    private void showProgressPanel() {
        if (progressBox != null) {
            progressBox.setVisibility(View.VISIBLE);
        }
    }

    private void hideProgressPanel() {
        if (progressBox != null) {
            progressBox.setVisibility(View.GONE);
        }
    }

    private void showPasteDialog(String title, boolean accounts, boolean standalonePhones) {
        EditText input = new EditText(this);
        input.setMinLines(8);
        input.setGravity(Gravity.TOP);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        input.setTextColor(colorText());
        input.setHint(accounts
                ? "email----password----client_id----refresh_token"
                : "+12633008723----https://api.example.com/record?token=xxx");
        int padding = dp(12);
        input.setPadding(padding, padding, padding, padding);
        input.setBackground(inputBg());
        new AlertDialog.Builder(this)
                .setTitle(title)
                .setView(input)
                .setNegativeButton("取消", null)
                .setPositiveButton("导入", (dialog, which) -> {
                    if (accounts) {
                        handleAccountImport(input.getText().toString());
                    } else {
                        handlePhoneImport(input.getText().toString(), standalonePhones);
                    }
                })
                .show();
    }

    private void showMoveDialog() {
        if (selectedEmails.isEmpty()) {
            toast("请先选择账号");
            return;
        }
        List<AccountCategory> categories = store.categorySnapshot();
        String[] labels = new String[categories.size()];
        for (int i = 0; i < categories.size(); i++) {
            labels[i] = categories.get(i).label;
        }
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("移动到分类")
                .setItems(labels, (opened, which) -> {
                    AccountCategory target = categories.get(which);
                    Set<String> selected = new HashSet<>(selectedEmails);
                    int changed = store.setCategory(selected, target.key);
                    for (String email : selected) {
                        selectedEmails.remove(email);
                    }
                    showStatus("已移动 " + changed + " 个账号到 " + target.label);
                    showPage("mailboxes");
                })
                .create();
        showThemedDialog(dialog);
    }

    private void showCategoryManager() {
        AlertDialog[] managerRef = new AlertDialog[1];
        LinearLayout panel = vertical();
        panel.setPadding(dp(18), dp(16), dp(18), dp(10));
        panel.setBackgroundColor(colorSurface());

        TextView title = label("管理邮箱分类", 20, Typeface.BOLD);
        panel.addView(title, matchWrap());
        TextView hint = label("分类会同步用于导入、导出、筛选和批量移动。", 12, Typeface.NORMAL);
        hint.setTextColor(colorMuted());
        panel.addView(hint, spaced());

        LinearLayout rows = vertical();
        for (AccountCategory category : store.categorySnapshot()) {
            LinearLayout row = horizontal();
            row.setPadding(dp(10), dp(8), dp(8), dp(8));
            row.setBackground(softCardBg());

            LinearLayout text = vertical();
            TextView name = label(category.label, 14, Typeface.BOLD);
            TextView meta = label(countCategory(category.key) + " 个邮箱" + (category.protectedCategory ? " · 系统分类" : ""), 11, Typeface.NORMAL);
            meta.setTextColor(colorMuted());
            text.addView(name, matchWrap());
            text.addView(meta, matchWrap());
            row.addView(text, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));

            if (!category.protectedCategory) {
                Button rename = button("重命名", "secondary", v -> {
                    if (managerRef[0] != null) {
                        managerRef[0].dismiss();
                    }
                    showCategoryPrompt("重命名分类", category);
                });
                row.addView(rename, new LinearLayout.LayoutParams(dp(78), dp(40)));
                Button delete = button("删除", "danger", v -> {
                    if (managerRef[0] != null) {
                        managerRef[0].dismiss();
                    }
                    confirm(
                            "删除分类",
                            "分类中的邮箱会移到“未使用”，确定删除“" + category.label + "”吗？",
                            () -> {
                                int moved = store.deleteCategory(category.key);
                                if (category.key.equals(currentCategory)) {
                                    currentCategory = Constants.CATEGORY_UNUSED;
                                }
                                showStatus("已删除分类，" + Math.max(0, moved) + " 个邮箱移到未使用");
                                showPage("mailboxes");
                            });
                });
                LinearLayout.LayoutParams deleteParams = new LinearLayout.LayoutParams(dp(66), dp(40));
                deleteParams.leftMargin = dp(6);
                row.addView(delete, deleteParams);
            }
            rows.addView(row, spaced());
        }
        ScrollView listScroll = new ScrollView(this);
        listScroll.addView(rows, matchWrap());
        LinearLayout.LayoutParams listParams = matchWrap();
        listParams.height = Math.min(dp(420), (int) (getResources().getDisplayMetrics().heightPixels * 0.52f));
        panel.addView(listScroll, listParams);

        Button add = button("新建分类", "primary", v -> {
            if (managerRef[0] != null) {
                managerRef[0].dismiss();
            }
            showCategoryPrompt("新建分类", null);
        });
        panel.addView(add, spaced());

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(panel)
                .setNegativeButton("关闭", null)
                .create();
        managerRef[0] = dialog;
        showThemedDialog(dialog);
    }

    private void showCategoryPrompt(String title, AccountCategory category) {
        EditText input = edit("输入分类名称，最多 24 个字");
        input.setText(category == null ? "" : category.label);
        input.setSelectAllOnFocus(true);
        LinearLayout box = vertical();
        box.setPadding(dp(18), dp(8), dp(18), 0);
        box.addView(input, matchWrap());
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle(title)
                .setView(box)
                .setNegativeButton("取消", null)
                .setPositiveButton("保存", (opened, which) -> {
                    String value = input.getText().toString();
                    boolean ok;
                    if (category == null) {
                        ok = store.addCategory(value) != null;
                    } else {
                        ok = store.renameCategory(category.key, value);
                    }
                    if (!ok) {
                        toast("分类名称无效或已经存在");
                    } else {
                        showStatus(category == null ? "已新建分类" : "已重命名分类");
                        showPage("mailboxes");
                    }
                })
                .create();
        showThemedDialog(dialog);
    }

    private void showFetchAccountPicker() {
        if (store.accounts.isEmpty()) {
            toast("请先导入邮箱");
            return;
        }
        if (fetchCandidateAccounts().isEmpty()) {
            toast("没有匹配的邮箱");
            return;
        }

        Set<String> draft = new HashSet<>(selectedEmails);
        String[] category = {defaultFetchPickerCategory()};
        AlertDialog[] dialogRef = new AlertDialog[1];

        LinearLayout panel = vertical();
        panel.setPadding(dp(16), dp(14), dp(16), dp(12));
        panel.setBackgroundColor(colorSurface());

        LinearLayout header = horizontal();
        LinearLayout titleBox = vertical();
        TextView title = label("选择取件邮箱", 20, Typeface.BOLD);
        TextView subtitle = label("先选分类，再从分类里勾选邮箱", 12, Typeface.NORMAL);
        subtitle.setTextColor(colorMuted());
        titleBox.addView(title, matchWrap());
        titleBox.addView(subtitle, matchWrap());
        header.addView(titleBox, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        TextView selectedBadge = badge("已选 " + draft.size(), colorBlue());
        header.addView(selectedBadge, wrapWrap());
        panel.addView(header, matchWrap());

        LinearLayout categoryRow = horizontal();
        HorizontalScrollView categoryScroll = new HorizontalScrollView(this);
        categoryScroll.setHorizontalScrollBarEnabled(false);
        categoryScroll.addView(categoryRow, new HorizontalScrollView.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        panel.addView(categoryScroll, spaced());

        TextView hint = label(accountQuery.trim().isEmpty()
                ? "当前未使用首页搜索过滤"
                : "已按首页搜索过滤：" + Parsing.compact(accountQuery.trim(), 18), 12, Typeface.NORMAL);
        hint.setTextColor(colorMuted());
        panel.addView(hint, spaced());

        LinearLayout listBox = vertical();
        ScrollView listScroll = new ScrollView(this);
        listScroll.setFillViewport(false);
        listScroll.addView(listBox, matchWrap());
        LinearLayout.LayoutParams listParams = matchWrap();
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        listParams.height = Math.max(dp(260), Math.min((int) (screenHeight * 0.52f), dp(470)));
        listParams.topMargin = dp(10);
        panel.addView(listScroll, listParams);

        LinearLayout tools = horizontal();
        Button selectCategory = button("本类全选", "secondary");
        Button clearCategory = button("清空本类", "secondary");
        Button clearAll = button("清空全部", "danger");
        tools.addView(selectCategory, equalButtonParams(3, 0));
        tools.addView(clearCategory, equalButtonParams(3, 1));
        tools.addView(clearAll, equalButtonParams(3, 2));
        panel.addView(tools, spaced());

        ViewGroup actions = horizontalWrap();
        Button cancel = button("取消", "secondary", v -> dialogRef[0].dismiss());
        Button save = button("保存选择", "primary", v -> {
            selectedEmails.clear();
            selectedEmails.addAll(draft);
            showStatus("已选择 " + selectedEmails.size() + " 个邮箱");
            showPage("fetch");
            dialogRef[0].dismiss();
        });
        actions.addView(cancel, buttonParams());
        actions.addView(save, buttonParams());
        panel.addView(actions, spaced());

        Runnable[] refreshCounts = new Runnable[1];
        Runnable[] refreshList = new Runnable[1];
        refreshList[0] = () -> {
        };
        refreshCounts[0] = () -> {
            selectedBadge.setText("已选 " + draft.size());
            renderFetchPickerCategories(categoryRow, category, draft, refreshList[0]);
        };
        refreshList[0] = () -> {
            refreshCounts[0].run();
            renderFetchPickerList(listBox, category[0], draft, refreshCounts[0]);
        };

        selectCategory.setOnClickListener(v -> {
            for (AccountRecord account : fetchCandidateAccounts(category[0])) {
                draft.add(account.email);
            }
            refreshList[0].run();
        });
        clearCategory.setOnClickListener(v -> {
            for (AccountRecord account : fetchCandidateAccounts(category[0])) {
                draft.remove(account.email);
            }
            refreshList[0].run();
        });
        clearAll.setOnClickListener(v -> {
            draft.clear();
            refreshList[0].run();
        });

        refreshList[0].run();
        AlertDialog dialog = new AlertDialog.Builder(this).setView(panel).create();
        dialogRef[0] = dialog;
        showThemedDialog(dialog);
        Window window = dialog.getWindow();
        if (window != null) {
            int width = (int) (getResources().getDisplayMetrics().widthPixels * 0.94f);
            window.setLayout(width, ViewGroup.LayoutParams.WRAP_CONTENT);
        }
    }

    private void renderFetchPickerCategories(LinearLayout categoryRow, String[] current, Set<String> draft, Runnable refreshList) {
        categoryRow.removeAllViews();
        for (AccountCategory category : store.categorySnapshot()) {
            int total = fetchCandidateAccounts(category.key).size();
            int selected = countSelectedInCategory(category.key, draft);
            String text = category.label + " " + total + (selected > 0 ? " / " + selected : "");
            Button chip = button(text, category.key.equals(current[0]) ? "segment-active" : "segment");
            chip.setOnClickListener(v -> {
                current[0] = category.key;
                refreshList.run();
            });
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(42));
            params.rightMargin = dp(8);
            categoryRow.addView(chip, params);
        }
    }

    private void renderFetchPickerList(LinearLayout listBox, String category, Set<String> draft, Runnable refreshCounts) {
        listBox.removeAllViews();
        List<AccountRecord> accounts = fetchCandidateAccounts(category);
        TextView summary = label(store.categoryLabel(category) + " · " + accounts.size()
                + " 个匹配 · 本类已选 " + countSelectedInAccounts(accounts, draft) + " 个", 12, Typeface.BOLD);
        summary.setTextColor(colorMuted());
        summary.setPadding(dp(2), 0, dp(2), dp(4));
        listBox.addView(summary, matchWrap());

        if (accounts.isEmpty()) {
            listBox.addView(emptyText(accountQuery.trim().isEmpty()
                    ? "这个分类还没有邮箱"
                    : "这个分类没有匹配搜索的邮箱"), spaced());
            return;
        }
        for (AccountRecord account : accounts) {
            listBox.addView(fetchPickerAccountRow(account, draft, refreshCounts), spaced());
        }
    }

    private View fetchPickerAccountRow(AccountRecord account, Set<String> draft, Runnable refreshCounts) {
        LinearLayout row = horizontal();
        row.setPadding(dp(10), dp(8), dp(10), dp(8));
        row.setBackground(pickerRowBg(draft.contains(account.email)));

        CheckBox check = new CheckBox(this);
        check.setButtonTintList(android.content.res.ColorStateList.valueOf(colorBlue()));
        check.setChecked(draft.contains(account.email));
        row.addView(check, new LinearLayout.LayoutParams(dp(40), ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout textBox = vertical();
        TextView email = label(Parsing.compact(account.email, 34), 14, Typeface.BOLD);
        TextView meta = label(fetchPickerMeta(account), 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        textBox.addView(email, matchWrap());
        textBox.addView(meta, matchWrap());
        row.addView(textBox, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));

        check.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (isChecked) {
                draft.add(account.email);
            } else {
                draft.remove(account.email);
            }
            row.setBackground(pickerRowBg(isChecked));
            refreshCounts.run();
        });
        row.setOnClickListener(v -> check.setChecked(!check.isChecked()));
        return row;
    }

    private void showBindDialog(PhoneRecord phone) {
        if (store.accounts.isEmpty()) {
            toast("请先导入邮箱账号");
            return;
        }
        List<AccountRecord> accounts = new ArrayList<>();
        for (AccountRecord account : store.accounts) {
            if (account.phone.isEmpty() || account.phone.equals(phone.phone)) {
                accounts.add(account);
            }
        }
        if (accounts.isEmpty()) {
            toast("没有可绑定的邮箱；其他邮箱已绑定到别的手机号");
            return;
        }
        String[] labels = new String[accounts.size()];
        boolean[] checked = new boolean[accounts.size()];
        for (int i = 0; i < accounts.size(); i++) {
            labels[i] = accounts.get(i).email;
            checked[i] = phone.emails.contains(accounts.get(i).email);
        }
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("绑定邮箱（最多3个）")
                .setMultiChoiceItems(labels, checked, (opened, which, isChecked) -> {
                    checked[which] = isChecked;
                    int count = 0;
                    for (boolean item : checked) {
                        if (item) {
                            count++;
                        }
                    }
                    if (count > DataStore.MAX_EMAILS_PER_PHONE) {
                        checked[which] = false;
                        ((AlertDialog) opened).getListView().setItemChecked(which, false);
                        toast("一个手机号最多绑定3个邮箱");
                    }
                })
                .setNegativeButton("取消", null)
                .setPositiveButton("保存", (opened, which) -> {
                    List<String> selected = new ArrayList<>();
                    for (int i = 0; i < checked.length; i++) {
                        if (checked[i]) {
                            selected.add(accounts.get(i).email);
                        }
                    }
                    store.setPhoneBindings(phone.phone, selected);
                    showStatus("已更新绑定：" + phone.phone);
                    renderPhoneList();
                })
                .create();
        showThemedDialog(dialog);
    }

    private void editTag(AccountRecord account) {
        LinearLayout box = vertical();
        box.setPadding(dp(18), dp(16), dp(18), dp(8));
        box.setBackgroundColor(colorSurface());
        TextView title = label("编辑标签", 20, Typeface.BOLD);
        box.addView(title, matchWrap());
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setText(account.tag);
        input.setSelectAllOnFocus(true);
        input.setTextColor(colorText());
        input.setHintTextColor(colorMuted());
        input.setHint("给这个邮箱加个短标签");
        input.setBackground(inputBg());
        input.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams inputParams = matchWrap();
        inputParams.topMargin = dp(14);
        box.addView(input, inputParams);
        AlertDialog tagDialog = new AlertDialog.Builder(this)
                .setView(box)
                .setNegativeButton("取消", null)
                .setPositiveButton("保存", (savedDialog, which) -> {
                    store.setTag(account.email, input.getText().toString());
                    renderAccountList();
                    showStatus("标签已更新");
                })
                .create();
        showThemedDialog(tagDialog);
    }

    private void showRowDetail(MailRow row) {
        LinearLayout box = vertical();
        int padding = dp(18);
        box.setPadding(padding, padding, padding, padding);
        box.setBackgroundColor(colorSurface());
        TextView title = label("详情", 20, Typeface.BOLD);
        box.addView(title, matchWrap());
        TextView subject = label(firstNonEmpty(row.subject, "(无主题)"), 17, Typeface.BOLD);
        subject.setTextColor(colorText());
        LinearLayout.LayoutParams subjectParams = matchWrap();
        subjectParams.topMargin = dp(14);
        box.addView(subject, subjectParams);
        TextView meta = label(row.sender + "\n" + row.time + " · " + row.protocol + " · " + row.account, 12, Typeface.NORMAL);
        meta.setTextColor(colorMuted());
        box.addView(meta, spaced());
        TextView preview = label(firstNonEmpty(row.preview, row.smsContent, "无正文预览"), 14, Typeface.NORMAL);
        preview.setTextColor(colorText());
        preview.setTextIsSelectable(true);
        box.addView(preview, spaced());
        ScrollView detailScroll = scroll(box);
        detailScroll.setBackgroundColor(colorSurface());
        AlertDialog.Builder builder = new AlertDialog.Builder(this)
                .setView(detailScroll)
                .setPositiveButton("关闭", null);
        if (!row.webLink.isEmpty()) {
            builder.setNegativeButton("打开网页", (dialog, which) -> openUrl(row.webLink));
        }
        showThemedDialog(builder.create());
    }

    private void deleteSelectedAccounts() {
        if (selectedEmails.isEmpty()) {
            toast("请先选择账号");
            return;
        }
        confirm("删除选中", "确定删除选中的 " + selectedEmails.size() + " 个账号吗？", () -> {
            int removed = store.removeAccounts(new HashSet<>(selectedEmails));
            selectedEmails.clear();
            showStatus("已删除 " + removed + " 个账号");
            showPage("mailboxes");
        });
    }

    private void clearAccounts() {
        if (store.accounts.isEmpty()) {
            return;
        }
        confirm("清空全部", "确定清空全部邮箱账号吗？", () -> {
            int total = store.clearAccounts();
            selectedEmails.clear();
            showStatus("已清空 " + total + " 个账号");
            showPage("mailboxes");
        });
    }

    private void exportAccounts() {
        if (store.accounts.isEmpty()) {
            toast("没有可导出的账号");
            return;
        }
        pendingExportText = store.exportAccountsText();
        createTextFile(REQ_EXPORT_ACCOUNTS, "wremail_accounts.txt", "text/plain");
    }

    private void exportPhones() {
        if (store.phones.isEmpty()) {
            toast("没有可导出的手机号");
            return;
        }
        pendingExportText = store.exportPhonesText();
        createTextFile(REQ_EXPORT_PHONES, "wremail_phones.txt", "text/plain");
    }

    private void exportResultsCsv() {
        List<MailRow> rows = filteredRows();
        if (rows.isEmpty()) {
            toast("没有可导出的结果");
            return;
        }
        StringBuilder csv = new StringBuilder("\uFEFFaccount,phone,protocol,time,sender,subject,code,read,preview,webLink,concise\n");
        for (MailRow row : rows) {
            String code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
            csv.append(Parsing.csv(row.account)).append(',')
                    .append(Parsing.csv(row.phone)).append(',')
                    .append(Parsing.csv(row.protocol)).append(',')
                    .append(Parsing.csv(row.time)).append(',')
                    .append(Parsing.csv(row.sender)).append(',')
                    .append(Parsing.csv(row.subject)).append(',')
                    .append(Parsing.csv(code)).append(',')
                    .append(Parsing.csv(row.read)).append(',')
                    .append(Parsing.csv(row.preview)).append(',')
                    .append(Parsing.csv(row.webLink)).append(',')
                    .append(row.concise)
                    .append('\n');
        }
        pendingExportText = csv.toString();
        createTextFile(REQ_EXPORT_RESULTS, "wremail_results.csv", "text/csv");
    }

    private List<AccountRecord> filteredAccounts() {
        String needle = accountQuery.trim().toLowerCase(Locale.ROOT);
        List<AccountRecord> result = new ArrayList<>();
        for (AccountRecord account : store.accounts) {
            if (!account.category.equals(currentCategory)) {
                continue;
            }
            String haystack = (account.email + " " + account.tag + " " + account.lastStatus + " " + account.phone).toLowerCase(Locale.ROOT);
            if (needle.isEmpty() || haystack.contains(needle)) {
                result.add(account);
            }
        }
        return result;
    }

    private List<AccountRecord> fetchCandidateAccounts() {
        return fetchCandidateAccounts(null);
    }

    private List<AccountRecord> fetchCandidateAccounts(String category) {
        String needle = accountQuery.trim().toLowerCase(Locale.ROOT);
        String normalizedCategory = category == null ? "" : store.resolveCategory(category);
        if (normalizedCategory == null) {
            normalizedCategory = "";
        }
        List<AccountRecord> result = new ArrayList<>();
        for (AccountRecord account : store.accounts) {
            if (!normalizedCategory.isEmpty() && !account.category.equals(normalizedCategory)) {
                continue;
            }
            String haystack = (account.email + " " + account.tag + " " + account.lastStatus + " "
                    + account.phone + " " + store.categoryLabel(account.category)).toLowerCase(Locale.ROOT);
            if (needle.isEmpty() || haystack.contains(needle)) {
                result.add(account);
            }
        }
        return result;
    }

    private String defaultFetchPickerCategory() {
        String normalized = store.resolveCategory(currentCategory);
        if (normalized == null) {
            normalized = Constants.CATEGORY_UNUSED;
        }
        if (!fetchCandidateAccounts(normalized).isEmpty()) {
            return normalized;
        }
        for (AccountCategory category : store.categorySnapshot()) {
            if (!fetchCandidateAccounts(category.key).isEmpty()) {
                return category.key;
            }
        }
        return normalized;
    }

    private int countSelectedInCategory(String category, Set<String> draft) {
        return countSelectedInAccounts(fetchCandidateAccounts(category), draft);
    }

    private int countSelectedInAccounts(List<AccountRecord> accounts, Set<String> draft) {
        int count = 0;
        for (AccountRecord account : accounts) {
            if (draft.contains(account.email)) {
                count++;
            }
        }
        return count;
    }

    private String fetchPickerMeta(AccountRecord account) {
        List<String> parts = new ArrayList<>();
        parts.add(store.categoryLabel(account.category));
        parts.add(account.source());
        if (!account.phone.isEmpty()) {
            parts.add(account.phone);
        }
        if (!account.tag.isEmpty()) {
            parts.add("标签：" + account.tag);
        }
        if (!account.lastStatus.isEmpty()) {
            parts.add(account.lastStatus);
        }
        return Parsing.compact(String.join(" · ", parts), 72);
    }

    private List<MailRow> filteredRows() {
        String keyword = resultKeyword.trim().toLowerCase(Locale.ROOT);
        String sender = resultSender.trim().toLowerCase(Locale.ROOT);
        List<MailRow> result = new ArrayList<>();
        synchronized (mailRows) {
            for (MailRow row : mailRows) {
                if (!"全部".equals(resultProtocolFilter) && !resultProtocolFilter.equals(row.protocol)) {
                    continue;
                }
                String haystack = (row.subject + " " + row.preview + " " + row.account + " " + row.phone + " " + row.code).toLowerCase(Locale.ROOT);
                String senderText = row.sender.toLowerCase(Locale.ROOT);
                if (!keyword.isEmpty() && !haystack.contains(keyword)) {
                    continue;
                }
                if (!sender.isEmpty() && !senderText.contains(sender)) {
                    continue;
                }
                result.add(row);
            }
        }
        return result;
    }

    private void copyAllCodes() {
        List<String> codes = new ArrayList<>();
        for (MailRow row : filteredRows()) {
            String code = Parsing.cleanCode(firstNonEmpty(row.code, Parsing.extractCode(row.subject, row.preview)));
            if (!code.isEmpty()) {
                codes.add(code);
            }
        }
        if (codes.isEmpty()) {
            toast("没有可复制的验证码");
            return;
        }
        copy(String.join("\n", codes), "已复制全部验证码");
    }

    private List<MailRow> recentRows(int limit) {
        List<MailRow> rows = filteredRows();
        List<MailRow> recent = new ArrayList<>();
        for (int i = 0; i < rows.size() && recent.size() < limit; i++) {
            recent.add(rows.get(i));
        }
        return recent;
    }

    private int countRows(String protocol) {
        int count = 0;
        synchronized (mailRows) {
            for (MailRow row : mailRows) {
                if (protocol.equals(row.protocol)) {
                    count++;
                }
            }
        }
        return count;
    }

    private void renderRecentResultsIfVisible() {
        if ("fetch".equals(page)) {
            showPage("fetch");
        } else {
            renderResultsList();
        }
    }

    private void chooseTopCount() {
        String[] values = {"1", "5", "10", "20", "30", "50"};
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("每次取件数量")
                .setItems(values, (opened, which) -> {
                    store.config.top = Integer.parseInt(values[which]);
                    store.saveConfig();
                    showStatus("每次取件：" + store.config.top + " 封");
                    showPage("fetch");
                })
                .create();
        showThemedDialog(dialog);
    }

    private void chooseProtocol() {
        String[] values = {"Graph 优先", "IMAP 优先"};
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("协议优先级")
                .setItems(values, (opened, which) -> {
                    store.config.protocol = which == 1 ? "IMAP" : "Graph";
                    store.saveConfig();
                    showStatus("协议：" + values[which]);
                    showPage("fetch");
                })
                .create();
        showThemedDialog(dialog);
    }

    private List<PhoneRecord> filteredPhones(boolean standalone) {
        String needle = (standalone ? standaloneQuery : phoneQuery).trim().toLowerCase(Locale.ROOT);
        List<PhoneRecord> source = standalone ? store.standalonePhones : store.phones;
        List<PhoneRecord> result = new ArrayList<>();
        for (PhoneRecord phone : source) {
            String haystack = (phone.phone + " " + phone.apiUrl + " " + phone.lastStatus + " " + phone.lastCode + " "
                    + phone.lastMessage + " " + String.join(" ", phone.emails)).toLowerCase(Locale.ROOT);
            if (needle.isEmpty() || haystack.contains(needle)) {
                result.add(phone);
            }
        }
        return result;
    }

    private int countCategory(String category) {
        int count = 0;
        for (AccountRecord account : store.accounts) {
            if (account.category.equals(category)) {
                count++;
            }
        }
        return count;
    }

    private List<String> emailsOf(List<AccountRecord> accounts) {
        List<String> emails = new ArrayList<>();
        for (AccountRecord account : accounts) {
            emails.add(account.email);
        }
        return emails;
    }

    private List<String> emailsFromImports(List<ImportRecord> records) {
        List<String> emails = new ArrayList<>();
        for (ImportRecord record : records) {
            emails.add(record.email);
        }
        return emails;
    }

    private List<String> singleton(String value) {
        List<String> list = new ArrayList<>();
        list.add(value);
        return list;
    }

    private void openTextFile(int requestCode) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, requestCode);
    }

    private void createTextFile(int requestCode, String name, String mime) {
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_TITLE, name);
        startActivityForResult(intent, requestCode);
    }

    private String readText(Uri uri) throws Exception {
        StringBuilder builder = new StringBuilder();
        try (InputStream input = getContentResolver().openInputStream(uri);
             BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line).append('\n');
            }
        }
        return builder.toString();
    }

    private void writeText(Uri uri, String text) throws Exception {
        try (OutputStream output = getContentResolver().openOutputStream(uri)) {
            output.write((text == null ? "" : text).getBytes(StandardCharsets.UTF_8));
        }
    }

    private void copy(String value, String message) {
        if (value == null || value.isEmpty()) {
            return;
        }
        ClipboardManager manager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        manager.setPrimaryClip(ClipData.newPlainText(Constants.DISPLAY_NAME, value));
        showStatus(message + "：" + Parsing.compact(value, 80));
        toast(message);
    }

    private void openUrl(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception exc) {
            toast("无法打开链接");
        }
    }

    private void confirm(String title, String message, Runnable action) {
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle(title)
                .setMessage(message)
                .setNegativeButton("取消", null)
                .setPositiveButton("确定", (opened, which) -> action.run())
                .create();
        showThemedDialog(dialog);
    }

    private void showThemedDialog(AlertDialog dialog) {
        dialog.setOnShowListener(opened -> {
            if (dialog.getWindow() != null) {
                dialog.getWindow().setBackgroundDrawable(cardBg());
            }
            Button positive = dialog.getButton(AlertDialog.BUTTON_POSITIVE);
            if (positive != null) {
                positive.setTextColor(colorBlue());
            }
            Button negative = dialog.getButton(AlertDialog.BUTTON_NEGATIVE);
            if (negative != null) {
                negative.setTextColor(colorBlue());
            }
        });
        dialog.show();
    }

    private void showStatus(String text) {
        if (statusView != null) {
            statusView.setText(text);
        }
    }

    private void toast(String text) {
        Toast.makeText(this, text, Toast.LENGTH_SHORT).show();
    }

    private String firstNonEmpty(String... values) {
        for (String value : values) {
            if (value != null && !value.isEmpty()) {
                return value;
            }
        }
        return "";
    }

    private String timestampName(String prefix, String suffix) {
        return prefix + "_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date()) + suffix;
    }

    private LinearLayout vertical() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        return layout;
    }

    private LinearLayout horizontal() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.HORIZONTAL);
        layout.setGravity(Gravity.CENTER_VERTICAL);
        return layout;
    }

    private ViewGroup horizontalWrap() {
        return new FlowLayout(this);
    }

    private TextView label(String text, int sp, int style) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(sp);
        view.setTypeface(Typeface.create(style == Typeface.BOLD ? "sans-serif-medium" : "sans-serif", style));
        view.setTextColor(colorText());
        view.setLineSpacing(0, 1.08f);
        return view;
    }

    private TextView emptyText(String text) {
        TextView view = label(text, 14, Typeface.NORMAL);
        view.setTextColor(colorMuted());
        view.setGravity(Gravity.CENTER);
        view.setPadding(dp(12), dp(22), dp(12), dp(22));
        view.setBackground(cardBg());
        return view;
    }

    private TextView badge(String text, int color) {
        TextView view = label(text, 11, Typeface.BOLD);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER);
        view.setPadding(dp(8), dp(3), dp(8), dp(3));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(withAlpha(color, 28));
        bg.setCornerRadius(dp(8));
        view.setBackground(bg);
        return view;
    }

    private EditText edit(String hint) {
        EditText edit = new EditText(this);
        edit.setSingleLine(true);
        edit.setHint(hint);
        edit.setTextColor(colorText());
        edit.setHintTextColor(colorMuted());
        edit.setTextSize(14);
        edit.setPadding(dp(12), 0, dp(12), 0);
        edit.setMinHeight(dp(46));
        edit.setBackground(inputBg());
        return edit;
    }

    private CheckBox checkbox(String text, boolean checked) {
        CheckBox box = new CheckBox(this);
        box.setText(text);
        box.setTextColor(colorText());
        box.setTextSize(14);
        box.setChecked(checked);
        box.setButtonTintList(android.content.res.ColorStateList.valueOf(colorBlue()));
        return box;
    }

    private Button button(String text, String role) {
        Button button = new Button(this);
        styleButton(button, text, role);
        return button;
    }

    private Button button(String text, String role, View.OnClickListener listener) {
        Button button = button(text, role);
        button.setOnClickListener(listener);
        return button;
    }

    private void styleButton(Button button, String text, String role) {
        button.setText(text);
        button.setAllCaps(false);
        button.setTextSize(13);
        button.setSingleLine(true);
        button.setMaxLines(1);
        button.setGravity(Gravity.CENTER);
        button.setIncludeFontPadding(false);
        button.setMinHeight(0);
        button.setMinimumHeight(0);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setHeight("primary-large".equals(role) ? dp(54) : dp(44));
        button.setPadding(dp(6), 0, dp(6), 0);
        button.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        int fill;
        int stroke = colorBorder();
        int textColor;
        int pressedFill;
        int pressedStroke = 0;
        if ("primary".equals(role) || "primary-large".equals(role)) {
            fill = colorBlue();
            stroke = colorBlue();
            pressedFill = pressColor(fill);
            textColor = Color.WHITE;
        } else if ("hero".equals(role)) {
            fill = Color.WHITE;
            stroke = Color.WHITE;
            pressedFill = Color.rgb(229, 241, 255);
            pressedStroke = pressedFill;
            textColor = colorBlue();
        } else if ("hero-soft".equals(role)) {
            fill = Color.argb(36, 255, 255, 255);
            stroke = Color.argb(80, 255, 255, 255);
            pressedFill = Color.argb(70, 255, 255, 255);
            pressedStroke = Color.argb(120, 255, 255, 255);
            textColor = Color.WHITE;
        } else if ("nav-active".equals(role)) {
            fill = withAlpha(colorBlue(), store.config.darkTheme ? 50 : 24);
            stroke = Color.TRANSPARENT;
            pressedFill = withAlpha(colorBlue(), store.config.darkTheme ? 70 : 38);
            pressedStroke = Color.TRANSPARENT;
            textColor = colorBlue();
        } else if ("nav".equals(role)) {
            fill = Color.TRANSPARENT;
            stroke = Color.TRANSPARENT;
            pressedFill = withAlpha(colorBlue(), store.config.darkTheme ? 38 : 22);
            pressedStroke = Color.TRANSPARENT;
            textColor = colorMuted();
        } else if ("segment-active".equals(role)) {
            fill = colorBlue();
            stroke = colorBlue();
            pressedFill = pressColor(fill);
            pressedStroke = colorBlue();
            textColor = Color.WHITE;
        } else if ("segment".equals(role)) {
            fill = store.config.darkTheme ? Color.rgb(30, 41, 59) : Color.rgb(241, 245, 249);
            stroke = Color.TRANSPARENT;
            pressedFill = withAlpha(colorBlue(), store.config.darkTheme ? 44 : 24);
            pressedStroke = Color.TRANSPARENT;
            textColor = colorMuted();
        } else if ("tagged".equals(role)) {
            fill = withAlpha(colorGreen(), store.config.darkTheme ? 40 : 30);
            stroke = colorGreen();
            pressedFill = withAlpha(colorGreen(), store.config.darkTheme ? 70 : 48);
            pressedStroke = colorGreen();
            textColor = colorGreen();
        } else if ("danger".equals(role)) {
            fill = store.config.darkTheme ? Color.rgb(68, 34, 42) : Color.rgb(255, 241, 242);
            stroke = store.config.darkTheme ? Color.rgb(105, 48, 58) : Color.rgb(254, 205, 211);
            pressedFill = store.config.darkTheme ? Color.rgb(92, 45, 50) : Color.rgb(255, 226, 226);
            textColor = colorRed();
        } else if ("disabled".equals(role)) {
            fill = store.config.darkTheme ? Color.rgb(42, 50, 64) : Color.rgb(232, 238, 246);
            pressedFill = fill;
            textColor = colorMuted();
        } else {
            fill = store.config.darkTheme ? Color.rgb(28, 45, 68) : Color.rgb(239, 246, 255);
            stroke = store.config.darkTheme ? Color.rgb(48, 73, 105) : Color.rgb(219, 234, 254);
            pressedFill = store.config.darkTheme ? Color.rgb(36, 56, 82) : Color.rgb(219, 234, 254);
            textColor = colorBlue();
        }
        pressedStroke = pressedStroke == 0 ? stroke : pressedStroke;
        button.setBackground(buttonBg(fill, stroke, pressedFill, pressedStroke));
        button.setTextColor(textColor);
    }

    private ScrollView scroll(View child) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        scroll.addView(child, matchWrap());
        return scroll;
    }

    private GradientDrawable cardBg() {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(colorSurface());
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), colorBorder());
        return bg;
    }

    private GradientDrawable softCardBg() {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(store.config.darkTheme ? Color.rgb(22, 33, 49) : Color.rgb(248, 250, 252));
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), colorBorder());
        return bg;
    }

    private GradientDrawable pickerRowBg(boolean selected) {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(selected ? withAlpha(colorBlue(), store.config.darkTheme ? 46 : 24) : colorSurface());
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), selected ? colorBlue() : colorBorder());
        return bg;
    }

    private StateListDrawable buttonBg(int fill, int stroke, int pressedFill, int pressedStroke) {
        StateListDrawable states = new StateListDrawable();
        states.addState(new int[]{-android.R.attr.state_enabled}, buttonShape(fill, stroke));
        states.addState(new int[]{android.R.attr.state_pressed}, buttonShape(pressedFill, pressedStroke));
        states.addState(new int[]{android.R.attr.state_focused}, buttonShape(pressedFill, pressedStroke));
        states.addState(new int[]{}, buttonShape(fill, stroke));
        return states;
    }

    private GradientDrawable buttonShape(int fill, int stroke) {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(fill);
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), stroke);
        return bg;
    }

    private GradientDrawable heroCardBg() {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(colorBlue());
        bg.setCornerRadius(dp(8));
        return bg;
    }

    private GradientDrawable bottomNavBg() {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(colorSurface());
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), colorBorder());
        return bg;
    }

    private GradientDrawable inputBg() {
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(colorSurface());
        bg.setCornerRadius(dp(8));
        bg.setStroke(dp(1), colorBorder());
        return bg;
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private LinearLayout.LayoutParams matchMatch() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
    }

    private LinearLayout.LayoutParams wrapWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private LinearLayout.LayoutParams spaced() {
        LinearLayout.LayoutParams params = matchWrap();
        params.topMargin = dp(8);
        return params;
    }

    private LinearLayout.LayoutParams buttonParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(actionButtonWidth(), ViewGroup.LayoutParams.WRAP_CONTENT);
        params.rightMargin = dp(8);
        params.bottomMargin = dp(8);
        return params;
    }

    private LinearLayout.LayoutParams equalButtonParams(int total, int index) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        if (index < total - 1) {
            params.rightMargin = dp(8);
        }
        return params;
    }

    private int actionButtonWidth() {
        float density = getResources().getDisplayMetrics().density;
        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels / density);
        if (widthDp < 360) {
            return dp(88);
        }
        if (widthDp < 420) {
            return dp(96);
        }
        if (widthDp < 600) {
            return dp(104);
        }
        return dp(118);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private int colorBg() {
        return store.config.darkTheme ? Color.rgb(15, 23, 42) : Color.rgb(244, 246, 248);
    }

    private int colorSurface() {
        return store.config.darkTheme ? Color.rgb(24, 34, 52) : Color.WHITE;
    }

    private int colorText() {
        return store.config.darkTheme ? Color.rgb(241, 245, 249) : Color.rgb(23, 32, 51);
    }

    private int colorMuted() {
        return store.config.darkTheme ? Color.rgb(148, 163, 184) : Color.rgb(102, 112, 133);
    }

    private int colorBorder() {
        return store.config.darkTheme ? Color.rgb(51, 65, 85) : Color.rgb(225, 230, 237);
    }

    private int colorBlue() {
        return store.config.darkTheme ? Color.rgb(96, 165, 250) : Color.rgb(37, 99, 235);
    }

    private int colorGreen() {
        return store.config.darkTheme ? Color.rgb(57, 215, 154) : Color.rgb(15, 159, 117);
    }

    private int colorRed() {
        return store.config.darkTheme ? Color.rgb(255, 122, 122) : Color.rgb(226, 83, 83);
    }

    private int pressColor(int color) {
        float factor = store.config.darkTheme ? 1.12f : 0.88f;
        return Color.rgb(
                Math.min(255, Math.round(Color.red(color) * factor)),
                Math.min(255, Math.round(Color.green(color) * factor)),
                Math.min(255, Math.round(Color.blue(color) * factor))
        );
    }

    private int withAlpha(int color, int alpha) {
        return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color));
    }

    private abstract static class SimpleWatcher implements TextWatcher {
        @Override
        public void beforeTextChanged(CharSequence s, int start, int count, int after) {
        }

        @Override
        public void onTextChanged(CharSequence s, int start, int before, int count) {
        }
    }
}
