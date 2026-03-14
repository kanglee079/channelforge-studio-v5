
type Props = {
  page: string
  onChange: (page: string) => void
}

const items = [
  ['dashboard', 'Dashboard'],
  ['channels', 'Channels'],
  ['jobs', 'Jobs & Queue'],
  ['content', 'Content Studio'],
  ['trends', 'Trend Radar'],
  ['settings', 'Settings']
]

export default function Sidebar({ page, onChange }: Props) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-badge">YA</div>
        <div>
          <h1>YouTube Auto Studio</h1>
          <p>V4 Admin Console</p>
        </div>
      </div>
      <nav className="nav">
        {items.map(([key, label]) => (
          <button
            key={key}
            className={page === key ? 'nav-item active' : 'nav-item'}
            onClick={() => onChange(key)}
          >
            {label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
