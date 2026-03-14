export default function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="page">
      <div className="page-head">
        <h2>{name.charAt(0).toUpperCase() + name.slice(1)}</h2>
        <p className="text-muted">This module will be available in Phase 2.</p>
      </div>
      <div className="placeholder-box">
        <span className="placeholder-icon">🚧</span>
        <h3>Coming Soon</h3>
        <p>This feature is planned for the next development phase.</p>
      </div>
    </div>
  );
}
