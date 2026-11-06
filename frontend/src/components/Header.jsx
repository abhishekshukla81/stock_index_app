export default function Header({ onToggleTheme }) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="logo" aria-hidden="true"><span /><span /><span /></div>
        <div>
          <h1>Breakout Scanner</h1>
          <p>Global indices &middot; CAR + 30 / 50 / 200 DMA</p>
        </div>
      </div>
      <button className="icon-btn" type="button" onClick={onToggleTheme}
        aria-label="Toggle light / dark theme" title="Toggle theme">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      </button>
    </header>
  );
}
