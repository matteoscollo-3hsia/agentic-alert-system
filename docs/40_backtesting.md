# Backtesting storico (MVP)

Il backtest usa fonti documentali storiche (es. `gdelt_doc`) per simulare
alert su una finestra temporale passata, senza modificare la pipeline di
matching. I risultati finiscono in `data/alerts_backtest.csv` con
`run_type=backtest`.

Nota: i risultati GDELT sono rolling e soggetti a variazioni; per MVP
limitiamo il lookback e il numero massimo di articoli per azienda.

## Setup rapido

1) Aggiungi un provider `gdelt_doc` nel tuo `providers.csv` e abilitalo.
2) Esegui la pipeline con `BACKTEST_ENABLED=true` e un lookback ridotto.

Esempio:

```bash
BACKTEST_ENABLED=true \
BACKTEST_LOOKBACK_DAYS=14 \
BACKTEST_COMPANY_IDS=c001,c002 \
BACKTEST_OUTPUT_CSV=data/alerts_backtest.csv \
PROVIDERS_CSV=data_private/providers.csv \
uv run python -m agentic_alert.pipeline
```

## Offline snapshot mode

Per validare il backtest senza rete/DNS usa il provider `gdelt_snapshot`
con un file JSON locale (es. `file://data/backtest_snapshots/sample_gdelt.json`).
Puoi mettere snapshot reali in `data_private/` e non committarli.

Schema JSON MVP:

```json
[
  {
    "title": "Titolo articolo",
    "url": "https://example.com/news/123",
    "published_at": "2026-02-01T10:00:00Z",
    "source": "GDELT Snapshot",
    "snippet": "Testo breve o estratto"
  }
]
```

## Tuning su 2–3 aziende

- Usa `BACKTEST_COMPANY_IDS` per ridurre il rumore e accelerare il debug.
- Raffina `aliases` e `website_domain` nel DB aziende: sono i match più forti.

## Interpretazione falsi positivi/negativi

- **Falsi positivi**: riduci alias troppo generici o aggiungi
  `website_domain` più specifici.
- **Falsi negativi**: aggiungi alias realistici (ragioni sociali,
  varianti "S.p.A./SRL") e verifica che i trigger keyword coprano il caso.
