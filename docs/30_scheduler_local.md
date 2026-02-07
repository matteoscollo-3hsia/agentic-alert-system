# Scheduler Locale (Cron)

Questo scheduler esegue la pipeline MVP in modo automatico su macchina locale.

## Prima attivazione
Prima di attivare il cron, esegui una volta `uv sync` manualmente.
Il cron **non** deve fare installazioni.

## Cache uv
Lo script imposta `UV_CACHE_DIR` su `.cache/uv` per evitare problemi di permessi
in ambienti cron con PATH ridotto e home limitata.

## Variabili d'ambiente (sicure)
Usa un file locale non versionato (es. `scripts/.env.local`) oppure imposta le variabili direttamente nella crontab.
**Non committare** `scripts/.env.local` e **non committare** `.env`.

Esempio `scripts/.env.local` (NON versionare):
```bash
ALERTS_ENABLED=true
ALERT_CHANNEL=slack
SLACK_WEBHOOK_URL=... 
```

## Esempi di crontab
Ogni giorno alle 08:30:
```cron
30 8 * * * /usr/bin/env bash -lc "source /path/to/repo/scripts/.env.local; /path/to/repo/scripts/run_daily_local.sh"
```

Ogni ora (test):
```cron
0 * * * * /usr/bin/env bash -lc "source /path/to/repo/scripts/.env.local; /path/to/repo/scripts/run_daily_local.sh"
```

## Verifica
Controlla i log in `logs/` (es. `logs/daily_run_YYYYMMDD.log`).

## Disabilitare
Commenta la riga nella crontab.

## macOS (launchd)
Installazione:
```bash
./scripts/launchd/install_launchd.sh
```

Disinstallazione:
```bash
launchctl unload "$HOME/Library/LaunchAgents/com.agentic-alert.daily.plist"
rm -f "$HOME/Library/LaunchAgents/com.agentic-alert.daily.plist"
```

Nota Slack: esporta `SLACK_WEBHOOK_URL` nel terminale prima di eseguire lo script
di installazione; lo script lo inserisce solo nel plist installato in
`~/Library/LaunchAgents/`. Per ruotare il webhook: disinstalla e reinstalla
(oppure modifica il plist installato).

Nota: se usi `scripts/.env.local`, non committarlo e gestisci le variabili in modo locale.

Nota proxy (launchd): launchd non eredita `HTTPS_PROXY`/`HTTP_PROXY` dalla shell.
Se sei dietro proxy, aggiungi queste variabili in `EnvironmentVariables` del plist
prima del bootstrap/kickstart.

Nota PATH (launchd): launchd non eredita il PATH della shell. Il PATH viene
impostato nel plist per garantire un ambiente deterministico.

Nota NetworkState: con `KeepAlive -> NetworkState=true` il job non parte prima
che la rete sia disponibile (utile su Wi-Fi all'avvio).

Troubleshooting rapido: controlla `logs/launchd.err.log` e cerca le righe
`NET_PREFLIGHT` nel `daily_run_YYYYMMDD.log`.

## macOS (launchd) — Final setup

Installare:

```bash
./scripts/launchd/install_launchd.sh
```

Questo script:
- installa il launch agent
- lo attiva
- mostra il suo stato

Per avviarlo subito (senza aspettare il login):

```bash
launchctl kickstart -k gui/$(id -u)/com.agentic-alert-system
```
