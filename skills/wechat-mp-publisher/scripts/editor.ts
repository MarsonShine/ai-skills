import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export function readJson(file: string) {
  return JSON.parse(readFileSync(resolve(file), 'utf8').replace(/^\uFEFF/, ''))
}

export function python() {
  return process.env.WECHAT_MP_PYTHON || process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3')
}

export function profileFor(workdir: string, explicit?: string) {
  const file = explicit || [resolve(workdir, 'profile.yaml'), resolve(homedir(), '.config/wechat-mp/profile.yaml')].find(existsSync)
  if (!file) return {}
  const script = fileURLToPath(new URL('./profile.py', import.meta.url))
  try {
    return JSON.parse(execFileSync(python(), ['-X', 'utf8', '-B', script, '--file', file], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }))
  } catch (error) {
    const failure = error as { stderr?: string; message: string }
    throw new Error('读取作者偏好失败：' + (failure.stderr?.trim() || failure.message))
  }
}

type Edit = { before: string; after: string; reason: string; occurrence?: number }

export function applyEdits(source: string, list: Edit[]) {
  if (!Array.isArray(list)) throw new Error('edits 应为修改列表')
  const edits = list.map(edit => {
    if (!edit || typeof edit.before !== 'string' || !edit.before || typeof edit.after !== 'string' ||
        typeof edit.reason !== 'string' || !edit.reason.trim()) throw new Error('每处修改需要 before、after、reason')
    const places: number[] = []
    for (let pos = source.indexOf(edit.before); pos >= 0; pos = source.indexOf(edit.before, pos + edit.before.length)) places.push(pos)
    const occurrence = edit.occurrence ?? 1
    if ((!edit.occurrence && places.length !== 1) || !Number.isInteger(occurrence) || occurrence < 1 || occurrence > places.length) {
      throw new Error('原文不能唯一定位修改，请核对 before，或给出 occurrence（从 1 开始）：' + edit.before)
    }
    return { ...edit, start: places[occurrence - 1] }
  }).sort((a, b) => a.start - b.start)
  let cursor = 0
  let text = ''
  for (const { start, before, after } of edits) {
    if (start < cursor) throw new Error('两处修改覆盖同一段原文，请合并修改')
    text += source.slice(cursor, start) + after
    cursor = start + before.length
  }
  return { text: text + source.slice(cursor), changes: edits.map(({ before, after, reason }) => ({ before, after, reason })) }
}

export function layoutFor(images: string[], captions: string[], cover?: string, layoutFile?: string) {
  const layout = layoutFile ? readJson(layoutFile) : {}
  if (!layout || typeof layout !== 'object' || Array.isArray(layout)) throw new Error('layout 应为布局对象')
  const order: number[] = layout.order ?? images.map((_, n) => n + 1)
  const valid = (n: number) => Number.isInteger(n) && n >= 1 && n <= images.length
  if (!Array.isArray(order) || order.length !== images.length || !order.every(valid) || new Set(order).size !== images.length) {
    throw new Error('layout.order 应完整列出每张照片的编号，每个编号使用一次')
  }
  if (layout.cover !== undefined && !valid(layout.cover)) throw new Error('layout.cover 应为照片编号')
  const selectedCover = layout.cover ? images[layout.cover - 1] : cover || images[0]
  const index = selectedCover && images.findIndex(img => resolve(img) === resolve(selectedCover))
  return { images: order.map(n => images[n - 1]), captions: order.map(n => captions[n - 1] ?? ''),
    imageNumbers: order, cover: selectedCover, coverNumber: layout.cover ?? (typeof index === 'number' && index >= 0 ? index + 1 : undefined), scene: layout.scene }
}
