# Gestionale Oculistico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire un prototipo HTML a file singolo che gestisce il flusso di uno studio oculistico (registrazione paziente su kiosk → conferma anagrafica medico → refertazione → consenso firmato → PDF), con board di lavoro multi-paziente.

**Architecture:** Singolo file `gestionale-oculista.html`. Tutta la logica in un `<script>` inline. Lo stato vive in `localStorage` dietro un modulo `db` (così il futuro passaggio a backend tocca solo `db`). Routing a viste via show/hide di sezioni. Ruolo corrente in `sessionStorage`. Nessun build step, nessuna dipendenza server; jsPDF caricato da CDN.

**Tech Stack:** HTML + CSS + JS vanilla (ES2020), `localStorage`/`sessionStorage`, Canvas API (firma con pointer events), jsPDF (CDN).

## Global Constraints

- File singolo: `oculista/gestionale-oculista.html`. Nessun file JS/CSS esterno (eccetto CDN jsPDF).
- Storage astratto dietro `db` — nessun accesso diretto a `localStorage` fuori dal modulo `db`.
- Chiave localStorage: `oculista_pazienti` (array di oggetti paziente nello schema dello spec).
- Verifica = comportamentale nel browser su `http://localhost:8080/gestionale-oculista.html` (server `static-oculista` già attivo). Non è un repo git: i passi "Checkpoint" sostituiscono i commit.
- Campi referto = identici a `app prova filippo/visita_oculistica_desktop.py`. Non aggiungere/togliere campi clinici.
- Stati paziente: `Registrato`, `In attesa`, `In corso`, `In stop`, `Refertato`, `Consenso firmato`, `Completato`.
- Ruoli demo: `rossi`/`demo`, `bianchi`/`demo` (oculisti), `paziente`/`demo` (kiosk). Nomi/credenziali sono placeholder.
- Lingua UI: italiano.
- **Stile UI = "Demo Laboratorio":** sidebar fissa a gruppi (drawer su iPad portrait) + vista dettaglio a card read-only con "Modifica" + timeline stato con storico `eventi[]` + barra azioni (PDF/Mail/Stop/Modifica). Token: card `#f5f5f7` r14px, testo `#1d1d1f`/`#6e6e73`, ambra `#fde68a`/`#92651a`, verde `#34c759`, rosso `#ff3b30`, bottoni outline `#d2d2d7` r10px. Badge stato: Registrato=grigio, In corso=verde, In stop=ambra, Refertato=blu, Consenso firmato=viola, Completato=verde pieno. Target touch ≥44px.
- Ogni transizione di stato fa append a `eventi[]` via `pushEvento(id, stato)`.

---

### Task 1: Scaffold, stile base, modulo `db`, schema paziente

**Files:**
- Create: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: niente.
- Produces:
  - `db.getPazienti() -> Array<Paziente>`
  - `db.getPaziente(id) -> Paziente | undefined`
  - `db.savePaziente(paziente) -> Paziente` (assegna `id` se mancante, setta `createdAt`/`updatedAt`, append all'array, persiste)
  - `db.updatePaziente(id, patch) -> Paziente` (merge superficiale per top-level + merge profondo per gli oggetti `anagrafica/motivo/anamnesi/referto`, aggiorna `updatedAt`)
  - `db.removeAll()` (helper per reset demo)
  - `nuovoPaziente() -> Paziente` factory che ritorna lo schema vuoto (vedi sotto)
  - `uuid() -> string`
  - costante `STATI = {REGISTRATO, IN_ATTESA, IN_CORSO, IN_STOP, REFERTATO, CONSENSO, COMPLETATO}` con i valori stringa esatti dello spec.

Schema (factory `nuovoPaziente()`):
```js
{
  id: uuid(), stato: STATI.REGISTRATO, medicoAssegnato: null,
  anagrafica: { nome:'', dataNascita:'', sesso:'', codiceFiscale:'', indirizzo:'', telefono:'', email:'' },
  motivo: { controllo:false, disturbi:'', prescrizione:false, altro:'' },
  anamnesi: { problemiOcchi:'No', qualiProblemi:'', portaOcchiali:'No', daQuanto:'', malattie:'', farmaci:'', interventi:'' },
  referto: { annessi:'', acuitaLontanoOD:'', acuitaLontanoOS:'', acuitaVicinoOD:'', acuitaVicinoOS:'',
             refOD:{sph:'',cyl:'',asse:''}, refOS:{sph:'',cyl:'',asse:''},
             pressioneOD:'', pressioneOS:'', fondo:'', altriEsami:'', diagnosi:'' },
  firmaConsenso: null, eventi:[], createdAt:null, updatedAt:null
}
```

Helper transizioni: `pushEvento(id, stato) -> Paziente` — fa `updatePaziente(id,{stato})` e append `{stato, ts:new Date().toISOString(), utente:sessionCorrente()?.user||'paziente'}` ad `eventi[]`. Tutte le transizioni di stato passano da qui.

- [ ] **Step 1: Creare il file con struttura base**

Creare `oculista/gestionale-oculista.html` con: doctype, `<meta viewport>` (kiosk iPad), `<title>Gestionale Oculistico</title>`, un `<style>` con i token dello stile "Demo Laboratorio": variabili CSS (`--card:#f5f5f7; --txt:#1d1d1f; --txt2:#6e6e73; --ambra:#fde68a; --ambra-txt:#92651a; --verde:#34c759; --rosso:#ff3b30; --bordo:#d2d2d7; --r:14px`), font `system-ui,-apple-system`; layout shell `display:grid; grid-template-columns:260px 1fr` (`#sidebar` + `#main`); `.view{display:none}` / `.view.active{display:block}`; classi base `.card`(bg var(--card), raggio var(--r), padding 20px), `.badge`(pillola), `.btn`(outline 1px var(--bordo), raggio 10px, min-height 44px), `.btn-danger`(rosso), `.timeline`/`.timeline .done`/`.timeline .current`; media query `max-width:820px` → sidebar a drawer (off-canvas) con bottone hamburger. Un `<div id="sidebar">` e `<div id="main">` dentro `<div id="app">`, e in fondo `<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>` seguito da `<script>` per il codice app.

- [ ] **Step 2: Implementare `uuid`, `STATI`, `nuovoPaziente`, modulo `db`**

Nel `<script>` app:
```js
const LS_KEY = 'oculista_pazienti';
const STATI = { REGISTRATO:'Registrato', IN_ATTESA:'In attesa', IN_CORSO:'In corso',
  IN_STOP:'In stop', REFERTATO:'Refertato', CONSENSO:'Consenso firmato', COMPLETATO:'Completato' };
function uuid(){ return 'p-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7); }
const db = {
  getPazienti(){ try { return JSON.parse(localStorage.getItem(LS_KEY)) || []; } catch { return []; } },
  _save(arr){ localStorage.setItem(LS_KEY, JSON.stringify(arr)); },
  getPaziente(id){ return this.getPazienti().find(p=>p.id===id); },
  savePaziente(p){ const arr=this.getPazienti(); if(!p.id) p.id=uuid();
    p.createdAt = p.createdAt || new Date().toISOString(); p.updatedAt = new Date().toISOString();
    arr.push(p); this._save(arr); return p; },
  updatePaziente(id, patch){ const arr=this.getPazienti(); const i=arr.findIndex(p=>p.id===id); if(i<0) return;
    const cur=arr[i];
    for(const k of ['anagrafica','motivo','anamnesi','referto']) if(patch[k]) patch[k]={...cur[k],...patch[k]};
    arr[i]={...cur,...patch,updatedAt:new Date().toISOString()}; this._save(arr); return arr[i]; },
  removeAll(){ localStorage.removeItem(LS_KEY); }
};
function nuovoPaziente(){ /* ritorna lo schema sopra con id/stato iniziali, eventi:[] */ }
function pushEvento(id, stato){ const p=db.getPaziente(id); if(!p) return;
  const ev={stato, ts:new Date().toISOString(), utente:(sessionCorrente&&sessionCorrente()?.user)||'paziente'};
  return db.updatePaziente(id,{stato, eventi:[...(p.eventi||[]), ev]}); }
```
Nota: `updatePaziente` fa merge profondo solo su `anagrafica/motivo/anamnesi/referto`; `eventi` è sostituito interamente (qui passiamo l'array già esteso).

- [ ] **Step 3: Verifica logica `db` (console asserzioni)**

Aprire `http://localhost:8080/gestionale-oculista.html`, in Console:
```js
db.removeAll();
const p = db.savePaziente(nuovoPaziente());
console.assert(db.getPazienti().length===1, 'save fallita');
db.updatePaziente(p.id,{stato:STATI.IN_CORSO, anagrafica:{nome:'Mario Rossi'}});
const q = db.getPaziente(p.id);
console.assert(q.stato==='In corso' && q.anagrafica.nome==='Mario Rossi' && q.anagrafica.email==='', 'update/merge fallita');
console.log('DB OK');
```
Expected: stampa `DB OK`, nessun assert fallito.

- [ ] **Step 4: Checkpoint**

Verificare che la pagina carichi senza errori in Console e che jsPDF sia disponibile (`window.jspdf` definito). Annotare il checkpoint.

---

### Task 2: Login e routing tra viste

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`.
- Produces:
  - `UTENTI = { rossi:{pass:'demo',ruolo:'medico',nome:'Dott. Rossi'}, bianchi:{...}, paziente:{pass:'demo',ruolo:'paziente',nome:'Paziente'} }`
  - `sessionCorrente() -> {user,ruolo,nome} | null` (legge `sessionStorage.oculista_user`)
  - `login(user,pass) -> bool`
  - `logout()`
  - `showView(id, ctx)` — nasconde tutte le `.view`, mostra `#view-<id>`, chiama il renderer associato con `ctx`.
  - `render()` — entry point: se non loggato mostra login; se medico → board; se paziente → registrazione.

- [ ] **Step 1: Markup login + shell sidebar (stile Demo Laboratorio)**

Aggiungere una `.view#view-login` (a tutto schermo, sidebar nascosta) con campi `user`/`pass`, bottone "Accedi" e area errore. Costruire la shell: `#sidebar` con gruppi nav (renderizzati per ruolo in `renderSidebar()`) + footer utente con nome e bottone "Esci"; `#main` con una topbar (breadcrumb placeholder) e i contenitori `.view`. `renderSidebar()` genera: medico → gruppi LAVORO (Board, In attesa), PAZIENTI (Lista, Nuovo), REFERTI (Da firmare); paziente → solo Registrazione + Firma consenso. Voci nav chiamano `showView(...)`. Su `max-width:820px` la sidebar è off-canvas con bottone hamburger nella topbar.

- [ ] **Step 2: Implementare `UTENTI`, `login`, `logout`, `sessionCorrente`, `showView`, `render`**

`login` valida contro `UTENTI`, su successo scrive `sessionStorage.oculista_user` (JSON con user/ruolo/nome) e chiama `render()`. `logout` rimuove la chiave e chiama `render()`. `showView(id)` toggla la classe `active`. `render()` instrada per ruolo (medico→`board`, paziente→`registrazione`). Collegare submit del form login.

- [ ] **Step 3: Verifica login/instradamento**

Su :8080: login `paziente`/`demo` → compare la vista registrazione (placeholder ok in questo task); "Esci" → torna al login; login `rossi`/`demo` → compare la vista board (placeholder ok); credenziali errate → messaggio errore, nessun cambio vista. Ricaricare la pagina da loggato → resta loggato (sessionStorage).

- [ ] **Step 4: Checkpoint**

Nessun errore Console nei tre flussi. Annotare checkpoint.

---

### Task 3: Form anagrafica riusabile (registrazione paziente + conferma medico)

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, `nuovoPaziente`, `showView`, `sessionCorrente`.
- Produces:
  - `renderAnagrafica(container, {paziente, editable, onSubmit, submitLabel})` — costruisce il form (Dati paziente + Motivo visita + Anamnesi) popolato da `paziente`; se `editable===false` i campi sono `disabled`; al submit raccoglie i valori in un oggetto `{anagrafica,motivo,anamnesi}` e chiama `onSubmit(dati)`.
  - `leggiAnagraficaDalForm(container) -> {anagrafica,motivo,anamnesi}`
  - Vista paziente `#view-registrazione`: nuovo paziente, `editable:true`, submit → `db.savePaziente({...nuovo, ...dati, stato:STATI.REGISTRATO})` poi schermata "Registrazione inviata" con bottone "Nuova registrazione".

**Campi (esatti, dal .py):** Nome e Cognome, Data di nascita (DD/MM/YYYY), Sesso (radio M/F), Codice Fiscale, Indirizzo, Telefono, Email. Motivo (checkbox): Visita di controllo; Disturbi visivi (+input testo); Prescrizione occhiali/lenti; Altro (+input testo). Anamnesi: problemi agli occhi (radio Sì/No) + "quali"; porta occhiali/lenti (radio Sì/No) + "da quanto"; Malattie sistemiche; Farmaci assunti; Interventi oculari pregressi.

- [ ] **Step 1: Implementare `renderAnagrafica` + `leggiAnagraficaDalForm`**

Generare il markup dei campi sopra (usare `name` coerenti con lo schema, es. `data-field="anagrafica.nome"`). Popolare i valori da `paziente`. Applicare `disabled` se `!editable`. `leggiAnagraficaDalForm` ricostruisce `{anagrafica,motivo,anamnesi}` leggendo i `data-field`.

- [ ] **Step 2: Cablare la vista registrazione paziente**

In `render()` per ruolo paziente: `renderAnagrafica(#view-registrazione, {paziente:nuovoPaziente(), editable:true, submitLabel:'Invia registrazione', onSubmit})`. `onSubmit` valida (Nome e Data nascita obbligatori, come il .py), salva con stato `Registrato`, mostra conferma.

- [ ] **Step 3: Verifica registrazione**

Login `paziente` → compilare Nome="Anna Verdi", Data nascita, spuntare "Disturbi visivi" + testo → Invia. Submit senza Nome → messaggio errore. In Console: `db.getPazienti()` mostra il paziente con `stato:'Registrato'`, `motivo.disturbi` valorizzato.

- [ ] **Step 4: Checkpoint**

Annotare checkpoint.

---

### Task 4: Board lavoro + transizioni di stato (In corso ⇄ In stop)

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, `sessionCorrente`, `showView`, `renderAnagrafica`.
- Produces:
  - `renderBoard(container)` — tre gruppi: **In attesa** (stato `Registrato`/`In attesa`, non assegnati o assegnati a me), **In corso**, **In stop** (assegnati a me). Ogni card/riga mostra nome + badge stato; click sulla riga → `renderDettaglio(#main, id)` (Task 8).
  - `prendiInCarico(id)` → `updatePaziente(id,{medicoAssegnato:userCorrente})` poi `pushEvento(id, IN_CORSO)` e apre il dettaglio.
  - `setStato(id, stato)` → `pushEvento(id, stato)` + ri-render della vista attiva.
  - bottoni: "Prendi in carico" (da In attesa), "In stop"⇄"Riprendi" (toggle In corso/In stop via `setStato`). Le azioni Conferma/Referto/PDF vivono nella vista dettaglio (Task 8).

- [ ] **Step 1: Implementare `renderBoard` con i tre gruppi**

Raggruppare `db.getPazienti()` per stato; filtrare per `medicoAssegnato` dell'utente corrente (In attesa include i non assegnati). Renderizzare card con badge stato.

- [ ] **Step 2: Implementare transizioni e bottoni**

`prendiInCarico`, toggle `In corso`⇄`In stop` via `setStato` (entrambi via `pushEvento`). Click sulla riga apre il dettaglio (Task 8). Dopo ogni transizione ri-renderizzare la board.

- [ ] **Step 3: Verifica board multi-paziente**

Reset (`db.removeAll()`), creare 3 pazienti via vista paziente (Anna, Bruno, Carla). Login `rossi`: tutti in "In attesa". Prendi in carico Anna → In corso. Prendi Bruno → In corso. Metti Anna "In stop". Risultato atteso: Bruno In corso, Anna In stop, Carla In attesa — esattamente lo scenario dello spec. Login `bianchi`: non vede i pazienti assegnati a rossi (vede solo In attesa non assegnati, es. Carla).

- [ ] **Step 4: Checkpoint**

Annotare checkpoint.

---

### Task 5: Refertazione (esame obiettivo + diagnosi)

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, `showView`, `renderBoard`.
- Produces:
  - `renderReferto(container, id)` — form coi campi referto del .py, popolato da `db.getPaziente(id).referto`.
  - `leggiRefertoDalForm(container) -> referto` (include `refOD/refOS` annidati).
  - submit → `updatePaziente(id,{referto})` poi `pushEvento(id, STATI.REFERTATO)` → torna al dettaglio.

**Campi (esatti, dal .py):** Esame annessi e segmento anteriore (textarea); Acuità visiva lontano OD; lontano OS; vicino OD; vicino OS; Refrazione OD (Sph/Cyl/Asse); Refrazione OS (Sph/Cyl/Asse); Pressione intraoculare OD (mmHg); OS (mmHg); Esame fondo oculare (textarea); Altri esami (textarea); Diagnosi e prescrizione (textarea).

- [ ] **Step 1: Implementare `renderReferto` + `leggiRefertoDalForm`**

Markup dei campi sopra con `data-field` (es. `referto.refOD.sph`). Popolare da paziente esistente.

- [ ] **Step 2: Cablare apertura dalla board e submit**

Bottone "Referto" sulla card (stati In corso/In stop) apre `renderReferto`. Submit salva referto e setta stato `Refertato`, poi `renderBoard`.

- [ ] **Step 3: Verifica refertazione**

Aprire referto di Anna, compilare Acuità lontano OD="10/10", Refrazione OD Sph="-1.50" Cyl="-0.50" Asse="90", Diagnosi="Miopia lieve" → Salva. In Console: `db.getPaziente(<id>).referto.refOD` = `{sph:'-1.50',cyl:'-0.50',asse:'90'}`, `stato:'Refertato'`. La card di Anna ora mostra "Refertato" e i bottoni "Genera PDF".

- [ ] **Step 4: Checkpoint**

Annotare checkpoint.

---

### Task 6: Modulo consenso trattamento dati + firma su canvas

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, `showView`, `render`.
- Produces:
  - `renderConsenso(container, id)` — testo GDPR placeholder + `<canvas>` firma + bottoni "Cancella firma" e "Conferma e firma".
  - `initFirmaCanvas(canvas) -> { toDataURL(), isEmpty(), clear() }` — disegno con pointer events (penna/dito/mouse).
  - "Conferma" (solo se firma non vuota) → `updatePaziente(id,{firmaConsenso:dataURL})` poi `pushEvento(id, STATI.CONSENSO)`.
  - Accesso paziente al consenso: dopo refertazione, il paziente (kiosk) apre il proprio modulo. Per la prova: nella vista paziente aggiungere selezione del proprio nominativo tra i pazienti in stato `Refertato` per aprire il consenso.

- [ ] **Step 1: Implementare `initFirmaCanvas` (pointer events)**

```js
function initFirmaCanvas(canvas){
  const ctx=canvas.getContext('2d'); let drawing=false, dirty=false;
  ctx.lineWidth=2; ctx.lineCap='round'; ctx.strokeStyle='#111';
  const pos=e=>{const r=canvas.getBoundingClientRect(); return [e.clientX-r.left, e.clientY-r.top];};
  canvas.addEventListener('pointerdown',e=>{drawing=true;dirty=true;const[x,y]=pos(e);ctx.beginPath();ctx.moveTo(x,y);canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drawing)return;const[x,y]=pos(e);ctx.lineTo(x,y);ctx.stroke();});
  canvas.addEventListener('pointerup',()=>drawing=false);
  return { toDataURL:()=>canvas.toDataURL('image/png'), isEmpty:()=>!dirty,
           clear:()=>{ctx.clearRect(0,0,canvas.width,canvas.height);dirty=false;} };
}
```
Impostare `touch-action:none` sul canvas via CSS (necessario per Apple Pencil/touch).

- [ ] **Step 2: Implementare `renderConsenso` + accesso paziente**

Testo placeholder GDPR + canvas (es. 600×200) + bottoni. "Conferma e firma" disabilitato finché `isEmpty()`. Nella vista paziente aggiungere lista dei pazienti `Refertato` per selezionare il proprio e aprire il consenso.

- [ ] **Step 3: Verifica firma**

Login `paziente`, selezionare Anna (Refertato), disegnare una firma nel canvas col mouse → "Conferma e firma" si abilita → conferma. In Console: `db.getPaziente(<id>).firmaConsenso` inizia con `data:image/png;base64,`, `stato:'Consenso firmato'`. "Cancella firma" svuota il canvas e ridisabilita il bottone.

- [ ] **Step 4: Checkpoint**

Annotare checkpoint.

---

### Task 7: Generazione PDF (referto + firma) e chiusura flusso

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, jsPDF (`window.jspdf.jsPDF`).
- Produces:
  - `generaPDF(id)` — costruisce il PDF con le stesse sezioni del `.py` (DATI DEL PAZIENTE, MOTIVO DELLA VISITA, ANAMNESI OCULARE E GENERALE, ESAME OBIETTIVO OCULARE, DIAGNOSI E PRESCRIZIONE) + immagine firma se presente; `doc.save('<Nome>_<YYYY-MM-DD>.pdf')`.
  - bottone board "Genera PDF" (stati `Refertato`/`Consenso firmato`/`Completato`) → `generaPDF(id)`; opzionale "Completa" → stato `Completato`.

- [ ] **Step 1: Implementare `generaPDF` con jsPDF**

```js
function generaPDF(id){
  const p=db.getPaziente(id); const { jsPDF }=window.jspdf; const doc=new jsPDF();
  let y=15; const line=(t,b=false,size=11)=>{ doc.setFont('helvetica',b?'bold':'normal'); doc.setFontSize(size);
    for(const ln of doc.splitTextToSize(t,180)){ if(y>275){doc.addPage();y=15;} doc.text(ln,15,y); y+=6; } };
  line('Modulo Visita Oculistica', true, 16); y+=2;
  line('DATI DEL PAZIENTE', true);
  const a=p.anagrafica; ['Nome e Cognome: '+a.nome,'Data di nascita: '+a.dataNascita,'Sesso: '+a.sesso,
    'Codice Fiscale: '+a.codiceFiscale,'Indirizzo: '+a.indirizzo,'Telefono: '+a.telefono,'Email: '+a.email].forEach(t=>line(t));
  // ...stesse sezioni MOTIVO / ANAMNESI / ESAME OBIETTIVO (refOD/refOS, pressione, fondo, altri) / DIAGNOSI come nel .py...
  if(p.firmaConsenso){ y+=4; line('Firma consenso trattamento dati:', true); if(y>240){doc.addPage();y=15;} doc.addImage(p.firmaConsenso,'PNG',15,y,80,30); }
  doc.save((a.nome||'paziente').replace(/\s+/g,'_')+'_'+new Date().toISOString().slice(0,10)+'.pdf');
}
```
Replicare per esteso le sezioni MOTIVO/ANAMNESI/ESAME/DIAGNOSI con le stesse etichette e l'ordine del `.py` (vedi `genera_pdf()` righe 234-270).

- [ ] **Step 2: Cablare bottone board + "Completa"**

Nella barra azioni del dettaglio (Task 8), in stato `Refertato`/`Consenso firmato`: bottone "Genera PDF" → `generaPDF(id)`; bottone "Completa" → `setStato(id, STATI.COMPLETATO)`.

- [ ] **Step 3: Verifica PDF**

Su Anna (con referto + firma): "Genera PDF" → scarica un `.pdf` con tutte le sezioni compilate e l'immagine della firma in fondo. Aprire il PDF e verificare ordine sezioni e firma presente.

- [ ] **Step 4: Checkpoint finale**

Eseguire il flusso end-to-end completo (registrazione → board → conferma → referto → consenso/firma → PDF → Completa) su un nuovo paziente, su entrambi i medici. Nessun errore Console. Annotare checkpoint.

---

### Task 8: Vista dettaglio paziente (card read-only + timeline stato)

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, `renderAnagrafica`, `renderReferto`, `renderConsenso`, `generaPDF`, `setStato`, `sessionCorrente`.
- Produces:
  - `renderDettaglio(container, id)` — vista a card in **sola lettura** dello stile "Demo Laboratorio": header con `# <id>` + breadcrumb `home / pazienti / <nome>` + `badgeStato(stato)`; card riepilogo (nome, data nascita, CF, medico assegnato); card Anagrafica; card Motivo/Anamnesi; card Referto (se compilato); card Consenso (mostra l'immagine firma se presente); poi `renderTimeline` e la barra azioni.
  - `badgeStato(stato) -> htmlString` — pillola con colore per stato (mappa colori dei Global Constraints).
  - `renderTimeline(eventi) -> htmlString` — lista nodi: eventi passati con check verde, ultimo evento (stato corrente) nodo ambra, ciascuno con `ts` formattato + `utente`.
  - Barra azioni contestuale per stato: `Modifica` (apre `renderAnagrafica` editable), `Referto` (apre `renderReferto`, se In corso/In stop), `Genera PDF` (se Refertato+), `In stop`⇄`Riprendi`, `Completa` (se Consenso firmato).

- [ ] **Step 1: Implementare `badgeStato` e `renderTimeline`**

`badgeStato` ritorna `<span class="badge" style="...">` con bg/testo per stato (Registrato grigio, In corso verde, In stop ambra, Refertato blu, Consenso firmato viola, Completato verde). `renderTimeline` itera `eventi`: classe `done` per tutti tranne l'ultimo che è `current` (ambra), mostra `new Date(ev.ts).toLocaleString('it-IT')` + `ev.utente`.

- [ ] **Step 2: Implementare `renderDettaglio` + barra azioni**

Comporre le card read-only (valori da `db.getPaziente(id)`) seguendo i token CSS del Task 1. La barra azioni mostra solo i bottoni pertinenti allo stato corrente e cabla le funzioni dei Task 3/5/6/7. Click voce board → `renderDettaglio`.

- [ ] **Step 3: Verifica dettaglio + timeline**

Aprire il dettaglio di Anna (post-referto e firma). Atteso: header con badge "Consenso firmato" (viola), card riepilogo/anagrafica/referto popolate, card consenso con immagine firma, timeline con nodi Registrato→In corso→Refertato→Consenso firmato (date+utente, ultimo nodo ambra), barra con "Genera PDF" e "Completa". "Modifica" apre anagrafica editabile; salvataggio torna al dettaglio aggiornato.

- [ ] **Step 4: Checkpoint**

Annotare checkpoint.

---

### Task 9: Cronometro pazienti in stop (tempo in pausa)

**Files:**
- Modify: `oculista/gestionale-oculista.html`

**Interfaces:**
- Consumes: `db`, `STATI`, `eventi[]` (già popolato da `pushEvento`), `renderBoard`, `renderDettaglio` (Task 8), `showView`.
- Produces:
  - `inizioStop(p) -> ISO|null` — ritorna il `ts` dell'ULTIMO evento con `stato === STATI.IN_STOP` in `p.eventi` (null se non in stop o nessun evento).
  - `formatDurata(ms) -> string` — `"Hh Mm"` se ≥1h, altrimenti `"Mm Ss"` (zero-pad sec). Es. `"7m 03s"`, `"1h 12m"`.
  - `avviaCronometri()` / `fermaCronometri()` — un singolo `setInterval(…,1000)` che ad ogni tick aggiorna il testo di tutti gli elementi `[data-stop-since]` con `formatDurata(now - ts)`. `fermaCronometri` fa `clearInterval` e azzera l'id. Evita interval multipli (idempotente).
- Le righe board "In stop" e la card dettaglio in stop renderizzano `<span class="crono" data-stop-since="<ISO>">…</span>` con etichetta "In pausa da ". `showView` chiama `fermaCronometri()` all'uscita e `renderBoard`/`renderDettaglio` chiamano `avviaCronometri()` dopo aver disegnato (solo se ci sono elementi `[data-stop-since]`).

- [ ] **Step 1: Implementare `inizioStop`, `formatDurata`, `avviaCronometri`/`fermaCronometri`**

`inizioStop`: itera `p.eventi` dal fondo, ritorna il primo `ts` con `stato===STATI.IN_STOP`. `formatDurata`: da ms a stringa. `avviaCronometri`: se `cronoInterval` già attivo, return; altrimenti `cronoInterval=setInterval(tick,1000)` dove `tick` fa `document.querySelectorAll('[data-stop-since]').forEach(el=>el.textContent=formatDurata(Date.now()-Date.parse(el.dataset.stopSince)))` e chiama subito `tick()` una volta. `fermaCronometri`: `clearInterval(cronoInterval); cronoInterval=null;`.

- [ ] **Step 2: Integrare nelle viste**

In `renderBoard` (riga gruppo "In stop") e in `renderDettaglio` (card stato, se `stato===IN_STOP`): aggiungere `In pausa da <span class="crono" data-stop-since="${inizioStop(p)}"></span>`. Dopo il render, se esiste almeno un `[data-stop-since]`, chiamare `avviaCronometri()`. In `showView` chiamare `fermaCronometri()` prima di cambiare vista (evita interval orfani). Stile `.crono`: riusa token (monospace opzionale, `var(--ambra-txt)`).

- [ ] **Step 3: Verifica cronometro**

Su :8080: metti Anna "In stop", apri la board → compare "In pausa da 0m 0Xs" che incrementa ogni secondo. `preview_eval`: `inizioStop(db.getPaziente('<id>'))` ritorna l'ISO dell'ultimo evento In stop; `formatDurata(3723000)==='1h 02m'`. Cambia vista e torna → un solo interval attivo (nessun raddoppio di velocità). Riprendi Anna (In corso) → il cronometro sparisce.

- [ ] **Step 4: Checkpoint**

Annotare checkpoint.

---

## Allineamento referto esteso (delta `.py` aggiornata)

La `.py` di riferimento è stata estesa. Allineare **SOLO i campi variati**, modifica chirurgica, senza toccare i campi esistenti che non cambiano.

**Delta campi:**
- Anagrafica: `nome` → split in `cognome` + `nome`; nuovo `comuneNascita`; validazione Codice Fiscale.
- Clinica (lato medico): nuovi `apo` (Anamnesi Patologica Oculare), `apg` (Anamnesi Patologica Generale).
- Esame obiettivo: nuovi `visusOD`/`visusOS`, `tonoOD`/`tonoOS`; `fondo` sostituito da `fundusOD`/`fundusOS`.

**Posizionamento:** APO/APG sono anamnesi clinica → vanno nel form REFERTAZIONE (medico), non nella registrazione self-service del paziente. Visus/Tono/Fundus → referto. Cognome/Comune nascita → anagrafica.

### Task 10: Anagrafica — split Cognome/Nome + Comune nascita + validazione CF

**Files:** Modify `oculista/gestionale-oculista.html`

**Interfaces:**
- Schema `anagrafica`: aggiungere `cognome:''` e `comuneNascita:''` (mantenere `nome`). Aggiornare `nuovoPaziente()`.
- `renderAnagrafica`/`leggiAnagraficaDalForm`: aggiungere campo **Cognome** (prima di Nome) e **Comune di nascita** (dopo Codice Fiscale). `data-field="anagrafica.cognome"`, `anagrafica.comuneNascita`.
- `nomeCompleto(p) -> string` → `"<cognome> <nome>"` (trim). Sostituire gli usi di `p.anagrafica.nome` per la visualizzazione del nominativo in board/PDF/liste con `nomeCompleto(p)` (SOLO display; non rinominare la chiave `nome`).
- `validaCodiceFiscale(anagrafica) -> {ok:boolean, atteso?:string, msg?:string}` — algoritmo CF italiano in JS: calcola codice cognome (consonanti/vocali), codice nome, codice data+sesso (anno 2 cifre, mese lettera, giorno +40 se F), e **carattere di controllo** (checksum). Confronta i 15 char calcolabili + checksum col CF inserito. **Il codice Belfiore del comune (4 char, pos. 12-15) NON è cross-validato** (richiederebbe la tabella catastale ~8000 comuni, fuori scope per il prototipo single-file): si verifica formato+checksum+cognome+nome+data+sesso. Validazione attiva al submit registrazione: obbligatori Cognome, Nome, Data nascita; se CF compilato → verifica e blocca con messaggio se incoerente.

- [ ] **Step 1:** Aggiungere `cognome`/`comuneNascita` a `nuovoPaziente().anagrafica`. Implementare `nomeCompleto` e `validaCodiceFiscale` (con tabella mesi `ABCDEHLMPRST`, set vocali, funzione checksum con le tabelle pari/dispari standard).
- [ ] **Step 2:** Aggiungere i due campi in `renderAnagrafica` (Cognome prima di Nome; Comune di nascita dopo CF) e in `leggiAnagraficaDalForm`. Sostituire i display del nominativo con `nomeCompleto`. Cablare `validaCodiceFiscale` nella validazione submit della registrazione.
- [ ] **Step 3: Verifica browser** — registra "Rossi"/"Mario", data, sesso M, CF coerente → passa; CF errato → messaggio "non corrisponde"; CF vuoto → consentito. `preview_eval`: `nomeCompleto(p)==='Rossi Mario'`; `validaCodiceFiscale` ritorna `ok:false` su CF con checksum errato.
- [ ] **Step 4: Checkpoint.**

### Task 11: Referto — Visus/Tono/Fundus + APO/APG

**Files:** Modify `oculista/gestionale-oculista.html`

**Interfaces:**
- Schema `referto`: aggiungere `apo:''`, `apg:''`, `visusOD:''`, `visusOS:''`, `tonoOD:''`, `tonoOS:''`, `fundusOD:''`, `fundusOS:''`; **rimuovere `fondo`** (sostituito da fundusOD/OS). Aggiornare `nuovoPaziente()`.
- `renderReferto`/`leggiRefertoDalForm`: aggiungere — in testa "ANAMNESI CLINICA": APO (textarea), APG (textarea); in ESAME: Visus OD/OS (dopo annessi, prima dell'acuità), Tono OD/OS (mmHg, vicino a Pressione), Fundus OD/OS (textarea, al posto di Fondo). `data-field` `referto.apo` ecc.
- Mantenere INTATTI i campi referto esistenti non variati (annessi, acuità lontano/vicino, refOD/refOS, pressioneOD/OS, altriEsami, diagnosi).

- [ ] **Step 1:** Aggiornare schema `referto` in `nuovoPaziente()` (aggiungere gli 8 campi, rimuovere `fondo`).
- [ ] **Step 2:** Aggiungere i campi in `renderReferto` e `leggiRefertoDalForm` nelle posizioni indicate; sostituire il blocco "Fondo Oculare" con Fundus OD/OS.
- [ ] **Step 3: Verifica browser** — compila Visus OD="10/10", Tono OD="15", Fundus OD="nella norma", APO="-" → salva → `preview_eval` conferma i campi salvati in `db.getPaziente(id).referto` e assenza di `fondo`.
- [ ] **Step 4: Checkpoint.**

### Task 12: PDF — sincronizzare i campi nuovi (ordine `.py`)

**Files:** Modify `oculista/gestionale-oculista.html`

**Interfaces:**
- `generaPDF(id)`: allineare 1:1 alla `genera_pdf()` nuova — DATI PAZIENTE: `Cognome:` + `Nome:` separati, `Comune di nascita:` dopo Sesso; ANAMNESI: aggiungere righe APO/APG (ora con dati reali dallo schema); ESAME OBIETTIVO: Visus OD/OS, Tono OD/OS, Fundus OD/OS (al posto di "Esame del Fondo Oculare"). Mantenere ordine e le righe esistenti non variate.

- [ ] **Step 1:** Aggiornare le sezioni di `generaPDF` per i soli campi variati (Cognome/Nome/Comune, APO/APG, Visus/Tono/Fundus OD/OS), usando `nomeCompleto` per il filename.
- [ ] **Step 2: Verifica browser** — `generaPDF` su paziente completo produce PDF con i nuovi campi popolati, niente `fondo`, niente righe vuote.
- [ ] **Step 3: Checkpoint.**

---

## Self-Review

- **Spec coverage:** Architettura/db+eventi (T1), login+ruoli+shell sidebar (T2), registrazione anagrafica + conferma medico (T3), stati+board In corso⇄In stop (T4), refertazione (T5), consenso+firma (T6), PDF con firma (T7), vista dettaglio a card + timeline stato — stile Demo Laboratorio (T8). Tutte le sezioni dello spec (incl. UI/UX) coperte.
- **Placeholder scan:** I "placeholder" residui (testo GDPR, nomi/credenziali, intestazione studio) sono dichiarati fuori scope nello spec e marcati come tali, non sono lacune del piano. Le sezioni PDF MOTIVO/ANAMNESI/ESAME sono indicate da replicare 1:1 dal `.py` (righe 234-270) per non duplicare ~40 righe qui.
- **Type consistency:** `db.getPaziente/getPazienti/savePaziente/updatePaziente/removeAll`, `pushEvento(id,stato)`, `STATI.*`, `renderSidebar/renderDettaglio/renderTimeline/badgeStato`, `data-field` annidati (`referto.refOD.sph`), `initFirmaCanvas().toDataURL/isEmpty/clear`, `generaPDF(id)` — nomi coerenti tra i task. Le transizioni di stato passano tutte da `pushEvento` (no `updatePaziente({stato})` diretto).
