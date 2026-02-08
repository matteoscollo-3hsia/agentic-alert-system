Questo file è la source of truth: ogni nuova entrypoint/command introdotto deve aggiornare questo documento.

## Su Github: repositories > actions > daily pipeline > run workflow. Per startarlo Manualmente
## Repository > Setting > Secrets & Variables > New Secret > inserire webhook

| Command | Descrizione | Output atteso | Note |
| --- | --- | --- | --- |
| `uv sync` | Sincronizza l'ambiente e installa le dipendenze. | Pacchetti installati/sincronizzati con log di `uv`. | Necessario prima di eseguire pipeline o test. |
| `uv run python -m agentic_alert.pipeline` | Esegue la pipeline MVP con dati locali. | Log con numero alert generati e dettaglio alert. | Usa i CSV in `data/`. Al secondo run, il dedupe evita duplicati (0 righe nuove in `alerts.csv`). In assenza di rete usa `base_url=file://data/rss_snapshots/sample.xml`. |
| `RSS_DIAGNOSTICS=true PROVIDERS_CSV=data_private/providers.csv uv run python -m agentic_alert.pipeline` | Esegue la pipeline con diagnostica RSS (una riga per provider). | Log con http_status, final_url, content_type, bytes, bozo, entries. | Utile per distinguere feed vuoto vs blocco/redirect/TLS. |
| `python scripts/import_orbis_xlsx.py` | Importa `orbis_export.xlsx` in `data_private/companies.csv`. | Log con conteggi (rows_in, rows_written, missing_website, missing_revenue). | Usa `ORBIS_EXPORT_PATH` e `ORBIS_SHEET_NAME` se vuoi sovrascrivere path/sheet. |
| `BACKTEST_ENABLED=true BACKTEST_LOOKBACK_DAYS=7 BACKTEST_COMPANY_IDS=c001,c002 BACKTEST_OUTPUT_CSV=data/alerts_backtest.csv PROVIDERS_CSV=data_private/providers.csv uv run python -m agentic_alert.pipeline` | Esegue un backtest storico (lookback giorni) e scrive su `alerts_backtest.csv`. | Log con numero alert generati + CSV backtest con `run_type=backtest`. | Per testare su 2-3 aziende usare `BACKTEST_COMPANY_IDS`. Slack resta off a meno di `ALERTS_ENABLED=true`. |
| `python -c "from pathlib import Path; Path('data/alerts.csv').write_text('alert_id,company_id,company_name,trigger_id,trigger_name,contact_owner,source,article_url,published_at,dedupe_key,created_at,status\\n', encoding='utf-8')"` | Reset `alerts.csv` al solo header. | File `data/alerts.csv` ripulito. | Utile prima di validazioni end-to-end. |
| `COMPANIES_CSV=data_private/companies.csv PROVIDERS_CSV=data_private/providers.csv TRIGGERS_CSV=data_private/triggers.csv uv run python -m agentic_alert.pipeline` | Run with real data (via env vars). | Log con numero alert generati e dettaglio alert. | Orbis e` committato in `data/companies.csv`; `data_private/` resta opzionale. |
| `./scripts/run_daily.sh` | Wrapper per eseguire la pipeline MVP. | Stesso output di `uv run python -m agentic_alert.pipeline`. | Richiede permessi di esecuzione sul file. |
| `./scripts/run_daily_local.sh` | Esegue la pipeline con logging in `logs/`. | Log file in `logs/daily_run_YYYYMMDD.log`. | Consigliato per scheduling locale. |
| `./scripts/launchd/install_launchd.sh` | Installa il job launchd su macOS. | Output con path plist e comandi utili. | Vedi `docs/30_scheduler_local.md`. |
| `launchctl kickstart -k "gui/$UID/com.agentic-alert.daily"` | Forza un run del job launchd. | Run immediato con log in `logs/`. | Solo macOS. |
| `launchctl unload "$HOME/Library/LaunchAgents/com.agentic-alert.daily.plist" && rm -f "$HOME/Library/LaunchAgents/com.agentic-alert.daily.plist"` | Disinstalla il job launchd. | Job rimosso da LaunchAgents. | Solo macOS. |
| `uv run pytest -q` | Esegue la suite di test (quiet). | Report test con pass/fail. | Usa l'ambiente `uv`. |

Per abilitare Slack: `ALERTS_ENABLED=true`, `ALERT_CHANNEL=slack`, `SLACK_WEBHOOK_URL=...`.
Per scheduling locale vedi `docs/30_scheduler_local.md`.
Dataset aziende: `data/companies.csv` = Orbis (default prod). `data/companies.sample.csv` = sample deterministico per test/dev.
In CI/test usa `COMPANIES_CSV=data/companies.sample.csv` + snapshot provider.

**GitHub Actions**
1. Aggiungi il secret `SLACK_WEBHOOK_URL` in GitHub: Settings → Secrets and variables → Actions → New repository secret.
2. Trigger manuale: Actions → Daily Pipeline → Run workflow.
3. Persistenza alert: il workflow committa automaticamente `data/alerts.csv` sul branch (vedi commit history).
4. Artifact/log: nella pagina del run trovi l'artifact `daily_run_YYYY-MM-DD` con `logs/*` e `data/alerts.csv`.
5. Nota schedule: GitHub usa UTC. Il workflow schedula `0 5 * * *` e `0 6 * * *` e salta i run fuori dalle 07:00 Europe/Rome.
6. Validazione E2E manuale: vedi `docs/40_actions_e2e_validation.md`.
7. Default live: Actions usa provider live; `Local RSS Snapshot` è solo test/offline.
GN SLA 96h: copertura top 4.000 con rotazione giornaliera (~1.050/day).
Env chiave: `GN_COMPANY_UNIVERSE_SIZE`, `GN_COMPANY_DAILY_BATCH`, `GN_RECENCY_HOURS`, `GN_MAX_ITEMS_PER_FEED`.
Actions imposta `GN_MODE=rotation_sla` e persiste `data/gn_rotation_state.json`.
