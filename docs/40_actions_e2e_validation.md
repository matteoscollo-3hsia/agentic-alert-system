# Validazione E2E GitHub Actions (workflow_dispatch)

Documento di validazione manuale per il workflow **Daily Pipeline** con due run consecutive.

## 1) Preconditions
- Branch repo: `main`
- Secret `SLACK_WEBHOOK_URL` presente: **[YES/NO]**
- Workflow: **Daily Pipeline**
- Providers: run live di default; `Local RSS Snapshot` solo test/offline.

## 2) Procedura (UI)
1. Apri GitHub → **Actions** → **Daily Pipeline**.
2. Clicca **Run workflow** → seleziona `main` → **Run workflow**.
3. Attendi completamento **Run #1**.
4. Avvia **Run #2** subito dopo, sempre su `main`.

## 3) Evidenze da copiare (per ogni run)
Compila questa sezione due volte, una per **Run #1** e una per **Run #2**.

### Run #[1/2]
**Timestamp (Europe/Rome):** `YYYY-MM-DD HH:MM`

**PROVENANCE (incollare l'intero blocco):**
```
[INCOLLA QUI]
```

**Summary line (una riga):**
```
Total news items: ... | Alerts generated: ... | Dedupe skipped: ...
```

**Slack dispatch evidence:**
- Log (alert lines o “Dispatch disabled…”):
```
[INCOLLA QUI]
```
- Slack messages ricevuti: **[YES/NO]**

**Commit step evidence:**
- Log:
```
No alerts.csv changes to commit.
```
oppure
```
[commit + push output]
```
- `data/alerts.csv` cambiato: **[YES/NO]**

## 4) PASS criteria (strict)
**Run #1**
- `Alerts generated` **>= 0** (se esistono match).
- Se `Alerts generated > 0` ⇒ Slack **YES**.
- Se `data/alerts.csv` cambia ⇒ commit **eseguito**.

**Run #2 (stessi input)**
- `Alerts generated = 0`.
- `Dedupe skipped > 0` (quando gli stessi item sono processati).
- Slack **NO**.
- Commit step: **No alerts.csv changes to commit.**

**Caso senza match reali**
- Entrambi i run con `Alerts generated = 0`.
- Commit step: **No alerts.csv changes to commit.**
- Slack **NO**.
- PROVENANCE conferma i CSV corretti.

## 5) Troubleshooting (MVP)
- Slack non inviato:
  - Verifica `SLACK_WEBHOOK_URL` secret e `ALERTS_ENABLED=true`, `ALERT_CHANNEL=slack`.
- Nessun commit:
  - Verifica `permissions: contents: write` nel workflow.
  - Verifica che `git status --porcelain -- data/alerts.csv` non sia vuoto.
- PROVENANCE con CSV sbagliati:
  - Verifica env override nel workflow e percorsi dei CSV.
