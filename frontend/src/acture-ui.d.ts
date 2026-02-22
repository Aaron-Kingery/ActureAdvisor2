declare module '@acture/ui' {
  import { ReactNode, FC } from 'react'

  export interface PlatformUser {
    displayName: string
    email: string
    role: string
    initials?: string
    avatarUrl?: string
  }

  export interface AppTab {
    id: string
    label: string
    href: string
    disabled?: boolean
  }

  export interface PlatformShellProps {
    children: ReactNode
    activeApp?: string
    user?: PlatformUser | null
    notifications?: number
    apps?: AppTab[]
    onLogout?: () => void
    logoHref?: string
  }

  export const PlatformShell: FC<PlatformShellProps>

  export interface AuthProviderProps {
    children: ReactNode
    clientId: string
    tenantId: string
    redirectUri?: string
    scopes?: string[]
  }

  export const AuthProvider: FC<AuthProviderProps>

  export interface RoleGateProps {
    children: ReactNode
    role: string
    fallback?: ReactNode
  }

  export const RoleGate: FC<RoleGateProps>

  export interface Column<T = any> {
    key: string
    header: string
    render?: (row: T) => ReactNode
  }

  export interface DataTableProps<T = any> {
    columns: Column<T>[]
    data: T[]
    onRowClick?: (row: T) => void
  }

  export const DataTable: FC<DataTableProps>
  export const ToastProvider: FC<{ children: ReactNode }>
  export function useToast(): {
    success: (msg: string) => void
    error: (msg: string) => void
    warning: (msg: string) => void
    info: (msg: string) => void
  }
  export function useAuth(): any
}

declare module '@acture/ui/styles' {}
