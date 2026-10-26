import { test } from 'node:test';
import assert from 'node:assert/strict';
import { apiFetch } from '../web/src/lib/browser-api.ts';
import { locationKey, snapshotRows } from '../web/src/lib/browser-history.ts';
import { fetchJson, ProviderError } from '../web/src/lib/providers.ts';

const sampleHour = (time, temperature, precipitation) => ({time, temperature, precipitation, wind: 0});
const sampleWeather = {
  location: {lat: 37.2319, lon: -8.6267, timezone: 'Europe/Lisbon'},
  forecasts: [{id: 'example-model', fetchedAt: '2026-10-26T20:00:00.000Z', hours: [sampleHour(1793044800, -2, 0), sampleHour(1793048400, null, null)]}],
};

test('browser snapshot identity deduplicates repeat fetches without replacing nulls or zeros', () => {
  const rows = snapshotRows(sampleWeather);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].locationKey, locationKey(37.2319, -8.6267));
  assert.equal(rows[0].temperature, -2);
  assert.equal(rows[0].precipitation, 0);
  assert.equal(rows[0].wind, 0);
  assert.equal(rows[1].temperature, null);
  assert.equal(rows[1].precipitation, null);
  assert.deepEqual(rows, snapshotRows(sampleWeather));
  assert.notEqual(rows[0].id, rows[1].id);
});

test('invalid coordinates are rejected before any upstream request', async context => {
  let calls = 0;
  context.mock.method(globalThis, 'fetch', async () => {calls++; throw Error('must not fetch');});
  const result = await apiFetch('/api/weather?lat=91&lon=0&timezone=Europe/Lisbon');
  assert.equal(result.status, 400);
  assert.match((await result.json()).error, /Latitude/);
  assert.equal(calls, 0);
});

test('a layout without a verified outline never substitutes the nearby GP circuit', async () => {
  const absent = await apiFetch('/api/geometry?lat=50.3566&lon=6.9689&trackId=nordschleife');
  assert.equal(absent.status, 200);
  const geometry = await absent.json();
  assert.deepEqual(geometry.coordinates, []);
  assert.match(geometry.message, /different nearby circuit has not been substituted/);
  const known = await apiFetch('/api/geometry?lat=50.3356&lon=6.9475&trackId=nurburgring');
  const knownGeometry = await known.json();
  assert.ok(knownGeometry.coordinates.length > 0);
  const [latitude, longitude] = knownGeometry.coordinates[0][0];
  assert.ok(latitude > 49 && latitude < 51);
  assert.ok(longitude > 6 && longitude < 8);
});

test('an already aborted local request rejects with the browser abort contract', async () => {
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(apiFetch('/api/health', {signal: controller.signal}), error => error.name === 'AbortError');
});

test('provider Retry-After stops immediate repeated requests to a rate-limited URL', async context => {
  const url = 'https://example.invalid/pitwall-rate-limit-test';
  let calls = 0;
  context.mock.method(globalThis, 'fetch', async () => {
    calls++;
    return new Response('{}', {status: 429, headers: {'Retry-After': '60'}});
  });
  await assert.rejects(fetchJson(url), error => error instanceof ProviderError && error.code === 'rate_limit');
  await assert.rejects(fetchJson(url), error => error instanceof ProviderError && error.code === 'rate_limit');
  assert.equal(calls, 1);
});
