# 微信草稿接入

只做“写入草稿”，不自动发表。作者在微信后台预览实际裁切后再手动发表。

## 凭据

按顺序读取：

1. `--appid` / `--secret`（不推荐放进命令历史）。
2. 环境变量 `WECHAT_APPID`、`WECHAT_APPSECRET`。
3. `~/.config/workbuddy-wechat/config.json`：`{"appid": "...", "secret": "..."}`。

`--account` 必须与凭据的 AppID 一致；不一致直接拒绝。公众号后台需要把运行机器的出口 IP 加入白名单。

Token 用 `stable_token` 获取，只在当前进程内使用，不落盘。

## 流程

1. `preview`：处理图片、渲染首页和正文、生成 `bundle.json`，并计算内容版本号。
2. `confirm`：`confirmation = sha256(account|action|version)[:12]`。展示账号、操作、标题、版本、图片结论，等作者明确同意。
3. `draft`：校验确认码 → 逐张上传正文图 → 下载回读 → 用 CDN URL 重渲染正文 → 上传封面 → `draft/add` 或 `draft/update` → `draft/get` 回读。
4. 报告 `media_id`、逐图 `lossless`、封面 `media_id`、草稿回读结果和后台入口。

一次同意只覆盖这一版。正文、图片、账号或操作变化后，版本号变化，必须重新确认。

## 接口

| 用途 | 路径 | 关键返回 |
| --- | --- | --- |
| Token | `cgi-bin/stable_token` | `access_token` |
| 正文图 | `cgi-bin/media/uploadimg` | `url`（CDN） |
| 封面素材 | `cgi-bin/material/add_material?type=image` | `media_id`、`url` |
| 新建草稿 | `cgi-bin/draft/add` | `media_id` |
| 更新草稿 | `cgi-bin/draft/update` | `errcode` |
| 读取草稿 | `cgi-bin/draft/get` | `news_item[]` |

正文 HTML 必须小于 1 MiB；正文里的图片必须换成 `uploadimg` 返回的 CDN URL 后再写入草稿。

## 回读与失败

- 每张正文图上传后立即下载，比较 `expected_px`/`remote_px`、字节数和像素；结果写入 `quality[]`。
- 封面有 `url` 时同样回读；没有 `url` 时只报告 `media_id`，不声称无损。
- `draft/get` 回读标题、正文长度和 `thumb_media_id`；不一致写入 `draft_readback`。
- 网络中断、超时或响应无法解析可能发生在写入成功之后，标记为 `ambiguous`，退出码 8。不要盲目重试新建，先用 `draft/get` 或后台草稿箱核对，避免重复草稿。
- 微信错误码原样放进 `error`，常见：`40164` 出口 IP 未白名单、`40001` token 无效、`45009` 频率限制、`40007` 素材无效。

## 安全

- 不把 AppSecret、access_token、文章目录的绝对路径写进正文、图注或公开预览。
- 不把 `~/.config/workbuddy-wechat/config.json` 提交到仓库。
- 删除文章目录前确认 `bundle.json`、`images/` 都只是本地副本。
