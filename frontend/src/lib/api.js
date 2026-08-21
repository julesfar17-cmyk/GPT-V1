import axios from "axios";

// Same-origin d'abord : si la page n'est pas servie depuis REACT_APP_BACKEND_URL
// (ex. www.beat-cut.com vs beat-cut.com), on passe en chemin relatif pour que les
// cookies httpOnly suivent toujours (l'ingress route /api/* sur chaque hôte).
const backendOrigin = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
const sameOrigin = typeof window !== "undefined" && window.location.origin === backendOrigin;
const api = axios.create({
  baseURL: sameOrigin ? `${backendOrigin}/api` : "/api",
  withCredentials: true,
});

// Cloudflare/proxy : une connexion keep-alive fermée côté serveur peut produire une réponse
// vide ou un 520 intermittent → un seul retry automatique sur les erreurs de transport.
api.interceptors.response.use(null, async (error) => {
  const cfg = error.config || {};
  const status = error.response?.status;
  const transient = !error.response || status === 502 || status === 504 || (status >= 520 && status <= 527);
  const safe = (cfg.method || "get").toLowerCase() === "get" || (cfg.url || "").startsWith("/auth/");
  if (transient && safe && !cfg._retried) {
    cfg._retried = true;
    await new Promise((r) => setTimeout(r, 800));
    return api(cfg);
  }
  return Promise.reject(error);
});

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Une erreur est survenue. Réessaie.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default api;
