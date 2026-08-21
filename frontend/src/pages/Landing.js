import { useCallback, useEffect } from "react";

const BUST = Date.now(); // anti-cache : garantit la dernière version de la landing après chaque déploiement

export default function Landing() {
  useEffect(() => {
    const sync = () => {
      let t = "dark";
      try { t = localStorage.getItem("bc_theme") || "dark"; } catch {}
      const c = t === "light" ? "#ffffff" : "#000000";
      document.documentElement.style.background = c;
      document.body.style.background = c;
      let m = document.querySelector('meta[name="theme-color"]');
      if (!m) { m = document.createElement("meta"); m.name = "theme-color"; document.head.appendChild(m); }
      m.setAttribute("content", c);
    };
    sync();
    const iv = setInterval(sync, 1500);
    return () => {
      clearInterval(iv);
      document.documentElement.style.background = "";
      document.body.style.background = "";
    };
  }, []);
  useEffect(() => {
    // la landing (iframe) a son propre curseur V3 : on masque celui du parent
    document.body.classList.add("no-cur");
    return () => document.body.classList.remove("no-cur");
  }, []);
  const onLoad = useCallback((e) => {
    try {
      const doc = e.target.contentDocument;
      doc.querySelectorAll('a[href^="/"]').forEach((a) => (a.target = "_top"));
    } catch {}
  }, []);
  return (
    <iframe
      src={`/landing.html?v=${BUST}`}
      title="BeatCut"
      data-testid="landing-iframe"
      onLoad={onLoad}
      style={{ position: "fixed", inset: 0, width: "100%", height: "100%", border: "none", background: "transparent" }}
    />
  );
}
