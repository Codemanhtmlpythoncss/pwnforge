import { useEffect, useState } from "react";
import { api } from "../api";
import { Panel, Spinner, Empty } from "../ui";
import { Logo } from "../logo";

type Cert = { serial: string; path_id: string; path_title: string; recipient: string; issued_at: string };

export default function Certificates() {
  const [items, setItems] = useState<Cert[] | null>(null);
  const [view, setView] = useState<Cert | null>(null);
  useEffect(() => { api.get("/api/certificates").then(r => setItems(r.items)).catch(() => setItems([])); }, []);

  if (view) return <CertificateView cert={view} onBack={() => setView(null)} />;
  if (items === null) return <Spinner />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Certificates</h1>
        <div className="text-muted text-sm mt-1">Earned by completing a learning path end to end.</div>
      </div>
      {!items.length ? (
        <Empty msg="No certificates yet — finish a learning path to earn one." />
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {items.map(c => (
            <Panel key={c.serial} hover>
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-xl">🎓</div>
                  <div className="font-semibold mt-1">{c.path_title}</div>
                  <div className="text-muted text-xs mt-0.5 font-mono">{c.serial} · {new Date(c.issued_at).toLocaleDateString()}</div>
                </div>
                <button className="btn btn-primary text-sm" onClick={() => setView(c)}>View</button>
              </div>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}

function CertificateView({ cert, onBack }: { cert: Cert; onBack: () => void }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 print:hidden">
        <button className="btn text-sm" onClick={onBack}>← Back</button>
        <button className="btn btn-primary text-sm" onClick={() => window.print()}>Print / Save as PDF</button>
      </div>
      <div className="cert-sheet mx-auto max-w-3xl rounded-2xl p-10 text-center border-2 border-brand bg-[var(--panel)]"
        style={{ boxShadow: "0 0 0 1px var(--line) inset" }}>
        <div className="flex items-center justify-center gap-2 mb-6"><Logo size={34} /><span className="text-xl font-bold tracking-wide">PwnForge</span></div>
        <div className="text-muted uppercase tracking-[0.3em] text-xs">Certificate of Completion</div>
        <div className="text-sm text-muted mt-8">This certifies that</div>
        <div className="text-3xl font-bold mt-2">{cert.recipient}</div>
        <div className="text-sm text-muted mt-6">has successfully completed the learning path</div>
        <div className="text-2xl font-semibold text-brand mt-2">{cert.path_title}</div>
        <div className="flex items-center justify-between mt-12 text-xs text-muted">
          <div className="text-left">
            <div className="font-mono">{cert.serial}</div>
            <div>Verify at /api/certificates/{cert.serial}</div>
          </div>
          <div className="text-right">
            <div className="font-semibold text-ink">{new Date(cert.issued_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}</div>
            <div>Date issued</div>
          </div>
        </div>
      </div>
    </div>
  );
}
