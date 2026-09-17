import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useI18n } from "@/i18n";

export const COOKIE_KEY = "bc_cookie_consent";

const TXT = {
  fr: {
    title: "Cookies",
    body: "BEATCUT utilise des cookies indispensables (connexion, sauvegarde de tes projets) et, si tu l'acceptes, des mesures d'audience anonymes pour améliorer le studio.",
    more: "En savoir plus",
    refuse: "Refuser",
    accept: "Tout accepter",
  },
  en: {
    title: "Cookies",
    body: "BEATCUT uses essential cookies (login, saving your projects) and, if you accept, anonymous audience measurement to improve the studio.",
    more: "Learn more",
    refuse: "Refuse",
    accept: "Accept all",
  },
};

export function readCookieConsent() {
  try { return localStorage.getItem(COOKIE_KEY); } catch { return null; }
}

export default function CookieBanner() {
  const { lang } = useI18n();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!readCookieConsent()) {
      const id = setTimeout(() => setOpen(true), 600);
      return () => clearTimeout(id);
    }
  }, []);
  if (!open) return null;
  const t = TXT[lang] || TXT.fr;
  const choose = (v) => {
    try { localStorage.setItem(COOKIE_KEY, JSON.stringify({ v, at: new Date().toISOString() })); } catch {}
    setOpen(false);
  };
  return (
    <div role="dialog" aria-live="polite" aria-label={t.title} data-testid="cookie-banner"
      className="fixed z-[9990] left-3 right-3 bottom-3 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[420px]
                 bg-black border border-[#2a2a2a] text-[#d9d9d9] p-4 sm:p-5 animate-in slide-in-from-bottom-4 fade-in duration-300"
      style={{ fontFamily: "'Space Grotesk', sans-serif", paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}>
      <div className="flex items-start gap-3">
        <span aria-hidden className="mt-[3px] inline-block w-2 h-2 bg-[#fc1c46] shrink-0" />
        <div className="min-w-0">
          <p className="text-white font-bold uppercase tracking-[0.12em] text-[11px] mb-1">{t.title}</p>
          <p className="text-[13px] leading-relaxed text-[#b3b3b3]">
            {t.body}{" "}
            <Link to="/confidentialite" className="underline underline-offset-2 text-white hover:text-[#fc1c46]" data-testid="cookie-more-link">{t.more}</Link>
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 sm:flex sm:justify-end">
        <button type="button" onClick={() => choose("refused")} data-testid="cookie-refuse-btn"
          className="h-11 sm:h-10 px-4 border border-[#3a3a3e] text-white text-[12px] font-semibold uppercase tracking-[0.06em] rounded-full hover:border-white transition-colors">
          {t.refuse}
        </button>
        <button type="button" onClick={() => choose("accepted")} data-testid="cookie-accept-btn"
          className="h-11 sm:h-10 px-5 bg-[#fc1c46] text-white text-[12px] font-bold uppercase tracking-[0.06em] rounded-full hover:bg-[#e0153c] transition-colors">
          {t.accept}
        </button>
      </div>
    </div>
  );
}
