# 验证记录

日期：2026-10-31。

- 现有电脑实机：Windows MSIX Claude Desktop 4.4212.0；基础汉化、协作/编程标签、建议隐藏、原生文件/编辑/视图/跳转子菜单均通过界面检查。
- 新项目 `Setup.ps1 -PrepareOnly`：使用未汉化的同版本原始 exe / app.asar / ion-dist.asar 副本，在 Windows PowerShell 5.1 下完整执行成功。生成的 manifest 状态为 prepared；两个 ASAR 结构和 exe 内嵌头哈希同步通过。
- 自动测试：ASAR 新增目录保留原始数据和 unpacked 引用、拒绝损坏 ASAR、标签只改显示/保留图标 ID、未知前端拒绝写入、CC Switch 保留后台路由和 1M 支持。
- 项目中的独立 Apply/Restore 事务脚本已通过 PowerShell 语法检查；未在第二台电脑执行安装/恢复。现有电脑原先使用同类备份/哈希/临时 ACL 方法安装，但这不等于本项目自动恢复流程已在第二台设备验证。

不包含：Cowork VM 功能测试、API 计费请求、macOS/Linux、其他 Claude 版本、其他第三方服务商。
