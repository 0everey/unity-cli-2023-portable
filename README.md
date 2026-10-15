# Unity 2023 CLI 便携分享包

Windows x64 / Unity 2023.1、2023.2 / 社区 unity-cli 0.18.1 / 2023 适配 r1。

[下载 ZIP](https://github.com/0everey/unity-cli-2023-portable/releases/latest) · [中文安装指南](INSTALL.zh-CN.md) · [常用命令](USAGE.zh-CN.md) · [验证范围](VERIFIED.md)

把命令行操作接入自己的 Unity 2023 工程。包含固定 CLI、Editor Bridge 源码、Roslyn 依赖、中文指南、安装/卸载脚本及 JSON 示例。

```powershell
# 替换解压目录和工程路径，先正常关闭目标工程的 Unity。
Set-Location 'D:\Tools\UnityCLI2023-Portable-0.18.1-r1-20261015'
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Project 'D:\Projects\MyGame2023'
# 用项目对应的 Unity 2023 Editor 打开工程，等待导入和编译完成。
powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 -Project 'D:\Projects\MyGame2023' status
powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 -Project 'D:\Projects\MyGame2023' capabilities
```

需要 Python 3.10+、已授权的 Unity 2023 Editor；首轮 Unity 包依赖解析需要网络。无需 Codex、Node.js、模型账号或额外 Python 包。

面向 Unity 2023.1/2023.2，实际验证对象是 **2023.2.14f1c1 + Input System 1.7.0**。Unity 2023.1 尚未实机复验；不能把 2022 版的验证结果直接当作 2023 版结果。具体结果见 DELIVERY-CHECKS.json 和 VERIFIED.md。

基于 MIT 许可的 [akiojin/unity-cli v0.18.1](https://github.com/akiojin/unity-cli/releases/tag/v0.18.1)。许可及修改说明见 [NOTICE.md](NOTICE.md)。本包保留上游协议版本，2023 专用扩展名为 unity2023_capabilities、unity2023_undo 和 unity2023_serialized_properties。

安装将 Bridge 嵌入目标工程，不引用分享者的工程路径。项目的场景、Prefab、游戏源码、存档和输入模式保留。安装记录及 manifest 备份在工程 .unity-cli-portable；卸载保留后来新增的其他依赖。

## 从 GitHub 获取

推荐从 Releases 下载完整 ZIP。若克隆源码仓库，先运行下载脚本补齐固定 CLI；ZIP 已包含可执行文件，无需重复下载。

```powershell
git clone https://github.com/0everey/unity-cli-2023-portable.git
Set-Location .\unity-cli-2023-portable
powershell -NoProfile -ExecutionPolicy Bypass -File .\Download-CLI.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Project 'D:\Projects\MyGame2023'
```

CLI 可执行文件通过 Release ZIP 分发，下载脚本同时校验 ZIP 与可执行文件的 SHA256。Roslyn 依赖和 Editor Bridge 源码随仓库提供；Unity Editor、Python 和 Unity 包依赖请按安装指南准备。
