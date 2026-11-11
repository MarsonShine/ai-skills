# 微信公众平台接口

只用 6 个接口，全部围绕「写进草稿箱」。**不调 `freepublish/submit`**——发表必须由人点。

Base: `https://api.weixin.qq.com`

---

## 1. 取 token：`stable_token`

```
POST /cgi-bin/stable_token
{"grant_type":"client_credential","appid":"...","secret":"...","force_refresh":false}
→ {"access_token":"...","expires_in":7200}
```

**为什么不用 `/cgi-bin/token`**：普通 token 每次获取都会让旧的失效。多进程/多工具同时用会互相踢，
表现为随机 `40001 invalid credential`。`stable_token` 在有效期内重复调用返回同一个 token，不会踢。

**缓存**：`~/.cache/wagent/token.json`（0600），存 `appid / token / expires_at`。
`40164` 时微信会拒绝发 token，此时无法缓存。

**重试**：收到 `40001` / `42001` 时 `force_refresh:true` 重取一次；再失败就是 secret 错，不要循环重试。

---

## 2. 正文图：`media/uploadimg`

```
POST /cgi-bin/media/uploadimg?access_token=...
multipart/form-data: media=@file
→ {"url":"http://mmbiz.qpic.cn/..."}
```

| 项 | 值 |
|---|---|
| 上限 | **1 MB**（硬上限，超了直接报错） |
| 格式 | jpg / png |
| 返回 | 一个 CDN URL，直接放进 `<img src>` |
| 有效期 | 长期有效，不会过期 |

**这是正文图片的唯一正路。** 塞本地路径或外链图床到 content 里，编辑器会静默过滤掉，草稿里就是空白。

---

## 3. 封面图：`material/add_material`

```
POST /cgi-bin/material/add_material?access_token=...&type=image
multipart/form-data: media=@file
→ {"media_id":"...","url":"http://mmbiz.qpic.cn/..."}
```

| 项 | 值 |
|---|---|
| 上限 | **10 MB** |
| 返回 | `media_id`（草稿必需）+ `url` |
| 建议 | 2.35:1，900×383 起，封面会被裁 |

**封面 `media_id` 是 `draft/add` 的必填项**，缺了会报错。同一个 media_id 可以复用。

---

## 4. 新建草稿：`draft/add`

```
POST /cgi-bin/draft/add?access_token=...
{"articles":[{
  "title":"...",
  "author":"...",
  "digest":"...",
  "content":"<section style=...>...</section>",
  "content_source_url":"",
  "thumb_media_id":"...",
  "need_open_comment":0,
  "only_fans_can_comment":0
}]}
→ {"media_id":"..."}
```

| 字段 | 必填 | 限制 |
|---|---|---|
| `title` | 是 | ≤64 字符；超过 32 字在列表页会被截断 |
| `author` | 否 | ≤16 字符 |
| `digest` | 否 | ≤120 字符；不填会从正文自动截取 |
| `content` | 是 | 内联样式 HTML 片段，**不要 `<html>` 外壳**；≤20000 字符 |
| `thumb_media_id` | **是** | 来自 `add_material` |
| `content_source_url` | 否 | 原文链接，需已认证 |
| `need_open_comment` | 否 | 0 关闭 / 1 开启 |

**content 必须是「片段」**：`<section>` 开头，不要 `<!doctype>`、`<head>`、`<style>`、`<script>`。

---

## 5. 读草稿：`draft/get`

```
POST /cgi-bin/draft/get?access_token=...
{"media_id":"..."}
→ {"news_item":[{"title":"...","content":"...","thumb_media_id":"..."}]}
```

**用途只有一个：回读校验。** 提交完立刻读回来，断言：
- `title` 非空
- 所有图片 URL 都在 `content` 里
- `content` 长度与本地渲染结果接近（差太多说明被过滤了）

这一步不做，就等于闭眼交付。

---

## 6. 更新与删除：`draft/update` / `draft/delete`

```
POST /cgi-bin/draft/update?access_token=...
{"media_id":"...","index":0,"articles":{...同 add 的单篇字段...}}
→ {"errcode":0}

POST /cgi-bin/draft/delete?access_token=...
{"media_id":"..."}
→ {"errcode":0}
```

**改稿一律走 `update`，不要 `delete` + `add`**：新加的 `media_id` 变了，用户已经贴出去的链接会失效。

---

## 错误码

| errcode | 含义 | 处理 |
|---|---|---|
| `40001` | 凭据失效 / token 被踢 | 强刷一次 token；仍失败查 secret |
| `40007` | media_id 非法 | 缩略图或草稿不存在，重新上传封面 |
| `40008` | 参数类型错误 | 多为标题超长或字段类型不对 |
| `40013` | AppID 非法 | 检查 `WX_APPID` |
| `40125` | AppSecret 无效 | 后台重置，注意别带空格 |
| `40164` | **IP 不在白名单** | 错误信息里有出口 IP，加进白名单 |
| `45009` | 接口调用超限 | 当日额度用完，明天再试 |
| `48001` | 接口未授权 | 账号类型不支持 |
| `53404` | 草稿数量超限 | 先删旧草稿 |

`40164` 的原始 errmsg 形如：

```
invalid ip 1.2.3.4 ipv6 ::ffff:1.2.3.4, not in whitelist
```

`wx.py` 会用正则把这个 IP 抠出来放进 `exit_ip`，因为这条错误看起来像「鉴权失败」，实测能卡人半小时。

---

## IP 白名单

路径：**公众号后台 → 设置与开发 → 基本配置 → IP 白名单**。

- 只认 IPv4，填 `1.2.3.4` 这种，不要带端口或 CIDR。
- 云函数/容器/CI 的出口 IP 会漂移，漂了就全挂。所以 `check` 必须先跑，失败时把 `exit_ip` 直接给用户。
- 本机开发时，出口 IP 是家里宽带或公司网关的公网 IP，不是 `127.0.0.1`。

---

## 账号类型

| 类型 | 草稿箱 | freepublish |
|---|---|---|
| 未认证订阅号 | ✅ 可用 | ❌ |
| 认证订阅号 | ✅ | ✅ |
| 认证服务号 | ✅ | ✅ |

**本 skill 只用草稿箱，所以未认证订阅号也能全流程走通。** 这是刻意的设计：门槛最低，风险最小。

---

## 不要做的事

- **不要自动发表**。`freepublish/submit` 一旦提交就进入审核+群发，撤回成本极高。
- **不要用 `/cgi-bin/token`**。多进程互踢。
- **不要把 secret 写进日志、产物、错误信息**。`wx.py` 的 `masked` 只输出 `已配置/缺失`。
- **不要手拼封面 URL**。必须走 `add_material` 换 `media_id`。
- **不要假设配额**。具体每日调用上限以后台公告为准，`45009` 出现就是到顶了。
