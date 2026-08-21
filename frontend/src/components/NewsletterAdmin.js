import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import api, { formatApiErrorDetail } from "@/lib/api";

export function NewsletterAdmin() {
  const [subject, setSubject] = useState("");
  const [mode, setMode] = useState("editor");
  const [content, setContent] = useState("");
  const [previewHtml, setPreviewHtml] = useState(null);
  const [testEmail, setTestEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [armed, setArmed] = useState(false);

  const [q, setQ] = useState("");
  const [subs, setSubs] = useState(null);
  const [campaigns, setCampaigns] = useState([]);

  const loadSubs = useCallback(async (query = "") => {
    try {
      const { data } = await api.get("/admin/newsletter/subscribers", { params: { q: query } });
      setSubs(data);
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail));
    }
  }, []);

  const loadCampaigns = useCallback(async () => {
    try {
      const { data } = await api.get("/admin/newsletter/campaigns");
      setCampaigns(data.campaigns || []);
    } catch (e) { /* silencieux */ }
  }, []);

  useEffect(() => { loadSubs(); loadCampaigns(); }, [loadSubs, loadCampaigns]);

  useEffect(() => {
    const t = setTimeout(() => loadSubs(q), 350);
    return () => clearTimeout(t);
  }, [q, loadSubs]);

  const sending = campaigns.some((c) => c.status === "sending");
  useEffect(() => {
    if (!sending) return;
    const iv = setInterval(loadCampaigns, 4000);
    return () => clearInterval(iv);
  }, [sending, loadCampaigns]);

  const doPreview = async () => {
    if (!subject.trim() || !content.trim()) { toast.error("Sujet et contenu requis"); return; }
    try {
      const { data } = await api.post("/admin/newsletter/preview", { subject, mode, content });
      setPreviewHtml(data.html);
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail));
    }
  };

  const sendTest = async () => {
    if (!subject.trim() || !content.trim() || !testEmail.trim()) { toast.error("Sujet, contenu et email de test requis"); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/admin/newsletter/send", { subject, mode, content, test_email: testEmail });
      data.sent ? toast.success(`Test envoyé à ${testEmail}`) : toast.error("Envoi test échoué (clé Resend ?)");
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const sendAll = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/newsletter/send", { subject, mode, content });
      toast.success(`Envoi lancé vers ${data.recipients} destinataire(s) — suivi en bas de page`);
      setArmed(false);
      loadCampaigns();
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const toggleSub = async (email, subscribed) => {
    try {
      await api.post("/admin/newsletter/subscription", { email, subscribed });
      setSubs((prev) => prev && {
        ...prev,
        total_subscribed: prev.total_subscribed + (subscribed ? 1 : -1),
        users: prev.users.map((u) => (u.email === email ? { ...u, subscribed } : u)),
      });
      toast.success(subscribed ? `${email} réinscrit` : `${email} retiré de la liste`);
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail));
    }
  };

  return (
    <div data-testid="admin-newsletter-tab">
      <section className="bg-card border border-border p-6 sm:p-8 mb-8" data-testid="newsletter-compose-section">
        <h2 className="font-display text-lg font-bold mb-2">Rédiger une newsletter</h2>
        <p className="text-xs text-muted-foreground mb-5 max-w-2xl">
          L'email est envoyé à tous les inscrits qui n'ont pas été décochés. Un lien de désinscription et un
          pixel de suivi d'ouverture sont ajoutés automatiquement à chaque email.
        </p>

        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setMode("editor")}
            data-testid="newsletter-mode-editor"
            className={`px-4 py-2 text-xs font-osd tracking-wider border transition-colors ${mode === "editor" ? "border-primary text-primary" : "border-border text-muted-foreground hover:border-foreground"}`}
          >
            ÉDITEUR (DA BEATCUT)
          </button>
          <button
            onClick={() => setMode("html")}
            data-testid="newsletter-mode-html"
            className={`px-4 py-2 text-xs font-osd tracking-wider border transition-colors ${mode === "html" ? "border-primary text-primary" : "border-border text-muted-foreground hover:border-foreground"}`}
          >
            IMPORTER DU HTML
          </button>
        </div>

        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Sujet de l'email"
          data-testid="newsletter-subject-input"
          className="w-full bg-background border border-border px-4 py-3 text-sm focus:border-[#fc1c46] focus:outline-none mb-3"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={mode === "html" ? 14 : 10}
          placeholder={mode === "html"
            ? "Colle ici ton code HTML complet — il sera envoyé tel quel."
            : "Écris ton message. Chaque ligne devient un paragraphe. Il sera mis en forme dans le gabarit BEATCUT (fond noir, logo, pilules)."}
          data-testid="newsletter-content-input"
          className={`w-full bg-background border border-border px-4 py-3 text-sm focus:border-[#fc1c46] focus:outline-none mb-4 ${mode === "html" ? "font-mono text-xs" : ""}`}
        />

        <div className="flex flex-wrap gap-3 items-center mb-4">
          <button onClick={doPreview} data-testid="newsletter-preview-button"
            className="border border-border px-4 py-2.5 text-xs font-osd tracking-wider hover:border-foreground transition-colors">
            APERÇU
          </button>
          <input
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            placeholder="email pour le test"
            data-testid="newsletter-test-email-input"
            className="bg-background border border-border px-3 py-2.5 text-sm w-56 focus:border-[#fc1c46] focus:outline-none"
          />
          <button onClick={sendTest} disabled={busy} data-testid="newsletter-send-test-button"
            className="border border-border px-4 py-2.5 text-xs font-osd tracking-wider hover:border-foreground transition-colors disabled:opacity-50">
            ENVOYER UN TEST
          </button>
        </div>

        {previewHtml && (
          <div className="mb-5 border border-border" data-testid="newsletter-preview-frame">
            <p className="font-osd text-[11px] tracking-wider text-muted-foreground px-3 py-2 border-b border-border">APERÇU DE L'EMAIL</p>
            <iframe title="preview" srcDoc={previewHtml} sandbox="" className="w-full bg-black" style={{ height: 480 }} />
          </div>
        )}

        {!armed ? (
          <button
            onClick={() => {
              if (!subject.trim() || !content.trim()) { toast.error("Sujet et contenu requis"); return; }
              setArmed(true);
            }}
            data-testid="newsletter-send-all-button"
            className="bg-primary text-white font-bold px-6 py-3 hover:opacity-90 transition-colors"
          >
            Envoyer à toute la base{subs ? ` (${subs.total_subscribed} inscrits)` : ""}
          </button>
        ) : (
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-primary">
              Confirmer l'envoi à {subs?.total_subscribed ?? "?"} destinataire(s) ? Irréversible.
            </span>
            <button onClick={sendAll} disabled={busy} data-testid="newsletter-send-all-confirm"
              className="bg-primary text-white px-5 py-2.5 text-xs font-bold disabled:opacity-50">
              {busy ? "…" : "OUI, ENVOYER"}
            </button>
            <button onClick={() => setArmed(false)} className="text-xs text-muted-foreground underline">Annuler</button>
          </div>
        )}
      </section>

      <section className="bg-card border border-border p-6 sm:p-8 mb-8" data-testid="newsletter-campaigns-section">
        <h2 className="font-display text-lg font-bold mb-2">Campagnes envoyées</h2>
        <p className="text-xs text-muted-foreground mb-4">
          Le taux d'ouverture est mesuré via un pixel invisible (certaines boîtes mail le bloquent — le taux réel est souvent un peu plus haut).
        </p>
        {!campaigns.length ? (
          <p className="text-sm text-muted-foreground" data-testid="newsletter-campaigns-empty">Aucune campagne pour l'instant.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-osd text-[11px] text-muted-foreground border-b border-border">
                  <th className="py-2 pr-4">DATE</th>
                  <th className="py-2 pr-4">SUJET</th>
                  <th className="py-2 pr-4">DESTINATAIRES</th>
                  <th className="py-2 pr-4">ENVOYÉS</th>
                  <th className="py-2 pr-4">OUVERTURES</th>
                  <th className="py-2 pr-4">TAUX D'OUVERTURE</th>
                  <th className="py-2">STATUT</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c, i) => (
                  <tr key={c.campaign_id} className="border-b border-border/50" data-testid={`newsletter-campaign-row-${i}`}>
                    <td className="py-2 pr-4">{c.created_at ? new Date(c.created_at).toLocaleDateString("fr-FR") : "—"}</td>
                    <td className="py-2 pr-4 max-w-[240px] truncate">{c.subject}</td>
                    <td className="py-2 pr-4">{c.recipients}</td>
                    <td className="py-2 pr-4">{c.sent}{c.failed ? <span className="text-primary"> ({c.failed} échec)</span> : ""}</td>
                    <td className="py-2 pr-4">{c.opens}</td>
                    <td className="py-2 pr-4 font-osd text-[#fc1c46]">{c.open_rate != null ? `${c.open_rate} %` : "—"}</td>
                    <td className="py-2">
                      {c.status === "sending"
                        ? <span className="text-foreground animate-pulse">Envoi en cours…</span>
                        : <span className="text-muted-foreground">Terminé</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="bg-card border border-border p-6 sm:p-8" data-testid="newsletter-subscribers-section">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="font-display text-lg font-bold">
            Liste de diffusion{subs ? ` — ${subs.total_subscribed} inscrit(s) sur ${subs.total}` : ""}
          </h2>
        </div>
        <p className="text-xs text-muted-foreground mb-4">
          Décoche un email pour l'exclure des prochains envois. Les utilisateurs désinscrits via le lien dans l'email apparaissent décochés ici.
        </p>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Rechercher un email ou un nom…"
          data-testid="newsletter-search-input"
          className="w-full max-w-md bg-background border border-border px-4 py-2.5 text-sm focus:border-[#fc1c46] focus:outline-none mb-4"
        />
        <div className="overflow-x-auto max-h-[420px] overflow-y-auto border border-border" data-testid="newsletter-subscribers-table">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-card">
              <tr className="font-osd text-[11px] tracking-wider text-muted-foreground border-b border-border">
                <th className="text-left px-3 py-2 w-10">ENVOI</th>
                <th className="text-left px-3 py-2">EMAIL</th>
                <th className="text-left px-3 py-2">NOM</th>
                <th className="text-left px-3 py-2">INSCRIT LE</th>
              </tr>
            </thead>
            <tbody>
              {(subs?.users || []).map((u) => (
                <tr key={u.email} className={`border-b border-border/50 ${!u.subscribed ? "opacity-50" : ""}`}>
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={u.subscribed}
                      onChange={(e) => toggleSub(u.email, e.target.checked)}
                      data-testid={`newsletter-sub-checkbox-${u.email}`}
                      className="accent-[#fc1c46] cursor-pointer"
                    />
                  </td>
                  <td className="px-3 py-2">{u.email}</td>
                  <td className="px-3 py-2 text-muted-foreground">{u.name || "—"}</td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString("fr-FR") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
