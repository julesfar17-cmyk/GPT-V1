import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Menu, X, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useI18n } from "@/i18n";

export const Logo = ({ className = "" }) => (
  <Link
    to="/"
    data-testid="nav-logo"
    className={`inline-flex items-end font-display text-lg font-extrabold tracking-tight uppercase text-foreground ${className}`}
  >
    Beatcut<span className="ml-1 mb-0.5 inline-block h-1.5 w-1.5 bg-primary" aria-hidden="true" />
  </Link>
);

const linkCls =
  "font-osd text-[11px] tracking-[0.14em] uppercase text-muted-foreground hover:text-foreground transition-colors";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { lang, setLang } = useI18n();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = async () => {
    navigate("/");
    await logout();
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 h-14 flex items-center justify-between">
        <Logo />

        <nav className="hidden md:flex items-center gap-7">
          {user ? (
            <>
              <Link to="/studio" data-testid="nav-songs-link" className={linkCls}>
                Mes morceaux
              </Link>
              <Link to="/dashboard" data-testid="nav-dashboard-link" className={linkCls}>
                Mon compte
              </Link>
            </>
          ) : (
            <Link to="/login" data-testid="nav-login-link" className={linkCls}>
              Se connecter
            </Link>
          )}
          <button
            onClick={() => setLang(lang === "fr" ? "en" : "fr")}
            data-testid="lang-toggle"
            title={lang === "fr" ? "Switch to English" : "Passer en français"}
            className="w-9 h-9 grid place-items-center rounded-full border border-border font-osd text-[10px] text-muted-foreground hover:text-foreground hover:border-foreground transition-colors"
          >
            {lang === "fr" ? "EN" : "FR"}
          </button>
          {user ? (
            <button
              onClick={handleLogout}
              data-testid="nav-logout-button"
              title="Se déconnecter"
              className="text-muted-foreground hover:text-foreground transition-colors p-1.5"
            >
              <LogOut size={15} />
            </button>
          ) : (
            <Link
              to="/register"
              data-testid="nav-register-link"
              className="inline-flex items-center rounded-full bg-primary text-white font-osd text-[11px] tracking-[0.08em] uppercase px-5 py-2.5 hover:opacity-90 transition-opacity"
            >
              Commence maintenant
            </Link>
          )}
        </nav>

        <button
          className="md:hidden p-2 text-foreground"
          onClick={() => setOpen(!open)}
          data-testid="nav-mobile-toggle"
          aria-label="Menu"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-border bg-background px-5 py-4 flex flex-col gap-4" data-testid="nav-mobile-menu">
          {user ? (
            <>
              <Link to="/studio" onClick={() => setOpen(false)} className="text-sm text-foreground" data-testid="nav-mobile-songs">
                Mes morceaux
              </Link>
              <Link to="/dashboard" onClick={() => setOpen(false)} className="text-sm text-foreground" data-testid="nav-mobile-dashboard">
                Mon compte
              </Link>
              <button onClick={handleLogout} className="text-sm text-muted-foreground text-left" data-testid="nav-mobile-logout">
                Se déconnecter
              </button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={() => setOpen(false)} className="text-sm text-foreground" data-testid="nav-mobile-login">
                Se connecter
              </Link>
              <Link
                to="/register"
                onClick={() => setOpen(false)}
                className="rounded-full bg-primary text-white text-sm font-bold px-5 py-3 text-center"
                data-testid="nav-mobile-register"
              >
                Commence maintenant
              </Link>
            </>
          )}
          <button
            onClick={() => setLang(lang === "fr" ? "en" : "fr")}
            data-testid="nav-mobile-lang"
            className="text-sm text-muted-foreground text-left"
          >
            {lang === "fr" ? "English" : "Français"}
          </button>
        </div>
      )}
    </header>
  );
}
