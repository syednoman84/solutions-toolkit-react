export interface Product {
  type: string
  name: string
}

export interface Params {
  destination_repo_github_url?: string
  'tenant-domain'?: string
  'tenant-id'?: string
  template_vars_tag?: string
  pr_title?: string
  branchName?: string
  commit_message?: string
  [key: string]: string | undefined
}

export interface LoadParamsResponse {
  params: Params
  products: Product[]
  error?: string
}

export interface ScriptResult {
  stdout?: string
  stderr?: string
  returncode?: number
  error?: string
}

export interface SSOConnection {
  displayName: string
  connectionName: string
  ssoUrl: string
}

export interface TenantProduct {
  productId: string
  productName: string
  productType: string
  policy: string
  selfServiceManaged: boolean | string
}

export interface CloneResult {
  repoPath: string
  repoName: string
  products: string[]
  error?: string
}

export type ProgressStep = {
  percent: number
  text: string
}
