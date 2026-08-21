import { Link } from "react-router-dom";
import { Logo } from "@/components/Navbar";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 py-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Logo />
        <span className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <Link to="/cgv" data-testid="footer-cgv-link" className="hover:text-foreground transition-colors">CGV</Link>
          <Link to="/confidentialite" data-testid="footer-privacy-link" className="hover:text-foreground transition-colors">Confidentialité</Link>
          <Link to="/mentions-legales" data-testid="footer-mentions-link" className="hover:text-foreground transition-colors">Mentions légales</Link>
          <a href="mailto:contact@beat-cut.com" data-testid="footer-contact-link" className="hover:text-foreground transition-colors">contact@beat-cut.com</a>
        </span>
      </div>
    </footer>
  );
}
