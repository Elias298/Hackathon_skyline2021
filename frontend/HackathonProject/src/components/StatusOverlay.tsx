import "./StatusOverlay.css";

export function Loader({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="status-overlay">
      <div className="spinner" />
      <span>{text}</span>
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="status-overlay error">
      <span className="error-icon">⚠</span>
      <span>{message}</span>
    </div>
  );
}
