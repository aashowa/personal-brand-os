// Run a batch of Palmier MCP tool calls in ONE session (initialize -> calls in order) and print each result.
// usage: node palmier_mcp.mjs '[["manage_project",{"action":"open","name":"..."}],["set_active_timeline",{"timelineId":"..."}],["get_timeline",{}]]'
//        node palmier_mcp.mjs list            -> tool catalog with schemas
// env:   PALMIER_MCP (default http://127.0.0.1:19789/mcp), MAX (chars of text printed per call, default 20000)
// Images returned by a tool (inspect_timeline, capture previews) are saved to the cwd and printed as "IMAGE <path>".
// Stops at the first tool error (exit 1): read state before retrying anything.
import fs from 'node:fs';
const endpoint = process.env.PALMIER_MCP || 'http://127.0.0.1:19789/mcp';
const headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'};
let nextId = 1;
async function rpc(method, params, notification = false) {
  const body = {jsonrpc: '2.0', method, params}; if (!notification) body.id = nextId++;
  const r = await fetch(endpoint, {method: 'POST', headers, body: JSON.stringify(body), signal: AbortSignal.timeout(600000)});
  const s = r.headers.get('mcp-session-id'); if (s) headers['Mcp-Session-Id'] = s;
  const raw = await r.text(); if (!r.ok) throw Error(`HTTP ${r.status} ${raw.slice(0, 300)}`);
  if (!raw.trim()) { if (notification) return; throw Error('empty response; outcome unknown, read state before retrying'); }
  const ev = raw.split(/\r?\n\r?\n/).map(b => b.split(/\r?\n/).filter(l => l.startsWith('data:')).map(l => l.slice(5).trimStart()).join('\n'));
  const msgs = ev.filter(Boolean).map(x => JSON.parse(x));
  const out = msgs.length ? msgs.find(m => m.id === body.id) : JSON.parse(raw);
  if (out?.error) throw Error(JSON.stringify(out.error));
  return out.result;
}
await rpc('initialize', {protocolVersion: '2024-11-05', capabilities: {}, clientInfo: {name: 'palmier-hyperframes-video', version: '2'}});
await rpc('notifications/initialized', {}, true);
if (process.argv[2] === 'list') {
  const c = await rpc('tools/list', {});
  console.log(JSON.stringify(c.tools.map(t => ({name: t.name, description: t.description, schema: t.inputSchema}))));
  process.exit(0);
}
const MAX = +process.env.MAX || 20000;
for (const [name, args] of JSON.parse(process.argv[2] || '[]')) {
  const res = await rpc('tools/call', {name, arguments: args});
  (res.content || []).filter(c => c.type === 'image').forEach((c, i) => {
    const f = `${process.cwd()}/img_${name}_${Date.now()}_${i}.${(c.mimeType || 'image/png').split('/')[1]}`;
    fs.writeFileSync(f, Buffer.from(c.data, 'base64')); console.log('IMAGE ' + f);
  });
  const txt = (res.content || []).filter(c => c.type === 'text').map(c => c.text).join('\n');
  console.log(`### ${name} ${res.isError ? 'ERROR' : ''}\n${txt.slice(0, MAX)}`);
  if (res.isError) process.exit(1);
}
