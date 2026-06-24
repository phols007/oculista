# Gestionale Oculistico — Design (prototipo HTML)

**Data:** 2026-06-24
**Stato:** in attesa di revisione utente

## Obiettivo

Mini gestionale per uno studio oculistico con due medici. Prototipo in un singolo file HTML che simula in tutto e per tutto il comportamento del gestionale online finale. Quando andrà online si sostituirà solo lo strato di storage (da `localStorage` a backend); UI e logica restano identiche.

Riferimento clinico autoritativo per i campi del referto: `app prova filippo/visita_oculistica_desktop.py` (app desktop Tkinter esistente). Tutti i campi del referto sono presi da lì.

## Architettura

- **Singolo file:** `oculista/gestionale-oculista.html` (stessa filosofia degli altri gestionali della cartella `html/`).
- **Storage:** `localStorage`, chiave unica con un array `pazienti[]`. Funge da "database online condiviso": tutti i ruoli leggono/scrivono lo stesso store. Astratto dietro un piccolo modulo `db` (getPazienti / savePaziente / updatePaziente) così che il passaggio a backend tocchi solo quel modulo.
- **Nessuna dipendenza server** per la prova. Si apre il file nel browser (o via `static-oculista` su :8080).
- **PDF:** jsPDF via CDN (genera un file scaricabile lato client, include l'immagine della firma). *Default modificabile.*

## Ruoli e login

Schermata di login iniziale. Tre utenze demo hardcoded (credenziali placeholder, da sostituire):

| Ruolo | Login demo | Cosa vede |
|-------|-----------|-----------|
| Dott. Rossi (Oculista 1) | `rossi` / `demo` | Board lavoro, conferma anagrafica, refertazione, genera PDF |
| Dott. Bianchi (Oculista 2) | `bianchi` / `demo` | Idem (i propri pazienti) |
| Paziente (kiosk iPad) | `paziente` / `demo` | Solo registrazione anagrafica + modulo consenso/firma |

I nomi "Rossi / Bianchi" e le credenziali sono placeholder, da sostituire con i dati reali.

## Stati del paziente (macchina a stati → board lavoro)

```
Registrato → In attesa → [In corso ⇄ In stop] → Refertato → Consenso firmato → Completato
```

- **Registrato:** paziente ha inviato l'anagrafica dal kiosk.
- **In attesa:** in coda, nessun medico l'ha ancora preso in carico.
- **In corso / In stop:** stato di lavoro del medico. Più pazienti possono essere contemporaneamente "in corso" o "in stop". Toggle per spostare un paziente tra i due (es: messo il collirio → In stop; entra un altro → In corso). Il paziente viene assegnato al medico che lo prende in carico.
- **Refertato:** medico ha completato e salvato il referto.
- **Consenso firmato:** paziente ha firmato il modulo trattamento dati.
- **Completato:** flusso concluso, referto + consenso archiviati.

**Board lavoro (vista medico):** tabella/colonne con i pazienti raggruppati per stato (In corso / In stop / In attesa), con pulsanti per cambiare stato e aprire conferma anagrafica o refertazione.

## Moduli

### 1. Registrazione anagrafica (paziente / kiosk iPad)
Campi (da `visita_oculistica_desktop.py`):
- **Dati paziente:** Nome e Cognome, Data di nascita (DD/MM/YYYY), Sesso (M/F), Codice Fiscale, Indirizzo, Telefono, Email.
- **Motivo della visita** (checkbox): Visita di controllo; Disturbi visivi (+ testo libero); Prescrizione occhiali/lenti; Altro (+ testo libero).
- **Anamnesi oculare e generale:** Ha mai avuto problemi agli occhi? (Sì/No + quali); Porta occhiali o lenti a contatto? (Sì/No + da quanto); Malattie sistemiche; Farmaci assunti; Interventi oculari pregressi.

All'invio: crea un paziente in stato `Registrato`.

### 2. Conferma anagrafica (medico)
Stessa schermata del modulo 1 ma editabile dal medico. Pulsante "Conferma e procedi" → stato `In corso` (o `In attesa` se messo in coda).

### 3. Refertazione (medico)
Campi clinici (da `visita_oculistica_desktop.py`):
- **Esame obiettivo oculare:** Esame annessi e segmento anteriore (testo); Acuità visiva per lontano OD/OS; Acuità visiva per vicino OD/OS; Refrazione OD (Sph/Cyl/Asse); Refrazione OS (Sph/Cyl/Asse); Pressione intraoculare OD/OS (mmHg); Esame del fondo oculare (testo); Altri esami (testo).
- **Diagnosi e prescrizione** (testo).

Al salvataggio → stato `Refertato`.

### 4. Consenso trattamento dati (paziente)
- Testo informativa privacy/GDPR (placeholder standard, da sostituire con il testo reale dello studio).
- **Canvas firma:** firma con dito/Apple Pencil su iPad (pointer events). La firma viene salvata come immagine (dataURL) nell'oggetto paziente.
- Al salvataggio → stato `Consenso firmato`.

### 5. Genera PDF (medico)
- Referto completo (tutte le sezioni dei moduli 1+3) + immagine firma consenso, con spazio per intestazione studio.
- jsPDF lato client → file `.pdf` scaricabile.
- Layout/sezioni rispecchiano `genera_pdf()` del .py.

## Modello dati (per paziente, in localStorage)

```json
{
  "id": "uuid",
  "stato": "Registrato | In attesa | In corso | In stop | Refertato | Consenso firmato | Completato",
  "medicoAssegnato": "rossi | bianchi | null",
  "anagrafica": { "nome": "", "dataNascita": "", "sesso": "", "codiceFiscale": "", "indirizzo": "", "telefono": "", "email": "" },
  "motivo": { "controllo": false, "disturbi": "", "prescrizione": false, "altro": "" },
  "anamnesi": { "problemiOcchi": "No", "qualiProblemi": "", "portaOcchiali": "No", "daQuanto": "", "malattie": "", "farmaci": "", "interventi": "" },
  "referto": { "annessi": "", "acuitaLontanoOD": "", "acuitaLontanoOS": "", "acuitaVicinoOD": "", "acuitaVicinoOS": "", "refOD": {"sph":"","cyl":"","asse":""}, "refOS": {"sph":"","cyl":"","asse":""}, "pressioneOD": "", "pressioneOS": "", "fondo": "", "altriEsami": "", "diagnosi": "" },
  "firmaConsenso": "dataURL | null",
  "eventi": [ { "stato": "Registrato", "ts": "ISO", "utente": "rossi | paziente | ..." } ],
  "createdAt": "ISO",
  "updatedAt": "ISO"
}
```

## UI/UX — stile "Demo Laboratorio" (riferimento utente)

Il gestionale adotta la lingua visiva del gestionale "Demo Laboratorio":

- **Sidebar fissa a sinistra** con gruppi (LAVORO, PAZIENTI, REFERTI) + footer utente con "Esci". Su iPad portrait collassa a drawer (hamburger). Contenuto sidebar dipende dal ruolo (il paziente/kiosk vede solo Registrazione + Firma consenso).
- **Vista dettaglio paziente** in sola lettura, a **card** (riepilogo, Anagrafica, Motivo/Anamnesi, Referto, Consenso) con breadcrumb e badge stato in header. Bottone **"Modifica"** apre i form editabili (anagrafica/referto). Separazione vista/modifica come nel riferimento.
- **Timeline "STATO DELLA VISITA"** con storico eventi (check verde per fatti, nodo ambra per stato corrente) + timestamp e utente. Alimentata da `eventi[]`.
- **Barra azioni** in fondo al dettaglio: `PDF`, `Mail` (placeholder), `Stop/Riprendi`, `Modifica`; azione distruttiva (es. Annulla) in rosso.

**Token visivi:** font system-ui; card `#f5f5f7` raggio 14px; testo `#1d1d1f`/`#6e6e73`; accento ambra `#fde68a`/`#92651a` (stato corrente/badge); verde ok `#34c759`; rosso `#ff3b30`; bottoni outline `#d2d2d7` raggio 10px. Badge stato per colore: Registrato=grigio, In corso=verde, In stop=ambra, Refertato=blu, Consenso firmato=viola, Completato=verde pieno.

## Fuori scope (per ora)

- Backend reale / sincronizzazione multi-dispositivo (simulata via localStorage).
- Autenticazione sicura (credenziali demo hardcoded).
- Testo GDPR definitivo, nomi/credenziali reali, intestazione grafica studio (placeholder).

## Default da confermare/sostituire

1. Nomi oculisti + credenziali → placeholder Rossi/Bianchi, `demo`.
2. Generazione PDF → jsPDF (CDN).
3. Testo consenso → placeholder GDPR standard.
