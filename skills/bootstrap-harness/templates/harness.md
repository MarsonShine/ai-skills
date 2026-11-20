# Harness 接入与恢复

当前基线版本见 `AGENTS.md` 中的 `harness:managed` 标记。
本文件由 `harness init` 生成。托管块由 `sync` 更新，不要手工编辑标记覆盖的内容。

## 四层结构

| 层 | 位置 | 作用 |
| --- | --- | --- |
| 全局触发 | 用户目录，如 `~/.dsh/AGENTS.md`、`~/.codex/AGENTS.md`、`~/.claude/CLAUDE.md` | 发现仓库缺少托管块时提醒初始化 |
| 引擎 | `~/.agents/harness/`（CLI、配套 Python 模块和 `templates/`） | 初始化、同步、检查和查询工作树任务 |
| 项目 | `AGENTS.md`、`CLAUDE.md`、`.github/copilot-instructions.md` | 托管块、适配器、项目事实 |
| 技能 | ai-skills 的 `bootstrap-harness` | 让 agent 知道何时调用引擎 |

## 本仓库文件

- `AGENTS.md`：canonical，含 `harness:managed` 托管块和 `## Project`。
- `CLAUDE.md`：`@AGENTS.md` 适配器。
- `.github/copilot-instructions.md`：相同托管块的副本。
- `docs/status.md`：当前分支、验证、阻塞、下一步。
- `docs/tasks/active.md`：由集成者维护的当前项目任务。
- 独立 Git 工作树根目录的 `HANDOFF.md`：该工作树的任务卡。
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

`check` 还会检查任务卡、状态页、本恢复指南和 PR 模板是否存在且非空。`sync --write` 只为缺失或空白的辅助文件补建模板，保留已有非空文件的原始内容。补建不能恢复丢失的任务结果，历史内容应从 Git 或备份恢复。

更新源模板不会迁移已有项目文档；新增字段需要在项目中增量修改。`check` 不验证验收标准、证据链接或业务正确性。

## 同一项目并行处理两个任务

为每个并行任务分配独立 Git 工作树和任务 ID。各会话可用 `git rev-parse --show-toplevel` 确认目录不同。会话接续同一项工作时，继续打开原工作树根目录的 `HANDOFF.md`。任务卡填写 `Task`、`Status` 和 `Next`。工作中用 `in_progress`，阻塞时用 `blocked` 并填写 `Blocker`，完成时用 `completed` 并填写 `Evidence: [验收结果](相对文件路径)`，链接须指向实际证据。

```powershell
python "$HOME/.agents/harness/harness.py" tasks --root .
python "$HOME/.agents/harness/harness.py" closeout --root . --worktree-task --scope HANDOFF.md
```

在任务工作树运行第二条命令，并为本任务的改动目录或文件追加 `--scope`。完成时加 `--complete`。`tasks` 只读汇总本地 Git 已登记工作树的任务卡，并报告重复的活跃 ID。它提供当前快照，任务认领仍需会话之间协调。集成者负责 `docs/status.md`；工作树中的卡片保留为未跟踪文件，合并或移除工作树前先将仍需复查的内容存入任务专属证据目录。

## 没有 AI 工具时

1. 打开 `AGENTS.md`，保留 `## Working Agreement` 到 `<!-- /harness:managed -->` 的内容；不要手改托管块。
2. 托管块丢失时，从下方“基线快照”复制正文；标记和哈希可以在下次运行 `sync --write` 时补上。
3. 确认 `CLAUDE.md` 含 `@AGENTS.md`。
4. 确认 `.github/copilot-instructions.md` 顶部有同一段托管块。
5. 在 `docs/status.md` 写当前分支、验证、阻塞、下一步。
6. 单任务使用 `docs/tasks/active.md` 并写验收命令。并行任务各自更新所在工作树的 `HANDOFF.md`，用 `git worktree list` 查找其他任务。

## 基线快照

{{AGENTS_MANAGED}}

## 注意事项

- 不要手工编辑托管块；改基线后运行 `sync`。
- README 是项目事实，托管块只链接，不复制命令。
- 已有 `AGENTS.md` 只 `adopt`，不自动合并。
- 自动初始化只在新/空仓库、干净工作区执行，且不自动提交。
- 哈希不一致时 `check` 失败；版本落后只警告。
