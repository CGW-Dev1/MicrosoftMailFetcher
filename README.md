# 邮件验证码助手
当前版本：V1.9

本项目包含 Windows 桌面版和 Android App 两个版本，用于批量导入 Outlook/Hotmail 邮箱账号，并通过 Microsoft Graph 或 IMAP OAuth 获取最新邮件、提取验证码。

Android 版定位为“邮箱账号池 + 验证码取件工作台”，适合在手机上完成导入邮箱、选择账号、取验证码、复制验证码、查看结果和导出数据等流程。

## 下载

Windows 桌面版 exe：

```text
https://github.com/CGW-Dev1/MicrosoftMailFetcher/raw/main/dist/邮件验证码助手.exe
```

Android App APK：

```text
https://github.com/CGW-Dev1/MicrosoftMailFetcher/raw/main/android/app/build/outputs/apk/debug/app-debug.apk
```

手机安装 APK 时，如系统提示“未知来源应用”，需要允许当前浏览器或文件管理器安装应用。

## Android App 介绍

Android 版已经按手机竖屏工作流重构，不是简单照搬桌面布局。

- 底部导航：取件 / 邮箱 / 结果 / 设置。
- 取件页：搜索邮箱、选择邮箱、全部取件、选中取件、停止任务、查看最近结果。
- 邮箱页：按未使用 / Plus / Free / 已封禁分类管理邮箱，支持搜索、复制、改标签、移动分类、删除和导出。
- 结果页：按全部 / Graph / IMAP / SMS 筛选结果，支持搜索邮件内容、搜索发件人、复制验证码、查看邮件详情和打开网页。
- 设置页：管理协议、每账号读取封数、简洁模式、深色模式、手机号取码和数据导入导出。
- 本地安全：Android 版使用 Android Keystore 加密保存账号、refresh_token 和手机号 API。
- 系统适配：支持 Android 15，界面会避开状态栏和底部导航区域，并按不同安卓手机宽度自适应。

## 版本规则

- 当前版本从 `V1.0` 开始。
- 小版本依次递增：`V1.0 -> V1.1 -> ... -> V1.9`。
- 到 `V1.9` 后下一版自动变为 `V2.0`。
- 版本号保存在 `VERSION` 文件中，同时显示在软件标题和主界面标题里。

升级版本号：

```powershell
.\bump_version.ps1
```

## 运行

```powershell
python -m pip install -r requirements.txt
python app.py
```

## 打包 exe

```powershell
.\build.ps1
```

打包完成后 exe 位于：

```text
dist\邮件验证码助手.exe
```

## 构建 Android APK

Android 工程位于 `android/` 目录。

```powershell
cd android
& 'C:\Users\cuigw\.gradle\wrapper\dists\gradle-8.14.3-all\10utluxaxniiv4wxiphsi49nj\gradle-8.14.3\bin\gradle.bat' assembleDebug
```

构建完成后 APK 位于：

```text
android\app\build\outputs\apk\debug\app-debug.apk
```

## 导入格式

每行一个账号，格式如下：

```text
email@outlook.com----password----client_id----refresh_token
```

普通四段格式导入后会进入“未使用”菜单。软件导出的账号会在末尾增加分类，重新导入时会自动回到对应菜单：

```text
email@outlook.com----password----client_id----refresh_token----已封禁
```

导出文件会按菜单增加 `# ===== 分类 =====` 分割线，重新导入时这些分割线会自动跳过。

账号内容会保存在本机当前 Windows 用户目录下，并使用 Windows DPAPI 加密保存。

## 主要功能

- 批量导入账号，重复邮箱自动过滤。
- 导入普通账号默认进入“未使用”菜单，导入带分类的导出文件会自动进入“未使用 / Plus / Free / 已封禁”对应菜单。
- 支持批量标记到 Plus / Free / 已封禁，也可以移回未使用。
- Graph 令牌 / IMAP 令牌切换，默认使用 Graph。
- 支持简洁模式，只提取最新验证码。
- 支持按邮箱、邮件内容、发件人搜索。
- 支持导出账号和导出取件结果 CSV。
- 支持复制邮箱。
- 支持本地单文件 exe 打包。
- 支持 Android APK 直接安装使用。

## 安全说明

- 导入的邮箱、密码、client_id、refresh_token 会保存在本机。
- 保存文件使用当前 Windows 用户的 DPAPI 加密。
- Android 版使用 Android Keystore 加密保存。
- 导出账号时会导出明文内容，并在末尾带分类，方便备份和迁移。
