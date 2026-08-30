const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// Mirrors backend/app/schemas/user.py UserRead
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface LogoutResponse {
  message: string;
}

// Mirrors backend/app/models/campaign.py's status column comment.
export type CampaignStatus =
  | 'PENDING'
  | 'SCRAPING'
  | 'ENRICHING'
  | 'SYNCING'
  | 'COMPLETED'
  | 'FAILED';

// Mirrors backend/app/schemas/campaign.py CampaignRead
export interface Campaign {
  id: string;
  name: string;
  industry: string;
  country: string | null;
  state: string | null;
  max_leads: number;
  status: CampaignStatus;
  total_scraped: number;
  total_enriched: number;
  total_imported: number;
  created_by: string | null;
  created_at: string;
  completed_at: string | null;
}

// Mirrors backend/app/schemas/campaign.py CampaignCreate
export interface CampaignCreateInput {
  name: string;
  industry: string;
  country?: string | null;
  state?: string | null;
  max_leads: number;
}

// Mirrors backend/app/schemas/pagination.py Page[T]
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type CampaignListResponse = Page<Campaign>;

// Mirrors backend/app/schemas/dashboard.py DashboardStats
export interface DashboardStats {
  total_scraped: number;
  total_enriched: number;
  total_imported: number;
  active_jobs: number;
  failed_jobs: number;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// FastAPI error bodies are either { detail: string } (e.g. 401 from auth.py)
// or { detail: [{ loc, msg, type }, ...] } (422 pydantic validation errors).
interface FastApiErrorBody {
  detail?: string | { loc: (string | number)[]; msg: string; type: string }[];
}

function extractErrorMessage(body: unknown): string | null {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null;
  const { detail } = body as FastApiErrorBody;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((e) => e.msg).join('; ');
  }
  return null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      // Required so the httpOnly access_token cookie set by /auth/login
      // is sent on every subsequent request, and so Set-Cookie from the
      // backend is honored by the browser.
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(0, 'Could not reach the server. Check your connection and try again.');
  }

  if (!response.ok) {
    let message = response.statusText || `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      message = extractErrorMessage(body) ?? message;
    } catch {
      // No JSON body on this error response — fall back to statusText.
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/** POST /auth/login — sets the httpOnly JWT cookie, returns the logged-in user. */
export function login(email: string, password: string): Promise<User> {
  return request<User>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

/** POST /auth/logout — clears the cookie. */
export function logout(): Promise<LogoutResponse> {
  return request<LogoutResponse>('/auth/logout', {
    method: 'POST',
  });
}

/** GET /auth/me — resolves the current user from the cookie, or throws ApiError(401, ...). */
export function getMe(): Promise<User> {
  return request<User>('/auth/me', {
    method: 'GET',
  });
}

/** GET /dashboard/stats — aggregate numbers for the dashboard header strip. */
export function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>('/dashboard/stats', {
    method: 'GET',
  });
}

/** GET /campaigns — most-recent-first, paginated. */
export function listCampaigns(page = 1, pageSize = 20): Promise<CampaignListResponse> {
  return request<CampaignListResponse>(`/campaigns?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
  });
}

/** GET /campaigns/{id} */
export function getCampaign(id: string): Promise<Campaign> {
  return request<Campaign>(`/campaigns/${id}`, {
    method: 'GET',
  });
}

/** POST /campaigns — creates the Campaign + its initial SCRAPE job, stub-triggers n8n. */
export function createCampaign(payload: CampaignCreateInput): Promise<Campaign> {
  return request<Campaign>('/campaigns', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// -- Accounts --

export interface Account {
  id: string;
  name: string;
  api_key: string;
  remaining_credits: number | string;
  status: string;
  reset_date: string | null;
  last_used_at: string | null;
}

export interface AccountCreateInput {
  name: string;
  api_key: string;
}

export function listAccounts(provider: 'apify' | 'apollo'): Promise<Account[]> {
  return request<Account[]>(`/${provider}-accounts`, { method: 'GET' });
}

export function createAccount(provider: 'apify' | 'apollo', payload: AccountCreateInput): Promise<Account> {
  return request<Account>(`/${provider}-accounts`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// -- Companies --

export interface Company {
  id: string;
  name: string;
  website: string | null;
  normalized_domain: string | null;
  industry: string | null;
  status: string;
  hubspot_company_id: string | null;
  created_at: string;
}

export type CompanyListResponse = Page<Company>;

export function listCompanies(page = 1, pageSize = 20): Promise<CompanyListResponse> {
  return request<CompanyListResponse>(`/companies?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
  });
}

// -- HubSpot --

export interface SyncResultSummary {
  company_id: string;
  status: string;
  error?: string | null;
}

export interface BulkSyncResponse {
  results: SyncResultSummary[];
}

export interface HubspotSyncLogOut {
  id: string;
  company_id: string | null;
  contact_id: string | null;
  company_name: string | null;
  sync_status: string | null;
  error_message: string | null;
  synced_at: string;
}

export type HubspotLogsResponse = Page<HubspotSyncLogOut>;

export function syncCompanyToHubspot(companyId: string): Promise<SyncResultSummary> {
  return request<SyncResultSummary>(`/hubspot/sync/${companyId}`, {
    method: 'POST',
  });
}

export function bulkSyncToHubspot(companyIds: string[]): Promise<BulkSyncResponse> {
  return request<BulkSyncResponse>('/hubspot/sync-bulk', {
    method: 'POST',
    body: JSON.stringify({ company_ids: companyIds }),
  });
}

export function getHubspotLogs(page = 1, pageSize = 20): Promise<HubspotLogsResponse> {
  return request<HubspotLogsResponse>(`/hubspot/logs?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
  });
}
