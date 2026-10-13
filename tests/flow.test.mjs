import test from 'node:test';
import assert from 'node:assert/strict';
import {parseQuote, uniqueNewAssets, run} from '../worker/flow.mjs';

test('credit quote must be unique and positive',()=>{
  assert.equal(parseQuote('Generate · 20 credits'),20);
  assert.throws(()=>parseQuote('Balance 50 credits · Generate 20 credits'));
  assert.throws(()=>parseQuote('Generate'));
  assert.throws(()=>parseQuote('0 credits'));
});
test('downloads track identity, never gallery ordering',()=>{
  assert.deepEqual(uniqueNewAssets(['old-a','old-b'],['old-b','new','old-a']),['new']);
  assert.deepEqual(uniqueNewAssets(['old-a'],['new-b','old-a','new-c']),['new-b','new-c']);
});
test('worker refuses untrusted account paths',async()=>{
  await assert.rejects(run({account_id:'../../outside',data_dir:'/tmp'}),/Invalid managed account/);
});
