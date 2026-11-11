import { randomUUID } from 'node:crypto'
import { existsSync, readFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { resolve } from 'node:path'
import { parseArgs } from 'node:util'
import { applyEdits, layoutFor, profileFor, python, readJson } from './editor.ts'
import { loadBundle, preview } from './preview.ts'
import { confirmation, syncDraft } from './sync.ts'
import { WechatClient, WxError } from './wechat.ts'

const configDir = resolve(homedir(), '.config/wechat-mp')
const stateDir = resolve(process.env.WECHAT_MP_STATE_DIR || resolve(homedir(), '.wechat-mp/state'))
const backend = 'https://mp.weixin.qq.com/'
const help = {
  preview: 'preview --text 内容 | --text-file 文件 --images 照片1 照片2 [--workdir 文章目录] [--scene daily|family|travel|anniversary] [--cover 照片] [--layout 文件] [--profile 文件] [--edits 文件] [--footer-image 图片 --footer-text 文字]',
  check: 'check [--offline] [--account AppID] [--bundle 版本目录 --action draft|update]',
  draft: 'draft --bundle 版本目录 --account AppID --confirmed 确认码',
  update: 'update --bundle 版本目录 --account AppID --confirmed 确认码 [--overwrite 冲突码]',
  status: 'status --bundle 版本目录 --account AppID [--claim 草稿ID]',
}
type Command = keyof typeof help

function credentials() {
  const { WECHAT_APPID: appid, WECHAT_APPSECRET: secret, WECHAT_ACCOUNT_NAME: name } = process.env
  if (appid || secret) return { appid, secret, name }
  const file = resolve(configDir, 'config.json')
  if (!existsSync(file)) return {}
  let data
  try { data = readJson(file) } catch { throw new Error('公众号本机配置无法读取，请检查 config.json 的 JSON 格式') }
  if (!data || typeof data.appid !== 'string' || typeof data.secret !== 'string' ||
      (data.name !== undefined && typeof data.name !== 'string')) throw new Error('公众号配置需要 appid、secret 和可选 name')
  return { appid: data.appid as string, secret: data.secret as string, name: data.name as string | undefined }
}

function expandImages(args: string[]) {
  const expanded: string[] = []
  for (let i = 0; i < args.length; i++) {
    if (args[i] !== '--images') { expanded.push(args[i]); continue }
    if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error('--images 需要照片路径')
    while (args[i + 1] && !args[i + 1].startsWith('--')) expanded.push('--image', args[++i])
  }
  return expanded
}

function checkAction(value = 'draft'): 'draft' | 'update' {
  if (value !== 'draft' && value !== 'update') throw new Error('--action 可选 draft 或 update')
  return value
}

async function run(command: Command, args: string[]): Promise<Record<string, unknown>> {
  if (command === 'preview') {
    const str = { type: 'string' } as const
    const many = { type: 'string', multiple: true } as const
    const { values: v } = parseArgs({ args: expandImages(args), options: {
      text: str, 'text-file': str, image: many, caption: many, title: str, digest: str, cover: str, scene: str,
      quality: str, author: str, profile: str, workdir: str, layout: str, edits: str, epigraph: str, account: str, action: str,
      'footer-image': str, 'footer-text': str,
    } })
    if ((v.text === undefined) === (v['text-file'] === undefined)) throw new Error('请提供 --text 或 --text-file 中的一项')
    const source = v.text ?? readFileSync(resolve(v['text-file']!), 'utf8').replace(/^\uFEFF/, '')
    const images = v.image ?? []
    if (!images.length) throw new Error('请提供至少一张有序照片（--images）')
    if ((v.caption?.length ?? 0) > images.length) throw new Error('图注数超过照片数')
    const workdir = resolve(v.workdir || resolve('.wechat-mp', randomUUID()))
    const profile = profileFor(workdir, v.profile)
    const layout = layoutFor(images, v.caption || [], v.cover, v.layout)
    const scene = layout.scene ?? v.scene ?? profile.scene ?? 'daily'
    if (!['daily', 'family', 'travel', 'anniversary', 'auto'].includes(scene)) throw new Error('场景可选 daily、family、travel、anniversary、auto')
    if (v.quality && !['lossless', 'balanced'].includes(v.quality)) throw new Error('画质可选 balanced 或 lossless')
    const action = checkAction(v.action)
    const quality = v.quality as 'lossless' | 'balanced' | undefined
    const {text, changes} = applyEdits(source, v.edits ? readJson(v.edits) : [])
    const suggestions: string[] = []
    const sentences = text.match(/[^。！？\n]+[。！？]?/gu) ?? []
    for (const word of (profile.avoid || []) as string[]) {
      for (const sentence of sentences.filter(s => s.includes(word))) suggestions.push('作者偏好避用“' + word + '”，可复核原句：“' + sentence.trim() + '”')
    }
    const result = await preview({ ...layout, scene, workdir, text, title: v.title, digest: v.digest,
      footerImage: v['footer-image'], footerText: v['footer-text'],
      epigraph: v.epigraph, quality, author: v.author ?? profile.author, profile, python: python(), changes, suggestions })
    const bundle = await loadBundle(result.bundleDir)
    return { ...result, workdir, changes, suggestions, preferences: profile,
      ...(v.account ? { account: v.account, action, confirmation: confirmation(action, v.account, bundle) } : {}) }
  }

  const str = { type: 'string' } as const
  const inputs = { account: str, bundle: str }
  const opts = command === 'check' ? { ...inputs, offline: { type: 'boolean' } as const, action: str }
    : command === 'status' ? { ...inputs, claim: str }
    : { ...inputs, confirmed: str, claim: str, ...(command === 'update' ? { overwrite: str } : {}) }
  const { values } = parseArgs({ args, options: opts })
  const v = values as { account?: string; bundle?: string; offline?: boolean; action?: string; confirmed?: string; overwrite?: string; claim?: string }
  const cfg = credentials()
  const appid = v.account || cfg.appid
  if (!v.offline && cfg.appid && appid !== cfg.appid) throw new Error('指定账号与本机凭据不匹配，请切换账号配置后重新确认')
  const bundleDir = v.bundle && resolve(v.bundle)
  const bundle = bundleDir ? await loadBundle(bundleDir, { requireCurrent: command !== 'status' }) : undefined
  const action = checkAction(v.action)
  if (command === 'check') {
    const targetMatches = Boolean(appid && appid === cfg.appid && cfg.secret)
    const report = { account: appid ?? null, name: appid === cfg.appid ? cfg.name : undefined,
      credentials: targetMatches ? 'configured' : 'missing', ip: 'unverified', draft_access: 'unverified',
      ...(bundle && appid ? { action, title: bundle.title, articleId: bundle.articleId, version: bundle.version,
        confirmation: confirmation(action, appid, bundle) } : {}) }
    if (v.offline || !targetMatches) return { ...report, ok: Boolean(v.offline), message: v.offline ? '离线检查' : '请在本机配置 WECHAT_APPID 和 WECHAT_APPSECRET，再运行 check' }
    const client = new WechatClient(appid!, cfg.secret!)
    try { await client.token() } catch (error) {
      return { ...report, ok: false, ip: error instanceof WxError && error.code === 40164 ? 'denied' : 'unverified',
        ...errorInfo(error) }
    }
    const article = bundle && bundleDir ? await syncDraft('status', bundleDir, bundle, appid!, stateDir, client, {}) : undefined
    return { ...report, ok: true, credentials: 'token_obtained', ip: 'accepted_for_token', article,
      draft_access: article && 'ok' in article && article.ok && 'checks' in article ? 'see_article_checks' : 'unverified' }
  }
  if (!bundle || !bundleDir || !v.account) throw new Error('请指定 --bundle 预览版本目录和 --account 目标 AppID')
  if (!cfg.secret || !cfg.appid) throw new Error('尚未配置微信凭据，请在本机配置 WECHAT_APPID 和 WECHAT_APPSECRET')
  const result = await syncDraft(command, bundleDir, bundle, v.account, stateDir, new WechatClient(cfg.appid, cfg.secret), v)
  return { account: v.account, title: bundle.title, backend, ...result }
}

function errorInfo(error: unknown) {
  return { message: error instanceof Error ? error.message : String(error),
    ...(error instanceof WxError ? { errcode: error.code } : {}) }
}

const [cmd, ...args] = process.argv.slice(2)
if (cmd === '--help' || !cmd || args.includes('--help')) {
  console.log(JSON.stringify(cmd && Object.hasOwn(help, cmd) ? help[cmd as Command] : help, null, 2))
} else {
  try {
    if (!Object.hasOwn(help, cmd)) throw new Error('未知命令，可用 preview、check、draft、update、status')
    const result = await run(cmd as Command, args)
    console.log(JSON.stringify(result))
    if (result.ok === false) process.exitCode = 1
  } catch (error) {
    const code = (error as { exitCode?: number })?.exitCode || 1
    console.log(JSON.stringify({ ok: false, code, ...errorInfo(error) }))
    process.exitCode = code
  }
}
