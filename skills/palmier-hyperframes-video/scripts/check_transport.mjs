// Offline by default; --live adds read-only initialize/list-tools verification.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const doc = await readFile(new URL('../references/palmier.md', import.meta.url), 'utf8');
const source = doc.match(/```javascript\n([\s\S]*?)\n```/)?.[1];
assert.ok(source, 'Documented transport example missing');
const build = new Function('fetch', `return (async () => {\n${source}\nreturn {rpc, catalog};\n})();`);
const requests = [];
const replies = [
  JSON.stringify({id:1, result:{protocolVersion:'2024-11-05'}}),
  '',
  'id: event-1\r\nevent: message\r\ndata: {"jsonrpc":"2.0","method":"notifications/tools/list_changed"}\r\n\r\n' +
  'id: event-2\r\ndata: {"id":2,"result":{"tools":[{"name":"get_timeline"}]}}\r\n\r\n',
  JSON.stringify({id:3, result:{isError:true, content:[]}}),
  '',
  JSON.stringify({id:5, error:{code:-32602, message:'invalid input'}}),
  ''
];
const fakeFetch = async (_url, options) => {
  requests.push({body:JSON.parse(options.body), headers:{...options.headers}});
  const index = requests.length - 1;
  return {
    ok:index !== 6, status:index === 6 ? 503 : 200,
    headers:{get:name => name === 'mcp-session-id' ? 'fixture-session' : null},
    text:async () => replies[index]
  };
};
const client = await build(fakeFetch);
assert.equal(client.catalog.tools[0].name, 'get_timeline');
assert.equal(requests[1].body.method, 'notifications/initialized');
assert.equal('id' in requests[1].body, false);
assert.equal(requests[2].headers['Mcp-Session-Id'], 'fixture-session');
await assert.rejects(client.rpc('tools/call', {}), /MCP error/);
await assert.rejects(client.rpc('tools/call', {}), /outcome unknown/);
await assert.rejects(client.rpc('tools/call', {}), /MCP error/);
await assert.rejects(client.rpc('tools/call', {}), /HTTP 503/);
assert.equal(requests.length, 7, 'Unexpected automatic retry');
console.log('PASS: JSON, multi-event SSE, session header, notification, tool/RPC/HTTP errors, empty response and no automatic retry.');

if (process.argv.includes('--live')) {
  const live = await build(globalThis.fetch);
  assert.ok(Array.isArray(live.catalog.tools));
  console.log(`PASS: live read-only MCP discovery returned ${live.catalog.tools.length} tools.`);
}
