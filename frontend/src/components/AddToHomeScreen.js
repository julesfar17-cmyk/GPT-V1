import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Share, SquarePlus, X } from "lucide-react";
import { useI18n } from "@/i18n";
import { readCookieConsent } from "@/components/CookieBanner";

const KEY = "bc_a2hs_snooze";
const SNOOZE_DAYS = 14;
const PAGES = ["/dashboard", "/projects", "/studio"];

const TXT = {
  fr: {
    title: "BEATCUT sur ton écran d'accueil",
    ios: ["Touche", "Partager", "puis", "Sur l'écran d'accueil", "pour ouvrir BEATCUT comme une app, en plein écran."],
    android: "Installe BEATCUT pour l'ouvrir comme une app, en plein écran.",
    install: "Installer",
    later: "Plus tard",
  },
  en: {
    title: "BEATCUT on your home screen",
    ios: ["Tap", "Share", "then", "Add to Home Screen", "to open BEATCUT like an app, full screen."],
    android: "Install BEATCUT to open it like an app, full screen.",
    install: "Install",
    later: "Later",
  },
};

function isStandalone() {
  return window.navigator.standalone === true || window.matchMedia("(display-mode: standalone)").matches;
}
function snoozed() {
  try { const v = +localStorage.getItem(KEY); return v && Date.now() - v < SNOOZE_DAYS * 864e5; } catch { return false; }
}

export default function AddToHomeScreen() {
  const { lang } = useI18n();
  const { pathname } = useLocation();
  const [mode, setMode] = useState(null);   // 'ios' | 'android'
  const [promptEvt, setPromptEvt] = useState(null);

  useEffect(() => {
    const ua = navigator.userAgent;
    const ios = /iPhone|iPad|iPod/i.test(ua) && !/CriOS|FxiOS|EdgiOS/i.test(ua);
    if (ios && !isStandalone()) setMode("ios");
    const onPrompt = (e) => { e.preventDefault(); setPromptEvt(e); setMode("android"); };
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!mode || snoozed() || isStandalone() || !PAGES.some((p) => pathname.startsWith(p))) { setOpen(false); return; }
    const tick = setInterval(() => { if (readCookieConsent() && !document.querySelector('[data-testid="cookie-banner"]')) { setOpen(true); clearInterval(tick); } }, 800);
    return () => clearInterval(tick);
  }, [mode, pathname]);

  if (!open || !mode) return null;
  const t = TXT[lang] || TXT.fr;
  const close = () => { try { localStorage.setItem(KEY, String(Date.now())); } catch {} setOpen(false); };
  const install = async () => {
    if (promptEvt) { try { await promptEvt.prompt(); } catch {} }
    close();
  };

  return (
    <div role="dialog" aria-label={t.title} data-testid="a2hs-banner"
      className="fixed z-[9985] left-3 right-3 bottom-3 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[400px]
                 bg-black border border-[#2a2a2a] text-[#d9d9d9] p-4 animate-in slide-in-from-bottom-4 fade-in duration-300"
      style={{ fontFamily: "'Space Grotesk', sans-serif", paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}>
      <div className="flex items-start gap-3">
        <img src="/favicon-192.png" alt="" width="44" height="44" className="shrink-0 border border-[#2a2a2a]" />
        <div className="min-w-0 flex-1">
          <p className="text-white font-bold uppercase tracking-[0.12em] text-[11px] mb-1">{t.title}</p>
          {mode === "ios" ? (
            <p className="text-[13px] leading-relaxed text-[#b3b3b3]" data-testid="a2hs-ios-steps">
              {t.ios[0]} <span className="inline-flex items-center gap-1 text-white"><Share size={14} strokeWidth={2} />{t.ios[1]}</span> {t.ios[2]}{" "}
              <span className="inline-flex items-center gap-1 text-white"><SquarePlus size={14} strokeWidth={2} />« {t.ios[3]} »</span> {t.ios[4]}
            </p>
          ) : (
            <p className="text-[13px] leading-relaxed text-[#b3b3b3]">{t.android}</p>
          )}
        </div>
        <button type="button" onClick={close} aria-label={t.later} data-testid="a2hs-close-btn"
          className="shrink-0 w-9 h-9 -mt-1 -mr-1 grid place-items-center text-[#7a7a7a] hover:text-white transition-colors">
          <X size={16} />
        </button>
      </div>
      <div className="mt-3 flex justify-end gap-2">
        <button type="button" onClick={close} data-testid="a2hs-later-btn"
          className="h-10 px-4 border border-[#3a3a3e] text-white text-[12px] font-semibold uppercase tracking-[0.06em] rounded-full hover:border-white transition-colors">
          {t.later}
        </button>
        {mode === "android" && (
          <button type="button" onClick={install} data-testid="a2hs-install-btn"
            className="h-10 px-5 bg-[#fc1c46] text-white text-[12px] font-bold uppercase tracking-[0.06em] rounded-full hover:bg-[#e0153c] transition-colors">
            {t.install}
          </button>
        )}
      </div>
    </div>
  );
}
