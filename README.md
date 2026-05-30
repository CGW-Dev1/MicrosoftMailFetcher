# 邮件验证码助手
当前版本：V1.4

本项目是一个本地 Windows 桌面工具，用于批量导入 Outlook/Hotmail 邮箱账号，并通过 Microsoft Graph 或 IMAP OAuth 获取最新邮件、提取验证码。

## 下载

最新版 exe：

```text
https://github.com/CGW-Dev1/MicrosoftMailFetcher/raw/main/dist/邮件验证码助手.exe
```

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

## 安全说明

- 导入的邮箱、密码、client_id、refresh_token 会保存在本机。
- 保存文件使用当前 Windows 用户的 DPAPI 加密。
- 导出账号时会导出明文内容，并在末尾带分类，方便备份和迁移。
