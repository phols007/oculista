// API pazienti per Cloudflare Pages Functions — stesso contratto della
// Netlify Function (netlify/functions/pazienti.mjs), storage su KV.
// Richiede un binding KV chiamato PAZIENTI_KV (Pages → Settings → Bindings).
// Senza binding risponde 501 e l'app degrada in modalità solo-locale.
//
// GET  /api/pazienti[?since=ISO]  → elenco pazienti (delta se `since` è dato)
// POST /api/pazienti              → upsert di un paziente {id,...} o di un array
// DELETE /api/pazienti?id=<id|*>  → elimina un paziente (o tutti con id=*)

const PREFIX = 'paz/';

export async function onRequest(context) {
  const { request, env } = context;
  const kv = env.PAZIENTI_KV;
  if (!kv) {
    return new Response('Storage non configurato: aggiungi il binding KV "PAZIENTI_KV" al progetto Pages.', { status: 501 });
  }
  const url = new URL(request.url);

  if (request.method === 'GET') {
    const since = url.searchParams.get('since');
    const sinceTs = since ? Date.parse(since) : null;
    const list = await kv.list({ prefix: PREFIX });
    const items = await Promise.all(list.keys.map(k => kv.get(k.name, 'json')));
    const out = items.filter(p =>
      p && p.id && (!sinceTs || Date.parse(p.updatedAt || 0) > sinceTs)
    );
    return Response.json(out);
  }

  if (request.method === 'POST' || request.method === 'PUT') {
    let body;
    try { body = await request.json(); } catch { return new Response('JSON non valido', { status: 400 }); }
    const lista = Array.isArray(body) ? body : [body];
    const validi = lista.filter(p => p && typeof p.id === 'string' && p.id.length < 100);
    if (!validi.length) return new Response('id mancante', { status: 400 });
    await Promise.all(validi.map(p => kv.put(PREFIX + p.id, JSON.stringify(p))));
    return Response.json({ ok: true, salvati: validi.length });
  }

  if (request.method === 'DELETE') {
    const id = url.searchParams.get('id');
    if (!id) return new Response('id mancante', { status: 400 });
    if (id === '*') {
      const list = await kv.list({ prefix: PREFIX });
      await Promise.all(list.keys.map(k => kv.delete(k.name)));
      return Response.json({ ok: true, eliminati: list.keys.length });
    }
    await kv.delete(PREFIX + id);
    return Response.json({ ok: true });
  }

  return new Response('Metodo non consentito', { status: 405 });
}
