import test from 'node:test';
import assert from 'node:assert/strict';
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