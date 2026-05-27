# CLAUDE.md — Vendor Analytics Chatbot

## Šta je ovaj projekat

Chatbot koji odgovara na pitanja o vendor/dobavljač podacima iz Excel tabele.
Napravljen za EMEA procurement tim, FY2026 podaci.

## Stack

- **Backend:** Python 3.13 + FastAPI + Anthropic SDK (claude-sonnet-4-6)
- **Data:** pandas čita Excel fajl u RAM pri pokretanju
- **Frontend:** Vanilla HTML/CSS/JS (two-column layout)
- **Deploy:** Railway.app

## Struktura

```
chatbotstojan/
├── backend/
│   ├── main.py           # FastAPI server, /chat i /dashboard endpointi
│   ├── data_handler.py   # Smart pandas query engine
│   └── .env              # ANTHROPIC_API_KEY (nije na GitHub-u)
├── frontend/
│   └── index.html        # Two-column sajt: dashboard levo, chat desno
├── Vendor details by vendor segmention (2).xlsx
├── requirements.txt
├── Procfile              # Railway start komanda
├── nixpacks.toml         # Railway build config
└── start.bat             # Lokalno pokretanje
```

## Excel podaci

- **Fajl:** `Vendor details by vendor segmention (2).xlsx`
- **Sheet:** `Export`
- **Redova:** 68.165
- **Kolone:** Fiscal Year, Region, Affiliate, Company Code, Vendor Number, Vendor Name, Level 1-4, Managed Supplier, Supplier Scope, PO Number, Spend (USD)
- **Ukupan spend:** ~$1.05B USD
- **Affiliates (21):** Austria, Balkans, Benelux, Central Europe, East Hub, Eurovision, France, Germany, Iberia, India, Israel, Italy, Lachen Plant, Middle-East, Nordics, Oevel Plant, Russia & CIS, South Africa, Switzerland, Turkey, UK

## Kako radi

1. Server učita Excel u pandas DataFrame jednom pri pokretanju
2. Korisnik pošalje pitanje kroz chat
3. `data_handler.py` detektuje filtre (affiliate, kategorija, vendor, scope) i filtrira DataFrame
4. Filtrirani rezultat (max ~50 redova) se šalje Claude-u kao kontekst
5. Claude generiše prirodan odgovor na osnovu podataka

## API Endpointi

- `GET /` — frontend sajt
- `POST /chat` — prima `{message, history}`, vraća `{reply}`
- `GET /dashboard` — vraća KPI podatke za levu stranu (top vendori, kategorije, scope)
- `GET /health` — status check

## Lokalno pokretanje

```bat
start.bat
# ili manuelno:
cd backend
python -m uvicorn main:app --reload --port 8000
```

Otvori: `http://localhost:8000`

## Production

**URL:** `https://chatbotstojan-production.up.railway.app/`
**Platform:** Railway.app
**ENV varijable na Railway:** `ANTHROPIC_API_KEY`

## Važne napomene

- `.env` fajl NIJE na GitHub-u (zaštićen `.gitignore`-om)
- API ključ se postavlja kao Railway environment variable
- Excel fajl JE na GitHub-u (potreban za deploy)
- Svaki push na `main` branch automatski trigguje novi deploy na Railway
