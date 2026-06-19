import type { SVGProps } from 'react'

/** Ícones em linha (stroke), consistentes em todo o app. */
function Base({
  children,
  size = 18,
  ...props
}: SVGProps<SVGSVGElement> & { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  )
}

export const IconHome = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M3 11l9-8 9 8" />
    <path d="M5 10v10h5v-6h4v6h5V10" />
  </Base>
)
export const IconInvest = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M4 19V5" />
    <path d="M4 19h16" />
    <path d="M8 15l3-4 3 2 4-7" />
  </Base>
)
export const IconStatement = (p: { size?: number }) => (
  <Base {...p}>
    <line x1="9" y1="7" x2="20" y2="7" />
    <line x1="9" y1="12" x2="20" y2="12" />
    <line x1="9" y1="17" x2="20" y2="17" />
    <circle cx="4.5" cy="7" r="1.3" />
    <circle cx="4.5" cy="12" r="1.3" />
    <circle cx="4.5" cy="17" r="1.3" />
  </Base>
)
export const IconTarget = (p: { size?: number }) => (
  <Base {...p}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="5" />
    <circle cx="12" cy="12" r="1.4" />
  </Base>
)
export const IconSettings = (p: { size?: number }) => (
  <Base {...p}>
    <line x1="4" y1="8" x2="20" y2="8" />
    <line x1="4" y1="16" x2="20" y2="16" />
    <circle cx="9" cy="8" r="2.6" fill="var(--panel)" />
    <circle cx="15" cy="16" r="2.6" fill="var(--panel)" />
  </Base>
)
export const IconEye = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
  </Base>
)
export const IconEyeOff = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M9.9 4.2A9.5 9.5 0 0 1 12 4c6 0 10 7 10 7a17 17 0 0 1-3.3 3.9" />
    <path d="M6.6 6.6A17 17 0 0 0 2 11s4 7 10 7a9.4 9.4 0 0 0 4.5-1.1" />
    <line x1="2" y1="2" x2="22" y2="22" />
  </Base>
)
export const IconSun = (p: { size?: number }) => (
  <Base {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </Base>
)
export const IconMoon = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
  </Base>
)
export const IconPower = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M12 4v8" />
    <path d="M7.5 6.5a7 7 0 1 0 9 0" />
  </Base>
)
export const IconBolt = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" />
  </Base>
)
export const IconSearch = (p: { size?: number }) => (
  <Base {...p}>
    <circle cx="11" cy="11" r="7" />
    <line x1="21" y1="21" x2="16.5" y2="16.5" />
  </Base>
)
export const IconArrowIn = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M17 7L7 17" />
    <path d="M17 14V7H10" />
  </Base>
)
export const IconArrowOut = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M7 17L17 7" />
    <path d="M8 7h9v9" />
  </Base>
)
export const IconRefresh = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M21 12a9 9 0 1 1-2.6-6.4" />
    <path d="M21 4v5h-5" />
  </Base>
)
export const IconTrash = (p: { size?: number }) => (
  <Base {...p}>
    <path d="M4 7h16" />
    <path d="M9 7V5h6v2" />
    <path d="M6 7l1 13h10l1-13" />
  </Base>
)
export const IconPlus = (p: { size?: number }) => (
  <Base {...p}>
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </Base>
)
