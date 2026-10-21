# Harness 接入与恢复

版本：v1
本文件由 `harness init` 生成。托管块由 `sync` 更新，不要手工编辑标记覆盖的内容。

## 四层结构

| 层 | 位置 | 作用 |
| --- | --- | --- |
| 全局触发 | 用户目录，如 `~/.dsh/AGENTS.md`、`~/.codex/AGENTS.md`、`~/.claude/CLAUDE.md` | 发现仓库缺少托管块时提醒初始化 |
| 引擎 | `~/.agents/harness/`（`harness.py` + `templates/`） | 执行 `init / adopt / sync / check` |
| 项目 | `AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md` | 托管块、适配器、项目事实 |
| 技能 | ai-skills 的 `bootstrap-harness` | 让 agent 知道何时调用引擎 |

## 本仓库文件

- `AGENTS.md`：canonical，含 `harness:managed` 托管块和 `## Project`。
- `CLAUDE.md`：`@AGENTS.md` 适配器。
- `.github/copilot-instructions.md`：相同托管块的副本。
- `docs/status.md`：当前分支、验证、阻塞、下一步。
- `docs/tasks/active.md`：当前唯一任务。
- `.github/pull_request_template.md`：任务、验收、范围检查。

## 命令

```powershell
python ~/.agents/harness/harness.py status
python ~/.agents/harness/harness.py init --write
python ~/.agents/harness/harness.py adopt --write
python ~/.agents/harness/harness.py sync --write
python ~/.agents/harness/harness.py check
```

`init` 只用于新仓库或空 `AGENTS.md`；已有内容用 `adopt`。所有写操作先看 diff，不自动提交。

## 没有 AI 工具时

1. 打开 `AGENTS.md`，保留 `## Working Agreement` 到 `<!-- /harness:managed -->` 的内容；不要手改托管块。
2. 托管块丢失时，从下方“基线快照”复制正文；标记和哈希可以在下次运行 `sync --write` 时补上。
3. 确认 `CLAUDE.md` 含 `@AGENTS.md`。
4. 确认 `.github/copilot-instructions.md` 顶部有同一段托管块。
5. 在 `docs/status.md` 写当前分支、验证、阻塞、下一步。
6. 在 `docs/tasks/active.md` 只保留一个 `in_progress` 任务，并写验收命令。

## 基线快照（v1）

{{AGENTS_MANAGED}}

## 注意事项

- 不要手工编辑托管块；改基线后运行 `sync`。
- README 是项目事实，托管块只链接，不复制命令。
- 已有 `AGENTS.md` 只 `adopt`，不自动合并。
- 自动初始化只在新/空仓库、干净工作区执行，且不自动提交。
- 哈希不一致时 `check` 失败；版本落后只警告。
