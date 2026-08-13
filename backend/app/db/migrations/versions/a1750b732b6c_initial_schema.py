"""initial schema

Revision ID: a1750b732b6c
Revises: 
Create Date: 2026-08-13 18:26:16.596530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1750b732b6c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
-- USERS (internal team, not customers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'sales',  -- 'admin' | 'sales'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- CAMPAIGNS
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(120) NOT NULL,
    country VARCHAR(80),
    state VARCHAR(80),
    max_leads INT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, SCRAPING, ENRICHING, SYNCING, COMPLETED, FAILED
    total_scraped INT DEFAULT 0,
    total_enriched INT DEFAULT 0,
    total_imported INT DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- JOBS (tracks each async step tied to a campaign — this is your "queue log")
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    job_type VARCHAR(30) NOT NULL,  -- SCRAPE, ENRICH, SYNC
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, RUNNING, SUCCESS, FAILED
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- COMPANIES
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    name VARCHAR(255) NOT NULL,
    website VARCHAR(255),
    normalized_domain VARCHAR(255),  -- used for deduplication
    phone VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(120),
    state VARCHAR(120),
    country VARCHAR(120),
    industry VARCHAR(120),
    source VARCHAR(50),              -- 'apify'
    google_rating NUMERIC(2,1),
    review_count INT,
    lead_score INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'RAW', -- RAW, CLEANED, ENRICHED, READY, HUBSPOT, CONTACTED, QUALIFIED, CUSTOMER
    hubspot_company_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (normalized_domain)  -- global dedup across all campaigns
);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_campaign ON companies(campaign_id);

-- CONTACTS
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    position VARCHAR(150),
    email VARCHAR(255),
    linkedin_url VARCHAR(255),
    apollo_source_id VARCHAR(100),
    verification_status VARCHAR(20),  -- verified, guessed, unknown
    hubspot_contact_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_contacts_company ON contacts(company_id);

-- APIFY ACCOUNTS
CREATE TABLE apify_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    api_key VARCHAR(255) NOT NULL,   -- encrypt at rest (see Best Practices)
    remaining_credits NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, COOLDOWN, DISABLED
    reset_date DATE,
    last_used_at TIMESTAMPTZ
);

-- APOLLO ACCOUNTS
CREATE TABLE apollo_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    remaining_credits NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    reset_date DATE,
    last_used_at TIMESTAMPTZ
);

-- HUBSPOT SYNC LOGS
CREATE TABLE hubspot_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    contact_id UUID REFERENCES contacts(id),
    sync_status VARCHAR(20),   -- SUCCESS, FAILED, SKIPPED_DUPLICATE
    error_message TEXT,
    synced_at TIMESTAMPTZ DEFAULT now()
);
    """)


def downgrade() -> None:
    op.execute("""
DROP TABLE IF EXISTS hubspot_sync_logs CASCADE;
DROP TABLE IF EXISTS apollo_accounts CASCADE;
DROP TABLE IF EXISTS apify_accounts CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS users CASCADE;
    """)
