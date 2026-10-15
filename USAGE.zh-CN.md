# 常用命令

以下在解压目录运行。`$project` 换成自己的工程。若脚本策略阻止直接调用，把命令写成 `powershell -NoProfile -ExecutionPolicy Bypass -File .\Unity.ps1 ...`。

```powershell
$project = 'D:\Projects\MyGame'
& .\Unity.ps1 -Project $project status
& .\Unity.ps1 -Project $project doctor
& .\Unity.ps1 -Project $project capabilities
& .\Unity.ps1 -Project $project tools
& .\Unity.ps1 -Project $project schema get_hierarchy
& .\Unity.ps1 -Project $project call get_hierarchy --params-file .\examples\hierarchy.json
& .\Unity.ps1 -Project $project call read_console --params-file .\examples\console-errors.json
& .\Unity.ps1 -Project $project call get_compilation_state
```

每个工具先用 `schema <工具名>` 查看实际参数。参数放 UTF-8 JSON 文件，用 `--params-file` 传入，避免 PowerShell 对内联 JSON 引号的处理差异。

| 能力 | 工具示例 |
|---|---|
| 场景与层级 | create_scene、load_scene、save_scene、get_hierarchy |
| 对象组件 | create_gameobject、modify_gameobject、add_component、modify_component、get_component_values |
| 资源、材质、Prefab | manage_asset_database、create_material、modify_material、create_prefab、instantiate_prefab |
| 脚本与序列化 | write_csharp_file、unity2023_serialized_properties |
| Undo | unity2023_undo |
| Play 与输入/UI | play_game、pause_game、stop_game、input_keyboard、find_ui_elements、click_ui_element |
| 截图与指标 | capture_screenshot、profiler_get_metrics |
| 测试与构建 | run_tests、get_test_status、build_player、get_build_status |

## 执行 Editor C#

```powershell
& .\Unity.ps1 -Project $project eval --file .\examples\read-scene.cs.txt --request-id read-scene-001
& .\Unity.ps1 -Project $project eval-status read-scene-001
```

相同工程与 request-id 仅首次提交，重复调用只查询。请求日志在 `%LOCALAPPDATA%\UnityCLI2023\Requests`。超时/断线/域重载不代表取消；先查原 ID 及实际对象，不改新 ID 重复执行可能已发生的写入。

## 直接使用社区 CLI

```powershell
& .\unity-cli.exe --version
& .\unity-cli.exe --project-path $project --output json tool list
& .\unity-cli.exe --project-path $project --output json tool schema get_hierarchy
```

直接调用提供上游完整命令面；`Unity.ps1` 提供固定目标选择、JSON 文件参数和 eval 去重日志。Bridge 能读取、修改 Editor 内容并运行 C#，应在你自己认可的工程与脚本范围内使用。

可选包如 Addressables、Timeline、Recorder、VFX Graph 需要对应 Unity 包。虚拟输入不模拟操作系统键盘；UGUI 事件调用不证明坐标命中或无遮挡；Camera 截图可能不包含 Screen Space Overlay UI。具体命令以当前 schema 和实际响应为准。
