# Real Data Setup (Template)

Questo documento spiega come preparare file locali con dati reali senza committarli.

## 1) Copiare i template in data_private/

```bash
mkdir -p data_private
cp data/templates/companies.template.csv data_private/companies.csv
cp data/templates/providers.template.csv data_private/providers.csv
cp data/templates/triggers.template.csv data_private/triggers.csv
```

## 2) Companies DB: required fields for matching

Per avere match affidabili:
website_domain e` il segnale piu` forte (match su dominio presente in URL o snippet).
aliases aiuta a catturare varianti del nome.
Per MVP Italia: usa country=IT e non includere banche nel dataset reale.
Schema companies: company_id,name,aliases,revenue_eur,industry_code,industry_description,website,website_domain,country,contact_owner,status.

I file reali vanno in `data_private/` e si usano via env vars, ad esempio:
`COMPANIES_CSV=data_private/companies.csv`.

Import da Orbis (XLSX):

```bash
python scripts/import_orbis_xlsx.py
```

Puoi sovrascrivere path o sheet:

```bash
ORBIS_EXPORT_PATH=data_private/orbis_export.xlsx ORBIS_SHEET_NAME="Sheet1" python scripts/import_orbis_xlsx.py
```

## 3) Configurare i provider RSS reali

Apri `data_private/providers.csv` (creato dal template) e inserisci i provider reali.
Esempio con 3 feed RSS pubblici (puoi sostituirli con i tuoi):

```csv
provider_id,name,type,base_url,enabled
rss_bbc,BBC News,rss,https://feeds.bbci.co.uk/news/rss.xml,true
rss_reuters,Reuters World,rss,https://www.reuters.com/rssFeed/worldNews,true
rss_hn,Hacker News,rss,https://news.ycombinator.com/rss,false
```

Per mantenere il fallback offline, aggiungi anche uno snapshot locale:

```csv
provider_id,name,type,base_url,enabled
rss_snapshot,Local RSS Snapshot,rss_file,file://data/rss_snapshots/sample.xml,true
```

Ricorda: `data_private/` non va committato.

## 4) Google News RSS (query-based)

Nel template sono presenti feed Google News (prefisso `GN_`) gia` pronti ma disabilitati.
Per usarli:

1. Apri `data_private/providers.csv`.
2. Seleziona i feed `GN_` di interesse e imposta `enabled=true`.
3. Modifica la query nell'URL se vuoi affinare i risultati (mantieni `hl=it&gl=IT&ceid=IT:it`).

## 5) Company Press RSS

Questo provider si usa solo se l'azienda ha un RSS ufficiale della newsroom/press.
Se non esiste un RSS, e` fuori scope MVP (no scraping HTML).

Esempio di riga in `data_private/providers.csv`:

```csv
provider_id,name,type,base_url,enabled
company_press_acme,ACME Press RSS,rss,https://www.example.com/press/rss,true
```

Ricorda: `data_private/` non va committato.

Nota: se un provider live cambia URL o blocca l'accesso, override in `data_private/providers.csv`.
