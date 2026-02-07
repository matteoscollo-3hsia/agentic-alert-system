# Agentic Alert System

MVP per Lead Generation B2B basato su trigger commerciali rilevati da fonti di notizie.

## Obiettivo MVP
1. Gestire database locali di aziende, trigger e fornitori di notizie.
2. Eseguire un processo giornaliero che cerca trigger nelle fonti.
3. Aggiornare il database degli alert e inviare una notifica (canale TBD).

## Struttura repository
- `configs/` configurazioni di base.
- `data/` dataset CSV locali (aziende, trigger, fornitori, alert).
- `docs/` documentazione di prodotto e flusso.
- `scripts/` script operativi.
- `src/` codice sorgente del pipeline agentico.
- `tests/` test unitari e di integrazione.

## Quickstart (stub)
1. Modifica i CSV in `data/`.
2. Sincronizza l'ambiente con `uv sync`.
3. Esegui il pipeline in modalita stub.

```bash
uv sync
uv run python -m agentic_alert.pipeline
```

## Configuration
```bash
cp .env.example .env
edit .env
uv sync
uv run python -m agentic_alert.pipeline
```

### Environment Variables
- `ALERTS_ENABLED`: abilita/disabilita invio alert (`true/false`).
- `ALERT_CHANNEL`: canale di alert (es. `slack`, `email`, `tbd`).
- `SLACK_WEBHOOK_URL`: webhook Slack (se usi Slack).
- `NEWS_API_KEY`: API key per provider news.
- `COMPANIES_CSV`: override path CSV aziende (default `data/companies.csv`).
- `CONTACT_OWNERS_CSV`: override path CSV contact owners (default `data/contact_owners.csv`).
- `TRIGGERS_CSV`: override path CSV trigger (default `data/triggers.csv`).
- `PROVIDERS_CSV`: override path CSV provider (default `data/providers.csv`).
- `ARTICLES_CSV`: override path CSV articoli (default `data/articles.csv`).
- `ALERT_CANDIDATES_CSV`: override path CSV alert candidates (default `data/alert_candidates.csv`).
- `ALERTS_CSV`: override path CSV alert (default `data/alerts.csv`).

Per abilitare Slack: `ALERTS_ENABLED=true`, `ALERT_CHANNEL=slack`, `SLACK_WEBHOOK_URL=...`.
Assicurati che il webhook sia valido prima di abilitare l'invio.

## Dummy data test
```bash
uv sync
uv run python -m agentic_alert.pipeline
uv run pytest
```

## Commands
Vedi `docs/10_commands.md`.

### GitHub Actions / Daily Pipeline
**Google News company feeds sampling (live mode)**
- `GN_COMPANY_FEEDS_CAP`: limite aziende (in Actions default `200`).
- `GN_COMPANY_FEEDS_MODE`: `top_revenue` | `random` | `rolling`.
- `GN_COMPANY_FEEDS_SEED`: seed giornaliero per rotazione deterministica.
Serve per scalare oltre ~25k aziende: cap + rotazione giornaliera.

Per attivare o disattivare l'RSS, modifica la colonna `enabled` in `data/providers.csv`
per i provider con `type=rss`.
In ambienti senza rete, imposta `base_url` su `file://data/rss_snapshots/sample.xml`.
Il provider RSS locale e` preconfigurato in `data/providers.csv`.

Example output:
```
Alerts generated: 12
ALERT | Futura Tech S.p.A. | Piano Industriale | Laura Bianchi | IndustryInsights Dummy | https://industryinsights.example/futura-tech-plan
ALERT | NordWind Energy AG | Acquisizione | Marco De Luca | IndustryInsights Dummy | https://industryinsights.example/nordwind-acquisizione
```

## Note
Questo e uno scheletro iniziale. Il collegamento a fonti reali e il canale di alert saranno implementati nelle prossime iterazioni.
