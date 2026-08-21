import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

const BUST = Date.now(); // anti-cache : garantit la dernière version du studio après chaque déploiement

export default function Studio() {
  const [params] = useSearchParams();
  useEffect(() => {
    // le studio (iframe) a son propre curseur V3 : on masque celui du parent
    document.body.classList.add("no-cur");
    // synchronise le fond + theme-color du document parent avec le thème du studio (bandes blanches/noires iOS)
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
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
    const iv = setInterval(sync, 1500);
    return () => {
      clearInterval(iv);
      document.body.classList.remove("no-cur");
      document.documentElement.style.background = "";
      document.body.style.background = "";
      document.documentElement.style.overflow = "";
      document.body.style.overflow = "";
    };
  }, []);
  const projectId = params.get("project");
  const sessionId = params.get("session_id");
  const qs = [
    projectId ? `project=${projectId}` : null,
    sessionId ? `session_id=${sessionId}` : null,
    `v=${BUST}`,
  ].filter(Boolean).join("&");
  return (
    <div className="w-full" style={{ background: "inherit", height: "100dvh", position: "fixed", inset: 0 }}>
      <iframe
        src={`/studio.html?${qs}`}
        title="Studio BEATCUT"
        data-testid="studio-iframe"
        className="block w-full h-full border-0"
        allow="autoplay; clipboard-write"
      />
    </div>
  );
}
