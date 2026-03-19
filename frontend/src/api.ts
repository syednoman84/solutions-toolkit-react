import type { LoadParamsResponse, ScriptResult, CloneResult, TenantProduct } from './types'

const json = (r: Response) => r.json()
const post = (url: string, body?: unknown) =>
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  }).then(json)

// Main setup
export const loadParams = (): Promise<LoadParamsResponse> => fetch('/api/load-params').then(json)
export const saveParams = (data: unknown): Promise<{ success: boolean; workdir: string }> => post('/api/save-params', data)
export const runSetup = (): Promise<ScriptResult> => post('/api/run-setup')
export const runValidation = (type: string): Promise<ScriptResult> => post(`/api/validate/${type}`)

// Add products
export const addProductsLoadParams = (): Promise<LoadParamsResponse> => fetch('/api/add-products/load-params').then(json)
export const addProductsSaveParams = (data: unknown) => post('/api/add-products/save-params', data)
export const addProductsRun = (): Promise<ScriptResult> => post('/api/add-products/run')

// Disable products
export const disableProductsSaveParams = (data: unknown) => post('/api/disable-products/save-params', data)
export const disableProductsRun = (): Promise<ScriptResult> => post('/api/disable-products/run')

// SSO
export const ssoSaveParams = (data: unknown) => post('/api/sso-connection/save-params', data)
export const ssoRun = (): Promise<ScriptResult> => post('/api/sso-connection/run')

// View products
export const fetchTenantProducts = (tenantId: string, branchName: string): Promise<{ products: TenantProduct[]; error?: string }> =>
  post('/api/view-products-by-tenant/fetch', { tenantId, branchName })

// Scan
export const scanTenantsRun = (limit: number, cleanup: boolean): Promise<ScriptResult> =>
  post('/api/scan-tenants/run', { limit, cleanup })
export const scanTenantsResults = (type: string): Promise<{ content: string; error?: string }> =>
  fetch(`/api/scan-tenants/results/${type}`).then(json)

// Rebase / Changelog
export const rebaseClone = (tenantId: string): Promise<CloneResult> => post('/api/rebase/clone', { tenantId })
export const rebaseRunCommand = (repoPath: string, command: string): Promise<ScriptResult> =>
  post('/api/rebase/run-command', { repoPath, command })
export const createChangelog = (repoPath: string, productId: string, jsonContent: string) =>
  post('/api/rebase/create-changelog', { repoPath, productId, jsonContent })

// Readme
export const getReadme = (): Promise<{ content: string }> => fetch('/api/readme').then(json)
