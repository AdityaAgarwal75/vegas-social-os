import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {checkBrowserCapacity} from '../worker/flow.mjs';

test('Chrome admission requires enough available memory', () => {
  assert.doesNotThrow(() => checkBrowserCapacity(1900 * 1024, 1.5, 2));
  assert.throws(() => checkBrowserCapacity(1200 * 1024, 1.5, 2), /memory/);
  assert.throws(() => checkBrowserCapacity(NaN, 1.5, 2), /memory/);
});

test('Chrome admission refuses extreme host load', () => {
  assert.throws(() => checkBrowserCapacity(2500 * 1024, 12, 2), /load/);
  assert.doesNotThrow(() => checkBrowserCapacity(2500 * 1024, 5, 2));
});
test('Chrome admission parser matches real Linux MemAvailable field', () => {
  const source = readFileSync(new URL('../worker/flow.mjs', import.meta.url), 'utf8');
  assert.ok(source.includes(String.raw`meminfo.match(/^MemAvailable:\s+(\d+) kB/m)`));
  const meminfo = `MemTotal:       3900000 kB
MemAvailable:   3257000 kB
`;
  const matched = meminfo.match(/^MemAvailable:\s+(\d+) kB/m);
  assert.equal(Number(matched?.[1]),3257000);
  assert.doesNotThrow(() => checkBrowserCapacity(3257000,1.5,2));
});
