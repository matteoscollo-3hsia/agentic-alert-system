# Data Model

## Aziende
Campi:
- `company_id`
- `name`
- `aliases`
- `revenue_eur`
- `industry_code`
- `industry_description`
- `website`
- `website_domain`
- `country`
- `contact_owner`
- `status`

## Trigger
Campi:
- `trigger_id`
- `name`
- `keywords`
- `priority`
- `description`

## Fornitori Notizie
Campi:
- `provider_id`
- `name`
- `type`
- `base_url`
- `enabled`

## Articoli (Ingestion Output)
Campi:
- `article_id`
- `provider_id`
- `source_name`
- `title`
- `url`
- `published_at`
- `content_snippet`

## Alert Candidates
Campi:
- `candidate_id`
- `article_id`
- `company_id`
- `trigger_id`
- `match_method`
- `confidence`

## Alert
Campi:
- `alert_id`
- `company_id`
- `company_name`
- `trigger_id`
- `trigger_name`
- `contact_owner`
- `source`
- `article_url`
- `published_at`
- `dedupe_key`
- `created_at`
- `status`

`dedupe_key` è calcolato come `company_id|trigger_id|published_date|norm_title` dove
`published_date` è la data UTC (YYYY-MM-DD) e `norm_title` è il titolo normalizzato.
Serve per il dedupe cross-provider della stessa notizia.
