import { useState } from "react";
import type { ReactNode } from "react";
import { frontendUrls } from "@tanim/config";
import { messages, phase5Messages } from "@tanim/i18n";
import type { AuthUser, Language } from "@tanim/types";
import { navigate } from "./navigation";

type PlatformShellProps = {
  language: Language;
  onLanguageChange: (value: Language) => void;
  user: AuthUser;
  onLogout: () => void;
  children: ReactNode;
};

export function InternalLink({
  href,
  children,
  className,
}: {
  href: string;
  children: ReactNode;
  className?: string;
}) {
  const currentPath = window.location.pathname;
  const active = href === "/dashboard"
    ? currentPath === "/dashboard" || currentPath === "/cooperative"
    : currentPath === href || currentPath.startsWith(`${href}/`);
  return (
    <a
      aria-current={active ? "page" : undefined}
      className={className}
      href={href}
      onClick={(event) => {
        event.preventDefault();
        navigate(href);
      }}
    >
      {children}
    </a>
  );
}

function LanguageSelector({
  language,
  onChange,
}: {
  language: Language;
  onChange: (value: Language) => void;
}) {
  const copy = messages[language];
  return (
    <label className="language-control" htmlFor="platform-language">
      <span>{copy.languageLabel}</span>
      <select
        id="platform-language"
        value={language}
        onChange={(event) => onChange(event.target.value as Language)}
      >
        <option value="en">{copy.languageOptions.en}</option>
        <option value="tl">{copy.languageOptions.tl}</option>
      </select>
    </label>
  );
}

export function PlatformShell({
  language,
  onLanguageChange,
  user,
  onLogout,
  children,
}: PlatformShellProps) {
  const copy = phase5Messages[language];
  const [menuOpen, setMenuOpen] = useState(false);
  const roleLabel = user.role === "cooperative" ? copy.roleCooperative : copy.roleFarmer;

  return (
    <div className="platform-app-shell">
      <header className="platform-header">
        <a className="brand-link" href="/dashboard" onClick={(event) => {
          event.preventDefault();
          navigate("/dashboard");
        }}>
          TANIM
        </a>
        <div className="platform-header-actions">
          <span className="user-badge">{user.display_name} · {roleLabel}</span>
          <LanguageSelector language={language} onChange={onLanguageChange} />
          <InternalLink className="header-settings" href="/settings">{copy.navSettings}</InternalLink>
          <button className="quiet-button" type="button" onClick={onLogout}>
            {copy.logout}
          </button>
        </div>
      </header>

      <nav className="desktop-nav" aria-label={copy.navLabel}>
        <InternalLink href="/dashboard">{copy.navDashboard}</InternalLink>
        <InternalLink href="/plans">{copy.navPlans}</InternalLink>
        <InternalLink href="/crops">{copy.navCrops}</InternalLink>
        <InternalLink href="/map">{copy.navMap}</InternalLink>
        <InternalLink href="/weather">{copy.navWeather}</InternalLink>
        <a href={frontendUrls.docs} target="_blank" rel="noreferrer">{copy.navHelp}</a>
      </nav>

      <main className="platform-main">{children}</main>

      <nav className="mobile-nav" aria-label={copy.navLabel}>
        <InternalLink href="/dashboard">{copy.navDashboard}</InternalLink>
        <InternalLink href="/plans">{copy.navPlans}</InternalLink>
        <InternalLink className="mobile-add-plan" href="/plans/new">{copy.navAddPlan}</InternalLink>
        <InternalLink href="/explore">{copy.navExplore}</InternalLink>
        <button
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? copy.closeMenu : copy.navMenu}
        </button>
      </nav>
      {menuOpen ? (
        <div id="mobile-menu" className="mobile-menu" aria-label={copy.menuLabel}>
          <InternalLink href="/settings">{copy.navSettings}</InternalLink>
          <a href={frontendUrls.docs} target="_blank" rel="noreferrer">{copy.navHelp}</a>
          <InternalLink href="/crops">{copy.navCrops}</InternalLink>
          <InternalLink href="/map">{copy.navMap}</InternalLink>
          <InternalLink href="/weather">{copy.navWeather}</InternalLink>
        </div>
      ) : null}
    </div>
  );
}
