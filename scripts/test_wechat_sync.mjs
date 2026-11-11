import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { confirmation, syncDraft } from '../skills/wechat-mp-publisher/scripts/sync.ts';
import { WxError } from '../skills/wechat-mp-publisher/scripts/wechat.ts';

async function setup(t) {
  const work = await mkdtemp(join(tmpdir(), 'wx-sync-'));
  t.after(() => rm(work, { recursive: true, force: true }));
  const images = ['images/body-1.jpg', 'images/body-2.png', 'images/cover.jpg'].map((path, i) => ({ path, sha256: 'hash-'+i }));
  const body = '<p>正文 images/body-1.jpg</p><img src="images/body-1.jpg" alt="images/body-2.png" />' +
    '<span>图注甲</span><img src="images/body-2.png" /><span>图注乙</span>';
  const bundle = { articleId:'article-a', version:'first', title:'郊游', digest:'春天', author:'阿毛', html:body, cover:images[2].path, images };
  const db = new Map(), calls = { add:0, update:0, uploads:[] };
  const client = {
    async uploadBody(path, sha) { calls.uploads.push([path, sha]); return 'https://img.service.example/'+sha+'?a=b&c=d'; },
    async uploadCover(path, sha) { calls.uploads.push([path, sha]); return 'cover-'+sha; },
    async add(article) { const id='draft-'+ ++calls.add; db.set(id, structuredClone(article)); return id; },
    async update(id, article) { calls.update++; db.set(id, structuredClone(article)); },
    async get(id) { if (!db.has(id)) throw new WxError('无效标识',40007); return structuredClone(db.get(id)); },
    async recent() { return [...db].reverse().slice(0,20).map(([id,article]) => ({id, article:structuredClone(article)})); },
  };
  const point = (b) => writeFile(join(work, 'current.json'), JSON.stringify({articleId:b.articleId,version:b.version}));
  await point(bundle);
  const run = (action, b=bundle, extra={}, appid='account-a') =>
    syncDraft(action, join(work,'versions',b.version), b, appid, join(work,'state'), client,
      { confirmed: confirmation(action,appid,b), ...extra });
  return {work, bundle, db, calls, client, run, point};
}

test('confirmations are bound to action, account, article and version; duplicate requests reuse one verified draft', async t => {
  const {bundle,db,calls,run} = await setup(t);
  for (const confirmationFor of [
    ['update','account-a',bundle], ['draft','account-b',bundle],
    ['draft','account-a',{...bundle,version:'older'}], ['draft','account-a',{...bundle,articleId:'other'}],
  ]) {
    assert.equal((await run('draft',bundle,{confirmed:confirmation(...confirmationFor)})).status,'confirmation_required');
  }
  assert.equal(calls.uploads.length,0);
  const created=await run('draft');
  assert.equal(created.status,'verified');
  const html=db.get(created.media_id).content;
  assert.match(html,/<p>正文 images\/body-1.jpg<\/p>/);
  assert.match(html,/alt="images\/body-2.png"/);
  assert.match(html,/src="https:\/\/img\.service\.example\/hash-0\?a=b&amp;c=d"/);
  assert.deepEqual(calls.uploads.map(entry=>entry[1]),bundle.images.map(i=>i.sha256));
  assert.equal((await run('draft')).reused,true);
  assert.equal((await run('status',bundle,{},'unrelated-account')).status,'no_draft');
  assert.equal(calls.add,1);
});

test('an accepted add whose reply is lost reconciles by exact content and never adds a second time', async t => {
  const {client,db,run,calls}=await setup(t);
  const add=client.add.bind(client);
  client.add=async article => { await add(article); throw new Error('connection closed'); };
  assert.equal((await run('draft')).status,'creation_unknown');
  const saved=structuredClone(db.get('draft-1'));
  db.set('draft-2', saved);
  const unknown=await run('status');
  assert.deepEqual(unknown.candidates.sort(),['draft-1','draft-2']);
  assert.equal(unknown.candidate_details[0].title,'郊游');
  assert.equal(unknown.candidate_details[0].image_count,2);
  assert.equal((await run('draft', undefined, {claim:'bad'})).status,'creation_unknown');
  const recovered=await run('status', undefined, {claim:'draft-1'});
  assert.equal(recovered.media_id,'draft-1');
  assert.equal(recovered.status,'verified');
  assert.equal(calls.add,1);
});

test('an indeterminate add with zero candidates remains unresolved on subsequent draft requests', async t => {
  const {client,run,calls}=await setup(t);
  client.add=async () => { calls.add++; throw new Error('timeout'); };
  assert.equal((await run('draft')).status,'creation_unknown');
  assert.deepEqual((await run('draft')).candidates,[]);
  assert.equal(calls.add,1);
});

test('read failures preserve the returned media_id; removed drafts are never silently recreated',async t=>{
  const {client,run,db,calls}=await setup(t);
  const get=client.get;
  client.get=async()=>{ throw new WxError('token error',40001); };
  const pending=await run('draft');
  assert.equal(pending.status,'awaiting_verification');
  assert.equal(pending.media_id,'draft-1');
  client.get=get;
  assert.equal((await run('status')).status,'verified');
  db.clear();
  assert.equal((await run('draft')).status,'missing');
  assert.equal(calls.add,1);
});

test('modified captions, image order, cover and styling are visible; overwrite is bound to a fresh remote baseline',async t=>{
  const {bundle,db,run,point,calls}=await setup(t);
  const {media_id:id}=await run('draft');
  const edited=db.get(id);
  const pending={...bundle,version:'second',title:'我的郊游'};
  await point(pending);
  edited.content=edited.content.replaceAll('hash-0','hash-1').replace('图注乙','新图注').replace('<span>','<span style="color:red">');
  edited.thumb_media_id='new-cover';
  edited.need_open_comment=1;
  edited.product_info={footer_product_info:{product_id:'editor-product'}};
  const mismatch=await run('update',pending);
  assert.equal(mismatch.status,'conflict');
  assert.deepEqual(mismatch.changed,['cover','images','content','editor_settings']);
  assert.deepEqual(mismatch.differences.cover,{old:'cover-hash-2',current:'new-cover'});
  assert.equal(mismatch.differences.images.positions[0].position,1);
  assert.ok(mismatch.differences.content.current.includes('hash-1'));
  edited.content=edited.content.replace('color:red','color:blue');
  const again=await run('update',pending,{overwrite:mismatch.overwrite});
  assert.equal(again.status,'conflict');
  assert.notEqual(again.overwrite,mismatch.overwrite);
  assert.equal(calls.update,0);
  assert.equal((await run('update',pending,{overwrite:again.overwrite})).status,'verified');
  assert.equal(db.get(id).need_open_comment,1);
  assert.deepEqual(db.get(id).product_info,edited.product_info);
  assert.equal(db.get(id).title,'我的郊游');
});

test('missing an image fails read-back even if other images still have WeChat URLs',async t=>{
  const {client,db,calls,run}=await setup(t);
  const add=client.add;
  client.add=async article=>{
    const id=await add(article);
    db.get(id).content=db.get(id).content.replace(/<img [^>]+>/,'');
    return id;
  };
  const result=await run('draft');
  assert.equal(result.status,'verification_mismatch');
  assert.equal(result.checks.images,false);
  assert.equal((await run('draft')).status,'verification_mismatch');
  assert.equal(calls.add,1);
});

test('equivalent HTML syntax verifies and final HTML size is checked after URL substitution',async t=>{
  const {client,db,calls,run,point,bundle}=await setup(t);
  const add=client.add;
  client.add=async article=>{
    const id=await add(article);
    db.get(id).content=article.content.replaceAll(' />','>').replaceAll('&amp;', '&#38;').replaceAll('<span>', '<SPAN>');
    return id;
  };
  assert.equal((await run('draft')).status,'verified');
  const huge={...bundle,version:'oversize',html:'x'.repeat(19970)+'<img src="images/body-1.jpg" />'};
  await point(huge);
  await assert.rejects(()=>run('update',huge), /正文超限/);
  assert.equal(calls.update,0);
});

test('concurrent calls hold one exclusive write lock',async t=>{
  const {client,run,calls}=await setup(t);
  let release, started;
  const gate=new Promise(r=>{release=r;}), entered=new Promise(r=>{started=r;});
  const firstUpload=client.uploadBody;
  client.uploadBody=async(...args)=>{started(); await gate; return firstUpload(...args);};
  const first=run('draft');
  await entered;
  try { assert.equal((await run('draft')).status,'busy'); } finally {release();}
  assert.equal((await first).status,'verified');
  assert.equal(calls.add,1);
});

test('a process killed after remote acceptance releases its lock and the next process recovers from durable intent', async t => {
  const { work, bundle, db, run } = await setup(t);
  const syncModule = new URL('../skills/wechat-mp-publisher/scripts/sync.ts', import.meta.url).href;
  const childProgram = `
    import { join } from 'node:path';
    const [moduleUrl, work, encoded] = process.argv.slice(1);
    const { syncDraft, confirmation } = await import(moduleUrl);
    const bundle = JSON.parse(encoded);
    const client = {
      async recent() { return []; },
      async uploadBody(file, sha) { return 'https://images.example/' + sha; },
      async uploadCover() { return 'cover-id'; },
      async add(article) {
        process.send(article);
        await new Promise(resolve => process.once('message', resolve));
      }
    };
    await syncDraft('draft', join(work, 'versions', bundle.version), bundle, 'account-a',
      join(work, 'state'), client, {confirmed: confirmation('draft', 'account-a', bundle)});
  `;
  const child = spawn(process.execPath, ['--input-type=module', '-e', childProgram, syncModule, work, JSON.stringify(bundle)],
    { stdio: ['ignore', 'ignore', 'inherit', 'ipc'], windowsHide: true });
  const stopped = once(child, 'exit');
  t.after(() => { if (child.exitCode === null && child.signalCode === null) child.kill(); });
  const [accepted] = await Promise.race([
    once(child, 'message'),
    stopped.then(() => { throw new Error('child exited before the simulated accept'); }),
  ]);
  db.set('remote-after-crash', accepted);
  assert.equal((await run('draft')).status, 'busy');
  child.kill('SIGKILL');
  await stopped;
  const recovered = await run('status');
  assert.equal(recovered.status, 'verified');
  assert.equal(recovered.media_id, 'remote-after-crash');
});

test('a preview superseded during upload never writes a draft',async t=>{
  const {bundle,client,calls,run,point}=await setup(t);
  const cover=client.uploadCover;
  client.uploadCover=async(...args)=>{await point({...bundle, version:'newer'});return cover(...args);};
  await assert.rejects(()=>run('draft'),/预览已有新版/);
  assert.equal(calls.add,0);
});

test('a newer preview during the list request prevents every upload', async t => {
  const { bundle, client, calls, run, point } = await setup(t);
  client.recent = async () => { await point({ ...bundle, version: 'newer' }); return []; };
  await assert.rejects(() => run('draft'), /预览已有新版/);
  assert.equal(calls.uploads.length, 0);
  assert.equal(calls.add, 0);
});

test('a newer preview during a body upload stops all remaining images and the permanent cover', async t => {
  const { bundle, client, calls, run, point } = await setup(t);
  const upload = client.uploadBody;
  client.uploadBody = async (...args) => {
    const result = await upload(...args);
    await point({ ...bundle, version: 'newer' });
    return result;
  };
  await assert.rejects(() => run('draft'), /预览已有新版/);
  assert.deepEqual(calls.uploads.map(([, sha]) => sha), [bundle.images[0].sha256]);
  assert.equal(calls.add, 0);
});

test('an unavailable pre-submit list does not block creation and requires a deliberate claim after a lost reply', async t => {
  const { client, calls, run } = await setup(t);
  const recent = client.recent, add = client.add;
  client.recent = async () => { throw new WxError('no permission', 48001); };
  client.add = async article => { await add(article); throw new Error('connection closed'); };
  assert.equal((await run('draft')).status, 'creation_unknown');
  assert.equal(calls.add, 1);
  assert.equal((await run('status')).code, 48001);
  client.recent = recent;
  const candidate = await run('status');
  assert.equal(candidate.status, 'creation_unknown');
  assert.deepEqual(candidate.candidates, ['draft-1']);
  assert.equal((await run('status', undefined, { claim: 'draft-1' })).status, 'verified');
  assert.equal(calls.add, 1);
});

test('a known rejection retains the redacted server diagnostic and is safe to retry', async t => {
  const {client,run}=await setup(t);
  const add=client.add;
  client.add=async()=>{ throw new WxError('invalid title, access_token=sensitive-id',45003); };
  const rejected=await run('draft');
  assert.equal(rejected.status,'rejected');
  assert.equal(rejected.code,45003);
  assert.match(rejected.errmsg,/invalid title/);
  assert.ok(!rejected.errmsg.includes('sensitive-id'));
  client.add=add;
  assert.equal((await run('draft')).status,'verified');
});

test('changed text past a long identical prefix is shown at the difference and preserves a safe backend link', async t => {
  const {bundle,client,db,run}=await setup(t);
  const local={...bundle,html:bundle.html.replace('图注乙','相同前缀'.repeat(110)+'凌晨四点')};
  const add=client.add;
  client.add=async article=>{
    const id=await add(article);
    const remote=db.get(id);
    remote.content=remote.content.replace('凌晨四点','凌晨五点');
    remote.url='https://mp.weixin.qq.com/preview';
    return id;
  };
  const mismatch=await run('draft',local);
  assert.equal(mismatch.status,'verification_mismatch');
  assert.match(mismatch.differences.content.old,/四点/);
  assert.match(mismatch.differences.content.current,/五点/);
  assert.equal(mismatch.preview_url,'https://mp.weixin.qq.com/preview');
});

test('a conflicting duplicate src attribute uses the same first occurrence as an HTML renderer', async t => {
  const {client,db,run}=await setup(t);
  const add=client.add;
  client.add=async article=>{
    const id=await add(article);
    db.get(id).content=article.content.replace('<img src=', '<img src="https://other.example/other" src=');
    return id;
  };
  const result=await run('draft');
  assert.equal(result.status,'verification_mismatch');
  assert.equal(result.checks.images,false);
});
