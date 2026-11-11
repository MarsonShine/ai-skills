import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { loadBundle } from '../skills/wechat-mp-publisher/scripts/preview.ts'
import { confirmation, syncDraft } from '../skills/wechat-mp-publisher/scripts/sync.ts'
import { WechatClient, WxError } from '../skills/wechat-mp-publisher/scripts/wechat.ts'

const cli = fileURLToPath(new URL('../skills/wechat-mp-publisher/scripts/wx_publish.ts', import.meta.url))
const pixel = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXkAAAAASUVORK5CYII=', 'base64')

function invoke(root, ...args) {
  const env = { ...process.env, HOME: root, USERPROFILE: root, WECHAT_APPID: '', WECHAT_APPSECRET: '', WECHAT_MP_STATE_DIR: join(root, 'state') }
  const result = spawnSync(process.execPath, [cli, ...args], { env, encoding: 'utf8' })
  assert.notEqual(result.stdout, '', result.stderr)
  return JSON.parse(result.stdout)
}

test('review and revise through the CLI, submit exactly that revision through the WeChat adapter', async t => {
  const root = await mkdtemp(join(tmpdir(), 'wechat-publish-'))
  t.after(() => rm(root, { recursive: true, force: true }))
  const img = join(root, '测试图.png'), workdir = join(root, '文章'), profile = join(root, 'profile.yaml')
  const edit = join(root, 'edits.json'), layout = join(root, 'layout.json')
  await writeFile(img, pixel)
  await writeFile(profile, 'author: 小禾\nperson: third\ntone: 简洁\navoid: [赶路]\n')
  await writeFile(edit, JSON.stringify([{ before: '原定周六，后来没去。', after: '原定周六。后来没去。', reason: '拆句，保留否定' }]))
  await writeFile(layout, JSON.stringify({ scene: 'travel', order: [2, 1], cover: 2 }))
  const args = ['preview', '--workdir', workdir, '--images', img, img, '--caption', '原图一', '--caption', '原图二',
    '--text', '原定周六，后来没去。\n\n没有赶路。', '--profile', profile, '--account', 'wxfixture']
  const first = invoke(root, ...args)
  assert.equal(first.ok, true, JSON.stringify(first))
  assert.equal(first.suggestions.length, 1)
  const revised = invoke(root, ...args, '--edits', edit, '--layout', layout)
  assert.equal(revised.ok, true, JSON.stringify(revised))
  assert.equal(revised.articleId, first.articleId)
  assert.notEqual(revised.version, first.version)
  const stale = invoke(root, 'draft', '--bundle', first.bundleDir, '--account', 'wxfixture', '--confirmed', first.confirmation)
  assert.match(stale.message, /新版|当前版本/)
  const checked = invoke(root, 'check', '--offline', '--bundle', revised.bundleDir, '--account', 'wxfixture')
  assert.equal(checked.confirmation, revised.confirmation)
  assert.equal(checked.credentials, 'missing')
  const bundle = await loadBundle(revised.bundleDir, { requireCurrent: true })
  assert.ok(bundle.html.indexOf('原图二') < bundle.html.indexOf('原图一'))
  assert.match(bundle.html, /原定周六。后来没去。/)
  assert.doesNotMatch(bundle.html, /拆句，保留否定/)
  assert.match(await readFile(revised.previewPath, 'utf8'), /拆句，保留否定/)

  let article
  const calls = []
  const api = new WechatClient('wxfixture', 'fixture-only')
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    const endpoint = url.pathname.replace('/cgi-bin/', '')
    calls.push(endpoint)
    assert.equal(url.origin, 'https://api.weixin.qq.com')
    assert.equal(options.method, 'POST')
    if (endpoint === 'stable_token') return Response.json({ access_token: 'test_token', expires_in: 7200 })
    assert.equal(url.searchParams.get('access_token'), 'test_token')
    if (endpoint === 'draft/batchget') return Response.json({ item: [] })
    if (endpoint === 'media/uploadimg' || endpoint === 'material/add_material') {
      const actual = Buffer.from(await options.body.get('media').arrayBuffer())
      const prepared = endpoint === 'media/uploadimg' ? bundle.images[0].path : bundle.cover
      assert.deepEqual(actual, await readFile(join(revised.bundleDir, prepared)))
      if (endpoint === 'material/add_material') {
        assert.equal(url.searchParams.get('type'), 'image')
        return Response.json({ media_id: 'cover_1' })
      }
      return Response.json({ url: 'https://example.test/image?a=1&b=2' })
    }
    const data = JSON.parse(options.body)
    if (endpoint === 'draft/add') {
      assert.equal(data.articles.length, 1)
      article = data.articles[0]
      return Response.json({ media_id: 'draft_1' })
    }
    assert.equal(endpoint, 'draft/get')
    assert.equal(data.media_id, 'draft_1')
    return Response.json({ news_item: [{ ...article, url: 'https://example.test/view' }] })
  })
  const result = await syncDraft('draft', revised.bundleDir, bundle, 'wxfixture', join(root, 'state'), api, { confirmed: checked.confirmation })
  assert.equal(result.status, 'verified', JSON.stringify(result))
  assert.equal(result.media_id, 'draft_1')
  assert.equal(article.thumb_media_id, 'cover_1')
  assert.equal(article.author, '小禾')
  assert.equal(article.content.match(/https:\/\/example.test\/image\?a=1&amp;b=2/g).length, 2)
  assert.equal(calls.filter(v => v === 'draft/add').length, 1)
  assert.notEqual(confirmation('update', 'wxfixture', bundle), checked.confirmation)
})

test('HTTP errors preserve genuine WeChat refusals, ambiguity and credential redaction', async t => {
  const api = new WechatClient('test-app-id', 'sensitive-test-secret')
  const article = { title: '样稿', digest: '', author: '', content: '原文', thumb_media_id: 'cover' }
  let status = 403
  t.mock.method(globalThis, 'fetch', async url => {
    if (url.pathname.endsWith('stable_token')) return Response.json({ access_token: 'sensitive-token', expires_in: 7200 })
    return Response.json({ errcode: 48001, errmsg: 'denied sensitive-test-secret access_token=sensitive-token' }, { status })
  })
  await assert.rejects(api.add(article), e => e instanceof WxError && e.code === 48001 && !e.ambiguous && !e.message.includes('sensitive'))
  status = 502
  await assert.rejects(api.add(article), e => e instanceof WxError && e.ambiguous)
})
