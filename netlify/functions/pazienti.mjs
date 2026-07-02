// API pazienti — storage condiviso su Netlify Blobs (un blob per paziente).
// GET  /api/pazienti[?since=ISO]  → elenco pazienti (solo aggiornati dopo `since`, se dato)
// POST /api/pazienti              → upsert di un paziente {id,...} o di un array di pazienti
// DELETE /api/pazienti?id=<id|*>  → elimina un paziente (o tutti con id=*)
import { getStore } from '@netlify/blobs';

const PREFIX = 'paz/';

export default async (req) => {
  const store = getStore({ name: 'oculista', consistency: 'strong' });
  const url = new URL(req.url);

  if (req.method === 'GET') {
    const since = url.searchParams.get('since');
    const sinceTs = since ? Date.parse(since) : null;
    const { blobs } = await store.list({ prefix: PREFIX });
    const items = await Promise.all(blobs.map(b => store.get(b.key, { type: 'json' })));
    const out = items.filter(p =>
      p && p.id && (!sinceTs || Date.parse(p.updatedAt || 0) > sinceTs)
    );
    return Response.json(out);
  }

  if (req.method === 'POST' || req.method === 'PUT') {
    let body;
    try { body = await req.json(); } catch { return new Response('JSON non valido', { status: 400 }); }
    const lista = Array.isArray(body) ? body : [body];
    const validi = lista.filter(p => p && typeof p.id === 'string' && p.id.length < 100);
    if (!validi.length) return new Response('id mancante', { status: 400 });
    await Promise.all(validi.map(p => store.setJSON(PREFIX + p.id, p)));
    return Response.json({ ok: true, salvati: validi.length });
  }

  if (req.method === 'DELETE') {
    const id = url.searchParams.get('id');
    if (!id) return new Response('id mancante', { status: 400 });
    if (id === '*') {
      const { blobs } = await store.list({ prefix: PREFIX });
      await Promise.all(blobs.map(b => store.delete(b.key)));
      return Response.json({ ok: true, eliminati: blobs.length });
    }
    await store.delete(PREFIX + id);
    return Response.json({ ok: true });
  }

  return new Response('Metodo non consentito', { status: 405 });
};

export const config = { path: '/api/pazienti' };
