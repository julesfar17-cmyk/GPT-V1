import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";

const REASON_LABELS = {
  auth_401: "Session expirée / autre appareil",
  project_quota: "Limite de projets",
  empty_overwrite_blocked: "État vide bloqué (course)",
  empty_overwrite: "État vide bloqué (client)",
  network: "Hors ligne",
};

export const SaveFailuresAdmin = () => {
  const [days, setDays] = useState(7);
  const [data, setData] = useState(null);

  const load = useCallback(async (d) => {
    try {
      const { data } = await api.get(`/admin/telemetry/save-failures?days=${d}`);
      setData(data);
    } catch {
      setData(null);
    }
  }, []);
  useEffect(() => { load(days); }, [days, load]);

  return (
    <section className="bg-card border border-border p-6 sm:p-8 mb-8" data-testid="save-failures-section">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display text-lg">Échecs de sauvegarde</h2>
        <select value={days} onChange={(e) => setDays(+e.target.value)} data-testid="save-failures-days-select"
          className="bg-secondary border border-border text-xs px-2 py-1.5">
          <option value={3}>3 jours</option>
          <option value={7}>7 jours</option>
          <option value={30}>30 jours</option>
        </select>
      </div>
      {!data ? (
        <p className="text-sm text-muted-foreground">Chargement…</p>
      ) : data.total === 0 ? (
        <p className="text-sm text-muted-foreground" data-testid="save-failures-empty">Aucun échec de sauvegarde sur la période.</p>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap gap-6">
            <div><p className="font-display text-2xl" data-testid="save-failures-total">{data.total}</p><p className="text-xs text-muted-foreground">échecs</p></div>
            {Object.entries(data.by_reason || {}).map(([k, v]) => (
              <div key={k}><p className="font-display text-2xl">{v}</p><p className="text-xs text-muted-foreground">{REASON_LABELS[k] || k}</p></div>
            ))}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs" data-testid="save-failures-users">
              <thead><tr className="text-muted-foreground text-left"><th className="py-1 pr-3">Utilisateur</th><th className="py-1 pr-3">Échecs</th><th className="py-1 pr-3">Raisons</th><th className="py-1">Dernier</th></tr></thead>
              <tbody>
                {(data.users || []).map((u) => (
                  <tr key={u.email} className="border-t border-border">
                    <td className="py-1.5 pr-3 truncate max-w-[220px]">{u.email}</td>
                    <td className="py-1.5 pr-3 font-osd">{u.count}</td>
                    <td className="py-1.5 pr-3 text-muted-foreground">{Object.entries(u.reasons).map(([k, v]) => `${REASON_LABELS[k] || k} ×${v}`).join(", ")}</td>
                    <td className="py-1.5 text-muted-foreground">{u.last ? new Date(u.last).toLocaleString("fr-FR") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
};
