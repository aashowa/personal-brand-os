// Apply privacy-mask ops in ONE Palmier session (many short sessions bloat Palmier's chat panel and stall it).
// usage: node masks_apply.mjs "<project name>" <timelineId> ops.json
//   ops.json from `privacy_scan.py --ops`: [["delete", clipId, maskId] | ["create", clipId, [x0, y0, x1, y1]]] (source coords)
// Creates rectangle masks named "privacy blur" (feather 8) with blur.gaussian radius 40. Prints progress every 100 ops.
// env: PALMIER_MCP (default http://127.0.0.1:19789/mcp). Stops at the first error: re-read the timeline before retrying.
import fs from 'node:fs';
const endpoint = process.env.PALMIER_MCP || 'http://127.0.0.1:19789/mcp';
const headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'};
let nextId = 1;
async function rpc(method, params, notification = false) {
  const body = {jsonrpc: '2.0', method, params}; if (!notification) body.id = nextId++;
  const r = await fetch(endpoint, {method: 'POST', headers, body: JSON.stringify(body), signal: AbortSignal.timeout(600000)});
  const s = r.headers.get('mcp-session-id'); if (s) headers['Mcp-Session-Id'] = s;
  const raw = await r.text(); if (notification) return;
  const msgs = raw.split(/\r?\n\r?\n/).map(b => b.split(/\r?\n/).filter(l => l.startsWith('data:')).map(l => l.slice(5).trimStart()).join('\n')).filter(Boolean).map(x => JSON.parse(x));
  const out = msgs.find(m => m.id === body.id);
  if (!out || out.error || out.result.isError) throw Error(JSON.stringify(out?.error || out?.result.content || raw.slice(0, 300)));
  return (out.result.content || []).filter(c => c.type === 'text').map(c => c.text).join('');
}
const call = (name, args) => rpc('tools/call', {name, arguments: args});
const [project, timelineId, opsFile] = process.argv.slice(2);
await rpc('initialize', {protocolVersion: '2024-11-05', capabilities: {}, clientInfo: {name: 'masks-apply', version: '1'}});
await rpc('notifications/initialized', {}, true);
await call('manage_project', {action: 'open', name: project});
await call('set_active_timeline', {timelineId});
let n = 0;
for (const [op, clipId, x] of JSON.parse(fs.readFileSync(opsFile))) {
  if (op === 'delete') await call('manage_masks', {action: 'delete', clipId, maskId: x});
  else {
    const res = JSON.parse(await call('manage_masks', {action: 'create', clipId, type: 'rectangle', name: 'privacy blur', feather: 8,
      geometry: {centerX: (x[0] + x[2]) / 2, centerY: (x[1] + x[3]) / 2, width: x[2] - x[0], height: x[3] - x[1], rotation: 0}}));
    await call('apply_effect', {maskTargets: [{clipId, maskId: res.created.maskId}], effects: [{type: 'blur.gaussian', params: {radius: 40}}]});
  }
  if (++n % 100 === 0) console.log('ok', n);
}
console.log('done', n);
