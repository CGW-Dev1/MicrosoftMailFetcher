# 邮件验证码助手 Android 版

这是桌面版 exe 的原生 Android 迁移工程，入口在 `app/src/main/java/com/cgwdev/wremail/MainActivity.java`。

## 已实现

- 批量导入邮箱账号：`email----password----client_id----refresh_token`
- 自动恢复分类：未使用 / Plus / Free / 已封禁
- 账号搜索、全选、移动分类、删除、清空、复制邮箱、编辑标签
- Graph / IMAP OAuth2 双协议取件
- 简洁模式、每账号读取封数、导入后自动取件
- 结果搜索、详情、复制验证码、打开网页链接、导出 CSV
- 手机号导入、邮箱绑定、解绑、删除、导出
- 绑定手机号取码和独立手机号批量取码
- Android Keystore 本地加密保存账号、refresh_token、手机号 API
- 文件导入和导出使用 Android 系统文件选择器

## 构建

本机 SDK 路径写在 `local.properties`，已配置为：

```properties
sdk.dir=D:/bcenv/android-sdk
```

构建 debug APK：

```powershell
& 'C:\Users\cuigw\.gradle\wrapper\dists\gradle-8.14.3-all\10utluxaxniiv4wxiphsi49nj\gradle-8.14.3\bin\gradle.bat' assembleDebug
```

APK 输出：

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

## 注意

Windows 版用 DPAPI 加密，Android 版用 Android Keystore 加密，所以桌面端本地 `.sec` 数据不能直接复制到手机。请用桌面版导出明文账号文本，再在 Android 版导入。
