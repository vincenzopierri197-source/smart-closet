# Smart Closet AI — IndexedDB + Backup

App web con inventario civile, militare e sportivo, lavaggio intelligente, look e abbinamenti con Gemini o Groq, organizzazione bagagli, **IndexedDB**, **backup completo** e installazione come **app (PWA)**.

## File del progetto

| File | A cosa serve |
| --- | --- |
| `index.html` | struttura della pagina |
| `style.css` | stili |
| `app.js` | logica dell'app |
| `manifest.json`, `sw.js`, `icon-192.png`, `icon-512.png` | installazione e uso offline (PWA) |
| `app.py`, `requirements.txt` | backend Flask opzionale |

## Archiviazione

Capi e foto sono salvati in **IndexedDB**, in locale sul dispositivo:

- Le foto sono ridimensionate (max 900 px) e salvate come Blob, non come testo base64 in localStorage.
- Lo spazio disponibile è molto superiore al limite di circa 5 MB di localStorage.
- I dati non vengono caricati su un server.

## Categorie

Ogni modulo ha le sue categorie (14 civile, 13 militare, 10 sportivo). Puoi:

- sceglierla quando aggiungi un capo (obbligatoria);
- cambiarla in qualsiasi momento con il pulsante **Categoria** del capo;
- usare **🔄 Ricontrolla categorie** nell'inventario: l'app propone i capi che stanno in una categoria troppo generica (per esempio una felpa in «Maglioni») e tu scegli quali spostare.

Al primo avvio dopo l'aggiornamento, se ci sono capi già salvati che possono passare a una categoria più precisa, l'app te li propone una volta sola.

## Importazione da cartella

Formato dei file: `Nome capo - Marca - Colore - Taglia.jpg`.

La categoria è suggerita **solo dal nome del capo** (non da marca o colore), con confronto a parole intere. Prima di importare compare una schermata di revisione dove puoi correggere ogni categoria; le righe non riconosciute sono segnate con ⚠️.

## Abbinamenti

Le regole locali escludono gli accostamenti estate/inverno (per esempio pantaloncini con cappotto o maglione). Intimo, calze e abbigliamento da casa non hanno abbinamenti suggeriti.

## Backup e ripristino

Nella sezione **💾 Backup e ripristino**:

- **Esporta backup completo**: scarica un file JSON con capi, foto e bagagli. Le API key non sono incluse.
- **Ripristino**: il file viene **controllato per intero prima di toccare i dati** (struttura, identificativi, moduli, categorie, immagini). Se non è valido non cambia nulla. Se è valido ti viene chiesta conferma e, se vuoi, viene scaricata prima una copia dei dati attuali. La sostituzione è atomica: o riesce tutta o non cambia nulla.

## Impostazioni AI

Clicca sul pulsante **🔑** in alto a destra per inserire:

- API key Gemini e modello Gemini.
- API key Groq gratuita e modello Groq.

Le chiavi restano nel `localStorage` di questo browser e le richieste partono direttamente dal tuo dispositivo verso Gemini/Groq. Per questo:

- **non scrivere le chiavi nel codice** e non committarle nella repository;
- usa chiavi con quota limitata;
- non salvarle su dispositivi condivisi.

## Installazione come app

Su un indirizzo `https://` (per esempio GitHub Pages) o `http://localhost`, dal menu del browser scegli **Installa app** / **Aggiungi a schermata Home**. L'app funziona anche offline; solo Gemini e Groq richiedono connessione.

## Pubblicazione su GitHub Pages

1. Crea una repository GitHub.
2. Carica **tutti** i file della tabella sopra (almeno `index.html`, `style.css`, `app.js`, `manifest.json`, `sw.js` e le due icone).
3. Vai in **Settings → Pages**.
4. Seleziona il branch principale e la cartella `/root`.

Dopo un aggiornamento, se il browser mostra ancora la versione vecchia, ricarica la pagina due volte (il service worker si aggiorna in background).

## Backend Python opzionale

L'app **non ha bisogno** del backend: usa IndexedDB nel browser. `app.py` è un'API di esempio coerente con il frontend (stessi moduli, categorie e transizioni di stato).

```bash
pip install -r requirements.txt
python app.py
```

- Ascolta solo su `127.0.0.1` (questo computer). Per cambiare: `HOST=...` e `PORT=...`.
- Il debugger di Flask è **spento**; si attiva con `FLASK_DEBUG=1` ed è da usare solo in sviluppo, mai con `HOST=0.0.0.0`.
- I dati sono salvati in `garments.json` (percorso modificabile con `SMART_CLOSET_DATA`).
- Endpoint: `GET /api/categories`, `GET|POST /api/garments`, `GET|DELETE /api/garments/<id>`, `POST /api/garments/<id>/status`.
