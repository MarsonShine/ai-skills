# 微信接入与恢复

## 本机配置

在将运行助手的机器设置 `WECHAT_APPID`、`WECHAT_APPSECRET`，可选 `WECHAT_ACCOUNT_NAME` 方便辨认。也可把 `{"appid":"…","secret":"…","name":"…"}` 存到用户主目录的 `.config/wechat-mp/config.json`，限制为当前用户可读。环境变量成组优先。请通过本机配置密钥，聊天中只需确认账号名称与 AppID。预览完全离线，无需密钥。选择 Python 可设置 `WECHAT_MP_PYTHON`。

`check` 尝试获取稳定 token，分别报告凭据和本次出口 IP 的结果。40164 表示出口 IP 不符合白名单，48001 表示该接口未授权。首次成功新增并回读草稿后才能确认该账号的写入能力。检查具体文章时传 `--bundle 版本目录`。查看已创建草稿用 `status --bundle 版本目录 --account AppID`。[稳定版凭据](https://developers.weixin.qq.com/doc/subscription/api/base/api_getstableaccesstoken.html) · [全局错误码](https://developers.weixin.qq.com/doc/oplatform/developers/errCode/)

正文使用 uploadimg，JPG/PNG 小于 1MB。封面使用永久素材的 image 类型，按该类型的 10M 限额处理。普通图文发送 news，标题最多 32 字、摘要 120 字，正文少于 2 万字符且小于 1M。更新现有单篇图文传 index=0。[正文图片](https://developers.weixin.qq.com/doc/subscription/api/material/permanent/api_uploadimage.html) · [永久素材](https://developers.weixin.qq.com/doc/subscription/api/material/permanent/api_addmaterial.html) · [新增草稿](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html) · [更新草稿](https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_update.html)

## 写入结果待核对时

- 新建请求无确定结果，先查最近 20 篇草稿并比对标题、摘要、正文、封面及图序。需要认领时，向用户展示候选及可用的临时查看链接，用户选定后用同一版本、账号运行 `status --claim media_id`。没有匹配时请用户核对后台，保留未决状态。
- 已有 media_id、回读失败，只重试 `status` 或原命令的读取。远端确认缺失时提示用户核对是否已发表或删除；需要另建时按一篇新文章走预览和确认。
- 后台有人编辑时展示实际差异。用户明确确认用本版覆盖该远端版本后，才将返回的冲突码作为 `update --overwrite 冲突码` 重新提交。若对方继续编辑，会再次提示。微信未提供原子条件更新，集中在同一编辑时段操作。
- 文章工作目录保留不可变版本；账号和草稿的对应关系在用户主目录的 `.wechat-mp/state`。备份或迁移时同时保留两处。设置 `WECHAT_MP_STATE_DIR` 可以迁移整份状态目录；日常重试沿用同一份记录。

## 首次真机验收

用一张封面、两张可分辨的正文图和两段短文生成预览，请作者确认目标账号与测试稿。新增并回读后在公众号后台看到同一篇，在微信里检查正文、图序、图注、封面裁切及打开大图的效果。改一处可识别文字，再生成预览并确认更新，核对 media_id 和后台草稿总数。分别查看四种场景的手机效果，记录设备、时间和结果。草稿交给作者处理。
