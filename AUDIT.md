# Audit Log Documentation

The LeadOS platform tracks lifecycle changes and security-relevant mutations across its core entities to maintain an internal audit trail. These events are stored in the `audit_log` table.

## Captured Entities and Events

1. **Apify / Apollo Accounts** (`entity_type: apify_account` / `apollo_account`)
   - **Fields Audited**: 
     - `remaining_credits`: Tracks any manual adjustments or automated depletion/syncs.
     - `status`: Transitions between `ACTIVE`, `COOLDOWN`, or `DISABLED`.
   - **Trigger**: Recorded whenever the internal account management `PATCH` endpoints are called.
   - **Identity (`changed_by`)**: The logged-in admin user's email who performed the action.

2. **Campaigns** (`entity_type: campaign`)
   - **Fields Audited**:
     - `status`: Captures pipeline lifecycle state transitions (e.g., `PENDING` -> `SCRAPING` -> `ENRICHING` -> `COMPLETED` / `FAILED`).
   - **Trigger**: System webhooks processing n8n node lifecycle completions.
   - **Identity (`changed_by`)**: `system:n8n` (system-triggered updates).

3. **Jobs** (`entity_type: job`)
   - **Fields Audited**:
     - `status`: Execution state of sub-processes (`RUNNING`, `SUCCESS`, `FAILED`).
   - **Trigger**: System webhooks processing queue changes.
   - **Identity (`changed_by`)**: `system:n8n` (system-triggered updates).

4. **Companies** (`entity_type: company`)
   - **Fields Audited**:
     - `status` (Initial Insertion): Tracks raw ingress. Recorded as `None` -> `CLEANED`.
     - `status` (Enrichment): Tracks data enrichment completion (e.g., `CLEANED` -> `ENRICHED`).
     - `status` (Manual Progression): Tracks user-driven pipeline staging (e.g., `HubSpot` -> `Contacted` -> `Qualified` -> `Customer`).
   - **Trigger**: System bulk-insert routes and the `PATCH /companies/{id}` endpoints.
   - **Identity (`changed_by`)**: `system:n8n` for automated pipeline phases, or the logged-in user's email for manual sales/admin interventions.

## Schema Reference

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` | Primary key auto-increment ID. |
| `entity_type` | `VARCHAR(100)` | The type of entity modified (e.g., `campaign`, `company`, `apify_account`). |
| `entity_id` | `VARCHAR(100)` | The UUID or ID of the specific entity instance. |
| `field` | `VARCHAR(100)` | The exact property modified (e.g., `status`, `remaining_credits`). |
| `old_value` | `TEXT` | The previous value before the mutation (can be `NULL` for initial inserts). |
| `new_value` | `TEXT` | The newly committed value. |
| `changed_by` | `VARCHAR(120)` | The identity performing the change. E.g., user email or `system:n8n`. |
| `changed_at` | `TIMESTAMPTZ` | The exact UTC timestamp of the change. |

## Querying the Audit Log

Since all updates write immutably to this single table, you can easily query the lifecycle of any specific lead or campaign. 

### Examples

**View the status history of a specific Campaign:**
```sql
SELECT field, old_value, new_value, changed_by, changed_at 
FROM audit_log 
WHERE entity_type = 'campaign' AND entity_id = 'c8b92b...'
ORDER BY changed_at ASC;
```

**Find all manual credit adjustments made to Apify accounts this month:**
```sql
SELECT entity_id, old_value, new_value, changed_by, changed_at 
FROM audit_log 
WHERE entity_type = 'apify_account' 
  AND field = 'remaining_credits'
  AND changed_by != 'system:n8n'
  AND changed_at >= date_trunc('month', CURRENT_DATE);
```

**See which Sales Representative progressed a Company to "Customer":**
```sql
SELECT changed_by, changed_at 
FROM audit_log 
WHERE entity_type = 'company' 
  AND field = 'status' 
  AND new_value = 'CUSTOMER';
```
