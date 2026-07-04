// "Your plan is ready" success banner (mock 1f) — shown after generation lands
// the spec. "Download all" is the PDF export seam (D5); the handler is injected.

export function PlanReadyBanner({
  onDownloadAll,
}: {
  onDownloadAll: () => void;
}) {
  return (
    <div className="mech-ready" role="status" style={{ marginTop: 24 }}>
      <div className="mech-ready__mark" aria-hidden="true">
        ✓
      </div>
      <div style={{ flex: 1 }}>
        <div className="mech-ready__title">Your plan is ready</div>
        <div className="mech-ready__sub">
          Saved to this project — revisit it any time from My Mechanic.
        </div>
      </div>
      <button type="button" className="mech-btn mech-btn--success" onClick={onDownloadAll}>
        ↓ Download all
      </button>
    </div>
  );
}
