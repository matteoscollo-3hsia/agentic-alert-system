# Provider Coverage (1:1 Trigger Mapping)

Questo mapping collega ogni sub-trigger ai provider che lo coprono.
- Hard coverage: publisher/regolatori/wires
- Soft coverage: Google News RSS query-based

## Cluster 1 — Piano strategico in scadenza

Sub-trigger: ciclo strategico concluso
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_PianoStrategico_Scadenza

Sub-trigger: richiesta Board/azionisti/famiglia
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_Board_Azionisti

Sub-trigger: preparazione a IPO / ingresso investitore / vendita
Hard coverage: PR Newswire All Releases; Business Wire RSS; ANSA Economia; Adnkronos Economia; Teleborsa News
Soft coverage: GN_IT_IPO_PE_Vendita

## Cluster 2 — Strategia esiste ma non diventa execution

Sub-trigger: piano gia` definito ma priorita` poco chiare
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_OrganizzazioneNonAllineata

Sub-trigger: organizzazione non allineata
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_OrganizzazioneNonAllineata

Sub-trigger: nessun sistema di responsabilita` e review
Hard coverage: PR Newswire All Releases; Business Wire RSS; ANSA Economia; Adnkronos Economia
Soft coverage: GN_IT_ExecutionGap

## Cluster 3 — Contesto cambiato, strategia da aggiornare

Sub-trigger: cambiamenti mercato/tecnologia (AI)/regolazione
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; MIMIT Notizie; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_AI_Regolazione

Sub-trigger: strategia formalmente valida ma non piu` adeguata
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_AggiornamentoStrategia

## Cluster 4 — Passaggio generazionale / transizione leadership

Sub-trigger: passaggio generazionale in corso o imminente / nuova proprieta`
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_PassaggioGenerazionale

Sub-trigger: nuovo CEO o eredi con leadership team da consolidare
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_NuovoCEO_Leadership

Sub-trigger: necessita` di sviluppo capability manageriali/decisionali
Hard coverage: PR Newswire All Releases; Business Wire RSS; ANSA Economia; Adnkronos Economia
Soft coverage: GN_IT_ExecutionGap

## Cluster 5 — Discontinuita` strutturale / perimetro strategico

Sub-trigger: ingresso fondo / cambio proprieta`
Hard coverage: EU DG COMP Mergers (Press Corner); ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_CambioProprieta_Perimetro

Sub-trigger: M&A, carve-out, riorganizzazioni multi-BU
Hard coverage: EU DG COMP Mergers (Press Corner); ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_MA_CarveOut

Sub-trigger: ridefinizione perimetro business o geografico
Hard coverage: ANSA Economia; Adnkronos Economia; Teleborsa News; PR Newswire All Releases; Business Wire RSS
Soft coverage: GN_IT_CambioProprieta_Perimetro

Nota: i provider "Company Press RSS" (per-azienda) sono opzionali e migliorano la copertura hard solo se l'azienda pubblica un RSS ufficiale.
