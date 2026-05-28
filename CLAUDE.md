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
│   └── index.html        # Two-column sajt: dashboard levo, chat desno (mobile: tab navigacija)
├── Vendor details anonymized.xlsx   # Spend zaokružen na najbliži 10.000 (na GitHub-u)
├── requirements.txt
├── Procfile              # Railway start komanda
├── nixpacks.toml         # Railway build config
└── start.bat             # Lokalno pokretanje
```

## Excel podaci

- **Fajl:** `Vendor details anonymized.xlsx` (originalni sa pravim podacima ostaje lokalno)
- **Anonimizacija:** Spend (USD) zaokružen na najbliži 10.000 radi privatnosti
- **Sheet:** `Export`
- **Redova:** do 200.000 (limit u `load_data()` da ne padne RAM)
- **Kolone:** Fiscal Year, Region, Affiliate, Company Code, Vendor Number, Vendor Name, Level 1-4, Managed Supplier, Supplier Scope, PO Number, Spend (USD)
- **Ukupan spend:** ~$1.01B USD (anonymizovan)
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

## Implementirano

- **Prompt caching** (`anthropic-beta: prompt-caching-2024-07-31`) — system prompt se kešira, ~70% ušteda na input tokenima
- **Dashboard endpoint** — vraća top vendore, kategorije po spendу, scope breakdown
- **Keep-alive** — GitHub Actions workflow pinga Railway svako 20 minuta da server ne zaspi
- **Mobile layout** — tab navigacija (Dashboard / Chat) ispod 900px, `dvh` + safe area insets za chat input
- **Scope breakdown** — query engine vraća Local/Regional/Global spend sa procentima
- **Memory crash fix** — `load_data()` limitiran na 200k redova + preskače ghost redove bez Affiliate-a
- **Anonimizovani podaci** — spend zaokružen na najbliži 10.000 za demo svrhe

## Poznati rizici (pre-mortem, 2026-05-27)

| Rizik | Kategorija | Urgentnost |
|-------|-----------|------------|
| Nema UI za upload novog Excel-a — klijent ne može sam ažurirati podatke | 🐯 Tiger | Launch-blocking |
| Nema autentifikacije — Railway URL je javan, API budžet se može istrošiti | 🐯 Tiger | Fast-follow |
| Railway sleep na free tier — server se gasi nakon neaktivnosti | 🐯 Tiger | Fast-follow |
| Nema logova/monitoringa — ne znamo kad/gde pada | 🐘 Elephant | Track |

## Buduće mogućnosti

- **Chat widget** — jedna `<script>` linija, chatbot se pojavi dole desno na bilo kom sajtu (kao Intercom/Crisp). Još nije implementirano.
- **Excel upload UI** — forma za upload novog fajla bez deploy-a
- **Autentifikacija** — API key ili login za zaštitu endpointa
