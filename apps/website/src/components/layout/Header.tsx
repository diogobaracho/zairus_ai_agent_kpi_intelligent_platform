import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import Logo from './Logo';
import Button from '../ui/Button';
import { nav, site } from '../../data/site';
import { hasApiDocs, hasChat } from '../../brand';

export default function Header() {
  const [open, setOpen] = useState(false);
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors hover:text-brand ${isActive ? 'text-brand' : 'text-ink'}`;
  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-paper/90 backdrop-blur">
      <div className="container-site flex h-[72px] items-center justify-between">
        <Link to="/" aria-label={`${site.brand} — home`}>
          <Logo />
        </Link>
        <nav className="hidden items-center gap-8 lg:flex" aria-label="Main">
          {nav.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'} className={linkCls}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="hidden items-center gap-3 lg:flex">
          {hasApiDocs && (
            <a
              href={site.apiDocsUrl}
              className="text-sm font-medium text-ink hover:text-brand"
              target="_blank"
              rel="noreferrer"
            >
              API docs
            </a>
          )}
          {hasChat && (
            <Button to={site.chatUrl} size="sm">
              Open the chat
            </Button>
          )}
        </div>
        <button
          className="rounded-lg p-2 text-ink lg:hidden"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
          aria-expanded={open}
        >
          {open ? <X /> : <Menu />}
        </button>
      </div>
      {open && (
        <div className="border-t border-line bg-paper lg:hidden">
          <div className="container-site flex flex-col gap-4 py-4">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={linkCls}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
            {hasChat && (
              <Button to={site.chatUrl} size="sm" className="w-full">
                Open the chat
              </Button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
