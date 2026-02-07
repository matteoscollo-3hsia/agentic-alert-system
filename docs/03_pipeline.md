# Pipeline Giornaliero (Stub)

1. Carica `data/companies.csv`, `data/triggers.csv`, `data/providers.csv`.
2. Per ogni provider, esegui uno stub di ricerca notizie.
3. Esegui matching tra notizie e trigger.
4. Genera alert e salva in `data/alerts.csv`.
5. Invio alert via dispatcher (stub).
