import { NavLink, Outlet } from 'react-router-dom'

type NavItem = {
  to: string
  label: string
}

type NavGroup = {
  title: string
  items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Observe',
    items: [
      { to: '/', label: 'Dashboard' },
      { to: '/batches', label: 'Batches' },
    ],
  },
  {
    title: 'Build',
    items: [
      { to: '/intake', label: 'Strategy Intake' },
      { to: '/optimization', label: 'Optimization' },
    ],
  },
  {
    title: 'Simulate',
    items: [{ to: '/simulations', label: 'Simulations' }],
  },
  {
    title: 'Govern',
    items: [{ to: '/workflow', label: 'Workflow' }],
  },
]

function NavAnchor({ to, label }: NavItem): JSX.Element {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) => (isActive ? 'app-nav__link app-nav__link--active' : 'app-nav__link')}
    >
      {label}
    </NavLink>
  )
}

export default function AppShell(): JSX.Element {
  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar">
        <div className="brand-mark">
          <p className="brand-mark__eyebrow">CBOT FARM</p>
          <h1 className="brand-mark__title">Strategy Lab</h1>
          <p className="brand-mark__copy">Research, iterate, validate, and govern trading systems.</p>
        </div>

        <nav className="app-nav" aria-label="Primary">
          {NAV_GROUPS.map((group) => (
            <div className="app-nav__group" key={group.title}>
              <p className="app-nav__title">{group.title}</p>
              {group.items.map((item) => (
                <NavAnchor key={`${group.title}-${item.to}`} to={item.to} label={item.label} />
              ))}
            </div>
          ))}
        </nav>

        <div className="shell-note">
          <p className="shell-note__label">Current focus</p>
          <p className="shell-note__value">UI refresh foundation and operator console quality.</p>
        </div>
      </aside>

      <div className="app-shell__main">
        <div className="app-shell__topbar">
          <div>
            <p className="topbar__eyebrow">Operator Console</p>
            <p className="topbar__title">Multi-market strategy research workstation</p>
          </div>
          <div className="topbar__status">
            <span className="status-dot" />
            <span>API-first workspace</span>
          </div>
        </div>

        <div className="app-shell__content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
