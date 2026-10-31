# Claude Desktop 完整中文配置（Windows）

把汉化、原生菜单修复和首页精简整理成可备份、可恢复、可供 Codex 执行的项目。

**已在 Windows Claude Desktop 4.4212.0 实机验证最终界面。** 自动化脚本固定支持这一版本；不承诺未来版本或所有第三方插件都能完整汉化。macOS / Linux 请使用上游项目，本仓库的附加脚本不支持它们。

[安装与复现](docs/REPRODUCE.md) · [兼容范围](docs/COMPATIBILITY.md) · [验证记录](docs/VALIDATION.md) · [项目导航](docs/PROJECTS.md) · [反馈问题](https://github.com/HeiAQua/claude-desktop-zh-complete/issues/new/choose)

## 以后只给 Codex 这个仓库网址

把仓库首页网址发给 Codex，并说：

> 请阅读这个仓库的 README.md 和 AGENTS.md，按 docs/REPRODUCE.md 在当前电脑配置 Claude 桌面版中文。先检测安装和版本，备份并准备补丁，再安装验证。使用默认的“协作/编程”中文标签并隐藏首页建议。若已有 CC Switch 官方 DeepSeek 配置，再更新 V4.1 Flash 并精简模型菜单。不要复制旧电脑密钥；登录、API 密钥和 UAC 由我本人处理。不兼容的版本先检查并适配，禁止强行套用。

网址用来读取项目步骤和源码；**无法让新电脑凭空拥有登录状态、API 密钥或管理员权限**。缺少的账号信息仍需在新电脑输入。脚本不安装 Claude 或 CC Switch，不创建账号，不复制凭据。

## 包含哪些改动

- 基础前端汉化：菜单、设置、提示、斜杠菜单说明。
- “Cowork / Code”导航标签改成“协作 / 编程”。只修改显示文字，不修改模型 ID、图标 ID、工具 ID。
- 给 `app.asar/resources/i18n` 增加 `zh-CN.json`，解决界面选择 `zh-CN` 而原生菜单回落英文的问题。
- 默认隐藏“给你的建议”及三张首页建议卡片；`-KeepSuggestions` 可保留。
- 可选 CC Switch：将现有 Flash 路由更新为 `deepseek-flash`，显示名为 `DeepSeek V4.1 Flash`；菜单仅保留 Pro、Flash 和各自的 1M 选项，同时保留后台各角色路由。

## 安装

1. 从 [Claude 官网](https://claude.com/download)安装 Windows 桌面版。需要第三方 API 时，从 [CC Switch 官方仓库](https://github.com/farion1231/cc-switch)安装并在应用界面中配置自己的服务商。无需第三方模型时跳过 CC Switch。
2. 安装 Python 3.10+，确保 `python --version` 可用。Windows 自带的 PowerShell 5.1 即可；PowerShell 7 也支持。
3. 克隆或下载本仓库，完整解压。保存 Claude 中正在做的工作，退出 Claude。
4. 在仓库目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Setup.ps1
```

找不到唯一安装目录时，明确指定：

```powershell
.\Setup.ps1 -AppPath 'C:\Program Files\WindowsApps\Claude_版本_x64__包标识\app'
```

脚本先在 `%LOCALAPPDATA%\ClaudeZhComplete\jobs\时间戳` 备份原始文件、生成补丁并校验；准备成功后才弹出 Windows UAC。选择“是”后写入当前安装。**会修改 `Claude.exe`、`app.asar`、`ion-dist.asar` 和桌面中文资源，导致原始数字签名失效；Cowork VM 可能因签名检查拒绝运行。** 如果必须保留签名或依赖 Cowork VM，请不要安装本方案。

只准备、不写入已安装应用：

```powershell
.\Setup.ps1 -PrepareOnly -WorkPath 'D:\ClaudeZhJobs\一次全新的目录'
```

新电脑首次启动后，打开左下角账户 → Language / 语言 → 选择 `zh-CN`。如果暂时未切换，完全退出托盘 Claude 后再打开。原生菜单中文已随本项目补齐。应用升级会覆盖补丁，不要用旧版本备份覆盖新版本。

## 恢复

以管理员身份打开 PowerShell，用安装时打印的工作目录：

```powershell
.\scripts\Apply.ps1 -WorkPath '完整的jobs工作目录' -Restore
```

恢复前会检查应用版本及原始/补丁哈希。只还原本次备份的文件，并删除本次新建且哈希匹配的中文资源；不会清除聊天、账号或模型配置。恢复后如需英文，请在语言菜单选择 English。跨版本恢复会被拒绝。

## 可选：CC Switch 模型菜单

在 CC Switch 中选择 **Claude Desktop → DeepSeek → 模型映射**，使用官方地址 `https://api.deepseek.com/anthropic`，密钥只在本机输入。将 Sonnet / Opus / Fable 设为 `deepseek-v4-pro`，Haiku 设为 `deepseek-flash`，Haiku 菜单名设为 `DeepSeek V4.1 Flash`。确认上游支持时才勾选 1M。

若已完成上述服务商配置，关闭 Claude 和 CC Switch（包括托盘）后可以运行：

```powershell
python .\scripts\model_menu.py --update-flash --simplify-menu
```

重新启动 CC Switch、Claude。菜单应为 Flash、Flash 1M、Pro、Pro 1M。**精简只改变本地展示列表，CC Switch 再次保存/切换服务商时会重建列表，需要重新执行 `--simplify-menu`。** 不移除后台 Sonnet/Opus/Fable 路由，避免子任务请求丢失。

仅适用于已有的官方 DeepSeek Claude Desktop 配置；其他服务商、端口、安装布局需要人工适配。模型版本和计费以 [DeepSeek 官方文档](https://api-docs.deepseek.com/en/)为准。模型菜单成功不等于已进行计费 API 调用测试。

## 检查与测试

```powershell
python -m unittest discover -s tests -v
```

安装后按 [验收清单](docs/REPRODUCE.md)实机查看。遇到未识别版本或定位锚点变化时，脚本停止在准备阶段；不要删掉检查或批量替换所有英文单词。

## 来源与项目定位

基础汉化源自 MIT 项目 [javaht/claude-desktop-zh-cn](https://github.com/javaht/claude-desktop-zh-cn)，固定提交 `4f0e457a0d161a97c39c9a64d4ded7fa68e2e7f2`。本项目保留其语言资源和底层补丁函数；移除上游自动执行入口，以独立流程调用，不运行上游服务启动、自动更新或旧补丁清理功能。

本项目新增：原生 `zh-CN` 菜单资源、完整导航中文标签、隐藏建议卡片、分阶段生成/校验/写入/恢复、CC Switch 可选说明与工具、Codex 复现流程。

GitHub 搜索记录和相近项目比较见 [docs/RELATED.md](docs/RELATED.md)。本仓库不声称全球不存在其他类似项目，仅说明本次检索未找到功能组合完全一致的现成方案。

仓库只包含脚本、翻译资源和文档，不含 Claude 安装包、修改后的程序、聊天数据、账号或 API 密钥。备份文件仅留在各自电脑，不要上传。
