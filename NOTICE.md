# 来源、许可与适配

- 上游：[akiojin/unity-cli](https://github.com/akiojin/unity-cli)，v0.18.1，MIT，许可见 LICENSE 和 LICENSE-unity-cli.txt。
- Bridge 上游 revision：7f45d7aec2a866abda88ba3768bf4057c5f23053。
- 原版 Windows x64 CLI SHA256：efcd697b940f78b6457829453888d9c608f19d2fcd331d0005b1ff47a7839357。
- 2023 版基于已冻结的 2022 便携 r1，更新 Unity 版本检查、包最低版本、启动入口、请求日志目录及三个兼容工具的名称/注册测试。正在开发的其他扩展未纳入。
- 保留已修正的组件全限定名、材质参数与失败原子性、Transform Undo、虚拟键盘、序列化只读检查、正式工具发现和 Editor 程序集边界。
- Roslyn 和 Microsoft 程序集许可位于 package/com.akiojin.unity-cli-bridge/Editor/ThirdParty/Roslyn。

本包不包含 Unity Editor、Unity 授权、Python、Unity 包完整离线缓存、游戏工程、个人素材、账号、API Key 或会话日志。它是社区工具的独立适配，不是 Unity 官方 CLI 产品。

Unity 2023 实机编译发现并修正：Physics2D.velocityThreshold 的新 API 分支提前到 UNITY_2023_1_OR_NEWER，读取 bounceThreshold 并保留既有 JSON 字段；依赖基线对应 Test Framework 1.3.9 与 UGUI 2.0.0。
