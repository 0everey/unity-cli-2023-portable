# 安装指南

## 1. 准备环境

- Windows 10/11 x64、Windows PowerShell 5.1 或 PowerShell 7。
- Unity Hub 和项目对应的 **Unity 2023.1 / 2023.2** Editor，完成正常授权。已实际验证版本为 2023.2.14f1c1；Unity 2023.1 与其他 2023.2 补丁版本尚未实机复验，需在自己的工程验证。
- Python **3.10+**：从 https://www.python.org/downloads/windows/ 安装，勾选 **Add python.exe to PATH**，然后重新打开 PowerShell。也支持 Python 的 `py -3` 启动器。
- 本地 Unity 工程：根目录必须包含 `Assets`、`Packages/manifest.json`、`ProjectSettings/ProjectVersion.txt`。

不需要管理员权限、不需要安装 Codex/Node.js、不需要配置模型账号。

## 2. 解压与检查

若使用 git clone，请先运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\Download-CLI.ps1` 补齐固定 CLI。Release ZIP 用户无需此步骤。



把整个 ZIP 解压到固定目录，例如 `D:\Tools`。不要在 ZIP 内直接运行脚本。中文及空格路径可用，命令中的路径需保留引号。

```powershell
Set-Location 'D:\Tools\UnityCLI2023-Portable-0.18.1-r1-20261015'
powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify.ps1
```

正常结果包含 `"verified": true`。这是文件一致性检查，不是数字签名。`-ExecutionPolicy Bypass` 仅用于这一次 PowerShell 进程，不改全局策略。若公司设备策略禁止脚本，请交管理员处理。下载文件被 Windows 标记时，可先在 ZIP 属性勾选“解除锁定”，再重新解压。

## 3. 安装到自己的工程

先正常关闭**目标工程**的 Unity Editor。下面的 `D:\Projects\MyGame` 必须换成你的工程根目录，不是 `Assets` 子目录。

```powershell
# 只预览，不修改工程。
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Project 'D:\Projects\MyGame' -DryRun

# 执行安装。
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Project 'D:\Projects\MyGame'
```

安装将 Bridge 嵌入 `Packages/com.akiojin.unity-cli-bridge`，在 `Packages/manifest.json` 增加这一项，备份和回执写入工程 `.unity-cli-portable`。场景、Prefab、游戏源码、存档和输入设置保留。Unity 的依赖解析会更新 `packages-lock.json` 和 Library。

依赖最低版本为 Input System 1.7.0、Newtonsoft JSON 3.2.1、Test Framework 1.3.9、UGUI 2.0.0。缺失依赖由 Unity Package Manager 联网获取。本包不包含这些 Unity 包的离线缓存。已有更高的数字版本会保留并提示；已有低版本或 Git/本地来源会拒绝安装，需先按自己工程兼容性协调依赖。

若提示已有 Bridge，本入口不会覆盖已有接入。若提示 UnityLockfile，先确认目标 Editor 是否确已关闭，处理自己的残留锁后再装；不要删除其他活跃工程的锁。

## 4. 打开 Unity 并确认连接

在 Unity Hub 用项目对应的 2023.2 Editor 打开工程，等待导入和编译完成。Console 先解决编译错误，再执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 -Project 'D:\Projects\MyGame' status
powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 -Project 'D:\Projects\MyGame' wait --seconds 120
powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 -Project 'D:\Projects\MyGame' capabilities
```

`capabilities` 的 `projectPath` 必须是自己的工程，`unityVersion` 为 2023.2，Bridge 版本为 0.18.1。多开工程时，每次传入完整 `-Project` 路径。

可选：用 CLI 启动 Editor 时，先告诉它真实安装位置；默认推荐直接通过 Unity Hub 打开：

```powershell
$env:UNITY_EDITOR_PATH = 'D:\Unity\2023.2.14f1c1\Editor\Unity.exe'
powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 -Project 'D:\Projects\MyGame' open
```

日常操作使用交互式 Editor。仅批处理宿主需要 `UNITY_CLI_ALLOW_BATCH_HOST=1`；单独 `-batchmode` 默认不会提供 Bridge。

## 5. 开启虚拟输入（按需）

层级、资源、脚本、构建等功能不需要改输入设置。使用虚拟键鼠工具时，在 Unity 的 **Edit → Project Settings → Player → Other Settings → Active Input Handling** 选择 **Input System Package (New)** 或 **Both**，按提示重启 Editor。安装器不会替你切换旧游戏的输入模式。

## 6. 卸载

正常关闭目标 Unity Editor，然后执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Uninstall.ps1 -Project 'D:\Projects\MyGame'
```

卸载只去掉当前 Bridge 依赖，把包移到工程 `.unity-cli-portable/retired-*`，不覆盖后来新增的其他依赖，不删除原包源码。当前 packages-lock 保留，下次打开 Unity 后自动解析。若工程由其他写入者持有租约，请用工程原协调流程。

## 常见问题

| 现象 | 处理 |
|---|---|
| 找不到 Python | 安装 Python 3.10+，勾选 PATH，关闭并重新打开终端 |
| 已安装但连不上 | 确认目标 Unity 已打开且编译完成；运行 `doctor`；核对 `-Project` 路径 |
| Unity 编译错误 | 先看 Console，核对依赖版本、包网络访问和 2023.2 Editor |
| 提示最低依赖版本不符 | 在自己的备份/分支中处理版本兼容后再安装；安装器不降级或覆盖你的依赖 |
| Windows 防火墙询问 | Bridge 默认仅监听本机回环地址；本地调用无需开放公网端口 |
| 写操作超时或域重载 | 先查原请求/实际对象状态，超时不等于没执行；不要立即换 ID 重复提交写操作 |
| 需要离线使用 | 首次准备好 Unity、Python 和 Unity 依赖缓存后，CLI 本身可本地运行；本 ZIP 不是 Unity 完整离线安装器 |
