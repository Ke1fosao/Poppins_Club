import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Baby, Heart, Smile, Star, Palette, BookOpen, ChevronDown, ChevronUp,
  Phone, MapPin, Mail, ShieldCheck,
  CheckCircle2, ArrowRight, ArrowLeft, Send, Image as ImageIcon, Clock, Sun,
  MessageCircle, X, Bot, Loader2, Check, Brain, Leaf, Activity, Menu, Settings,
  Home, HelpCircle, Users, Sparkles
} from 'lucide-react';

// У prod-білді — завжди relative URL (фронт і бек на одному домені).
// У dev — повний URL Django (за замовчуванням 127.0.0.1:8000, можна перевизначити через VITE_API_BASE у .env).
const API_BASE = import.meta.env.PROD
  ? ''
  : (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000');

// --- Тонкий роутер на History API ---
const useRoute = () => {
  const [path, setPath] = useState(() => (typeof window !== 'undefined' ? window.location.pathname : '/'));
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = useCallback((newPath) => {
    if (newPath !== window.location.pathname) {
      window.history.pushState({}, '', newPath);
      setPath(newPath);
      window.scrollTo(0, 0);
    }
  }, []);
  return [path, navigate];
};

// Мапа назв іконок (з адмінки) на компоненти Lucide
const ICONS = {
  ShieldCheck, Palette, Smile, Heart, Star, Brain, Leaf, Activity,
  BookOpen, Baby, Sun, Clock, CheckCircle2,
};
const renderIcon = (name, className = "w-8 h-8") => {
  const Icon = ICONS[name] || ShieldCheck;
  return <Icon className={className} />;
};

// Літеральні класи Tailwind для кольорових схем
const COLOR_CLASSES = {
  teal:    { bg50: "bg-teal-50",    bg100: "bg-teal-100",    text500: "text-teal-500",    text600: "text-teal-600",    border500: "border-teal-500" },
  amber:   { bg50: "bg-amber-50",   bg100: "bg-amber-100",   text500: "text-amber-500",   text600: "text-amber-600",   border500: "border-amber-500" },
  rose:    { bg50: "bg-rose-50",    bg100: "bg-rose-100",    text500: "text-rose-500",    text600: "text-rose-600",    border500: "border-rose-500" },
  blue:    { bg50: "bg-blue-50",    bg100: "bg-blue-100",    text500: "text-blue-500",    text600: "text-blue-600",    border500: "border-blue-500" },
  green:   { bg50: "bg-green-50",   bg100: "bg-green-100",   text500: "text-green-500",   text600: "text-green-600",   border500: "border-green-500" },
  emerald: { bg50: "bg-emerald-50", bg100: "bg-emerald-100", text500: "text-emerald-500", text600: "text-emerald-600", border500: "border-emerald-500" },
  slate:   { bg50: "bg-slate-50",   bg100: "bg-slate-100",   text500: "text-slate-500",   text600: "text-slate-600",   border500: "border-slate-500" },
};
const colorOf = (name) => COLOR_CLASSES[name] || COLOR_CLASSES.teal;

// Очистка telephone для href="tel:..." (залишає + і цифри)
const telHref = (phone) => `tel:${(phone || '').replace(/[^\d+]/g, '')}`;
const mailHref = (email) => `mailto:${email || ''}`;
const mapHref = (address) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address || '')}`;

// Чи це валідний http(s) URL
const isHttpUrl = (url) => /^https?:\/\//i.test(url || '');

// Бренд (з логотипом або fallback) — спільний для Navbar/Footer
const Brand = ({ logoUrl, brand, brandAccent, accentClass = "text-teal-500", iconBg = "bg-teal-500", textClass = "text-slate-800", height = "h-10" }) => {
  if (logoUrl) {
    return (
      <img src={logoUrl} alt={`${brand} ${brandAccent}`} className={`${height} w-auto object-contain`} />
    );
  }
  return (
    <div className="flex items-center space-x-2">
      <div className={`${iconBg} p-2 rounded-xl`}>
        <Baby className="w-6 h-6 text-white" />
      </div>
      <span className={`font-extrabold text-2xl tracking-tight ${textClass}`}>
        {brand} <span className={accentClass}>{brandAccent}</span>
      </span>
    </div>
  );
};

const RadioOption = ({ label, selected, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full flex items-center gap-4 p-4 rounded-2xl border-2 transition-all duration-200 text-left
      ${selected ? 'border-teal-500 bg-teal-50 shadow-md' : 'border-slate-200 bg-white hover:border-teal-200 hover:bg-slate-50'}`}
  >
    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors
      ${selected ? 'border-teal-500 bg-teal-500' : 'border-slate-300 bg-white'}`}>
      {selected && <div className="w-2.5 h-2.5 bg-white rounded-full" />}
    </div>
    <span className={`font-medium ${selected ? 'text-teal-900' : 'text-slate-700'}`}>{label}</span>
  </button>
);

const CheckboxOption = ({ label, selected, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full flex items-center gap-4 p-4 rounded-2xl border-2 transition-all duration-200 text-left
      ${selected ? 'border-amber-400 bg-amber-50 shadow-md' : 'border-slate-200 bg-white hover:border-amber-200 hover:bg-slate-50'}`}
  >
    <div className={`w-6 h-6 rounded-md border-2 flex items-center justify-center shrink-0 transition-colors
      ${selected ? 'border-amber-400 bg-amber-400' : 'border-slate-300 bg-white'}`}>
      {selected && <Check className="w-4 h-4 text-white" />}
    </div>
    <span className={`font-medium ${selected ? 'text-amber-950' : 'text-slate-700'}`}>{label}</span>
  </button>
);

const Navbar = ({ navigate, currentPath, settings }) => {
  const [scrolled, setScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isLanding = currentPath === '/';

  const scrollToSection = (id) => {
    setIsMobileMenuOpen(false);
    if (!isLanding) {
      // Переходимо на головну, потім скролимо
      navigate('/');
      setTimeout(() => {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 150);
    } else {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // На сторінці анкети навбар відразу білий і солідний (фон не прозорий)
  const navBg = isLanding
    ? (scrolled || isMobileMenuOpen ? 'bg-white/95 backdrop-blur-md shadow-sm py-3' : 'bg-transparent py-5')
    : 'bg-white shadow-sm py-3';

  // Закриваємо drawer при ESC + блокуємо скрол body
  useEffect(() => {
    if (!isMobileMenuOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') setIsMobileMenuOpen(false); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  // Пункти меню з іконками (для desktop і drawer)
  const navItems = [
    { id: 'home',       label: 'Головна',  Icon: Home },
    { id: 'about',      label: 'Про нас',  Icon: Smile },
    { id: 'directions', label: 'Напрямки', Icon: Brain },
    { id: 'services',   label: 'Групи',    Icon: Users },
    { id: 'faq',        label: 'Питання',  Icon: HelpCircle },
  ];

  return (
    <>
      <nav className={`fixed top-0 w-full z-40 transition-all duration-300 ${navBg}`}>
        <div className="max-w-7xl mx-auto px-5 sm:px-6 flex justify-between items-center relative gap-3">
          <div className="cursor-pointer group min-w-0" onClick={() => isLanding ? scrollToSection('home') : navigate('/')}>
            <Brand
              logoUrl={settings.logo_navbar}
              brand={settings.nav_brand}
              brandAccent={settings.nav_brand_accent}
              height="h-10 sm:h-12"
            />
          </div>

          {/* Desktop menu з іконками */}
          <div className="hidden lg:flex space-x-2 items-center font-semibold text-slate-600">
            {navItems.map(({ id, label, Icon }) => (
              <button
                key={id}
                onClick={() => scrollToSection(id)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-teal-50 hover:text-teal-600 transition-colors"
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}

            <a
              href={`${API_BASE}/admin/`}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-1 p-2 rounded-full hover:bg-slate-100 transition-colors group"
              title="Адмін-панель"
            >
              <Settings className="w-5 h-5 text-slate-400 group-hover:text-teal-500 group-hover:rotate-90 transition-all duration-300" />
            </a>
          </div>

          {/* CTA — лише на desktop (lg+). На мобільному ховаємо щоб не обрізалось */}
          <button
            onClick={() => navigate('/anketa')}
            className="bg-amber-400 text-amber-950 px-5 py-2.5 rounded-full hover:bg-amber-300 hover:shadow-lg hover:-translate-y-0.5 transition-all font-bold hidden lg:block whitespace-nowrap"
          >
            {settings.nav_cta_text}
          </button>

          {/* Hamburger — лише на мобільному */}
          <button
            className="lg:hidden p-2.5 -mr-1 rounded-xl text-slate-700 hover:bg-slate-100 transition-colors active:scale-95"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Відкрити меню"
          >
            <Menu className="w-7 h-7" />
          </button>
        </div>
      </nav>

      {/* Backdrop під drawer (клік для закриття) */}
      <div
        className={`lg:hidden fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 transition-opacity duration-300 ${isMobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsMobileMenuOpen(false)}
        aria-hidden="true"
      />

      {/* Drawer з правого боку */}
      <aside
        className={`lg:hidden fixed top-0 right-0 h-[100dvh] w-[85vw] max-w-sm bg-white shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ease-out ${isMobileMenuOpen ? 'translate-x-0' : 'translate-x-full'}`}
        aria-hidden={!isMobileMenuOpen}
      >
        {/* Шапка drawer */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2 min-w-0">
            <Brand
              logoUrl={settings.logo_navbar}
              brand={settings.nav_brand}
              brandAccent={settings.nav_brand_accent}
              height="h-9"
            />
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 rounded-xl hover:bg-slate-100 transition-colors active:scale-95"
            aria-label="Закрити меню"
          >
            <X className="w-6 h-6 text-slate-600" />
          </button>
        </div>

        {/* Список пунктів */}
        <div className="flex-1 overflow-y-auto py-3 px-3 space-y-1">
          {navItems.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => scrollToSection(id)}
              className="w-full flex items-center gap-3 px-3 py-3.5 rounded-2xl hover:bg-teal-50 active:bg-teal-100 transition-colors text-left group"
            >
              <div className="w-10 h-10 bg-teal-50 group-hover:bg-teal-100 rounded-xl flex items-center justify-center shrink-0 transition-colors">
                <Icon className="w-5 h-5 text-teal-600" />
              </div>
              <span className="font-semibold text-slate-700 group-hover:text-teal-700">{label}</span>
            </button>
          ))}

          <a
            href={`${API_BASE}/admin/`}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center gap-3 px-3 py-3.5 rounded-2xl hover:bg-slate-50 active:bg-slate-100 transition-colors text-left group"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center shrink-0">
              <Settings className="w-5 h-5 text-slate-500" />
            </div>
            <span className="font-semibold text-slate-700">Адмін-панель</span>
          </a>
        </div>

        {/* CTA внизу drawer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <button
            onClick={() => { navigate('/anketa'); setIsMobileMenuOpen(false); }}
            className="w-full bg-amber-400 text-amber-950 px-6 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-amber-500 active:scale-[0.98] transition-all shadow-md"
          >
            <Sparkles className="w-5 h-5" />
            <span className="break-words">{settings.nav_cta_text}</span>
          </button>
        </div>
      </aside>
    </>
  );
};

// Інлайн-парсер для **bold** у звичайному тексті
const renderInlineMarkdown = (text, accentClass = 'text-teal-700') => {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className={`font-bold ${accentClass}`}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
};

const HeroTitle = ({ title, accent }) => {
  if (!accent || !title.includes(accent)) {
    return (
      <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-slate-800 leading-[1.1] w-full break-words">{title}</h1>
    );
  }
  const idx = title.indexOf(accent);
  const before = title.slice(0, idx);
  const after = title.slice(idx + accent.length);
  return (
    <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-slate-800 leading-[1.1] w-full break-words">
      {before}
      <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-500 to-emerald-400">{accent}</span>
      {after}
    </h1>
  );
};

const Hero = ({ onOpenChat, content }) => {
  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) element.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section id="home" className="relative min-h-screen pt-28 pb-20 px-6 flex items-center bg-[#FFFDF9] overflow-hidden">
      <div className="absolute top-20 left-10 w-64 h-64 bg-teal-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-pulse"></div>
      <div className="absolute top-40 right-20 w-72 h-72 bg-amber-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-pulse" style={{ animationDelay: '2s' }}></div>
      <div className="absolute -bottom-8 left-1/2 w-80 h-80 bg-rose-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-pulse" style={{ animationDelay: '4s' }}></div>

      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16 relative z-10 w-full">
        <div className="lg:w-1/2 flex flex-col items-start space-y-8 text-center lg:text-left min-w-0">
          <div className="inline-flex items-center space-x-2 bg-teal-50 text-teal-700 px-4 py-2 rounded-full font-semibold text-sm mx-auto lg:mx-0 max-w-full">
            <Star className="w-4 h-4 fill-current shrink-0" />
            <span className="break-words">{content.hero_badge}</span>
          </div>

          <HeroTitle title={content.hero_title} accent={content.hero_title_accent} />

          <div className="max-w-xl mx-auto lg:mx-0 w-full space-y-4">
            {(content.hero_desc || '').split(/\n+/).map(s => s.trim()).filter(Boolean).map((p, i) =>
              i === 0 ? (
                // Перший абзац — як "лід-цитата" з вертикальною бірюзовою рисочкою
                <div key={i} className="relative pl-5 sm:pl-6 py-1 border-l-[3px] border-teal-400">
                  <p className="text-lg sm:text-xl lg:text-2xl text-slate-800 leading-snug break-words font-semibold">
                    {renderInlineMarkdown(p, 'text-teal-600')}
                  </p>
                </div>
              ) : (
                // Решта — звичайний текст, але з bold-підсвічуванням ключових фраз
                <p
                  key={i}
                  className="text-base sm:text-lg text-slate-600 leading-relaxed break-words"
                >
                  {renderInlineMarkdown(p, 'text-teal-700')}
                </p>
              )
            )}
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center lg:justify-start">
            <button
              onClick={() => scrollToSection('about')}
              className="bg-teal-500 text-white px-7 py-4 rounded-full font-bold text-base lg:text-lg hover:bg-teal-600 hover:shadow-xl hover:shadow-teal-500/30 hover:-translate-y-1 transition-all flex items-center gap-2 justify-center"
            >
              {content.hero_btn_primary}
              <ArrowRight className="w-5 h-5 shrink-0" />
            </button>
            <button
              onClick={() => scrollToSection('contacts')}
              className="bg-white text-slate-700 border-2 border-slate-200 px-7 py-4 rounded-full font-bold text-base lg:text-lg hover:border-teal-500 hover:text-teal-600 transition-all w-full sm:w-auto"
            >
              {content.hero_btn_secondary}
            </button>
          </div>

          <div className="pt-2 w-full flex justify-center lg:justify-start">
            <button
              onClick={onOpenChat}
              className="flex items-center gap-2 text-teal-600 font-medium hover:text-teal-700 transition-all bg-teal-50/80 px-5 py-2.5 rounded-2xl border border-teal-100 hover:border-teal-300 group"
            >
              <Bot className="w-5 h-5 group-hover:animate-bounce shrink-0" />
              <span className="text-left">{content.hero_ai_btn_text}</span>
            </button>
          </div>
        </div>

        <div className="lg:w-1/2 relative w-full max-w-lg mx-auto">
          <div className="relative bg-teal-100 rounded-[3rem] rounded-tr-[8rem] rounded-bl-[8rem] aspect-[4/5] overflow-hidden shadow-2xl flex items-center justify-center border-8 border-white">
            {content.hero_image ? (
              <img src={content.hero_image} alt="Фото садочка" className="absolute inset-0 w-full h-full object-cover" />
            ) : (
              <div className="text-center p-8">
                <ImageIcon className="w-24 h-24 text-teal-300 mx-auto mb-4" />
                <p className="text-teal-700 font-bold text-lg">Яскраве фото дітей<br/>(додайте в адмінці)</p>
              </div>
            )}
          </div>

          <div className="absolute -bottom-6 -left-6 bg-white p-5 sm:p-6 rounded-3xl shadow-xl border border-slate-100 flex items-center gap-3 sm:gap-4 animate-bounce hover:animate-none max-w-[85%]" style={{ animationDuration: '3s' }}>
            <div className="bg-amber-100 p-3 rounded-full shrink-0">
              <Heart className="w-7 h-7 sm:w-8 sm:h-8 text-amber-500 fill-current" />
            </div>
            <div className="min-w-0">
              <p className="text-slate-800 font-extrabold text-lg sm:text-xl break-words leading-tight">{content.hero_badge_value}</p>
              <p className="text-slate-500 font-medium text-xs sm:text-sm break-words">{content.hero_badge_label}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

const About = ({ content, cards, highlights }) => {
  const paragraphs = (content.about_desc || '')
    .split(/\n+/)
    .map(s => s.trim())
    .filter(Boolean);

  // Перший абзац — підкреслено великий «лід»; інші — звичайний текст
  const [lead, ...rest] = paragraphs;
  const hasHighlights = highlights && highlights.length > 0;

  return (
    <section id="about" className="py-24 px-6 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-sm font-bold text-teal-500 uppercase tracking-widest mb-3">{content.about_kicker}</h2>
          <h3 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-800 break-words">
            {content.about_title}
          </h3>
        </div>

        {/* Структурований текст: лід + абзаци + опціональний список тез */}
        <div className={`max-w-5xl mx-auto mb-20 grid ${hasHighlights ? 'lg:grid-cols-5' : 'grid-cols-1'} gap-10 lg:gap-14 items-start`}>
          <div className={`${hasHighlights ? 'lg:col-span-3' : ''} space-y-5`}>
            {lead && (
              <p className="text-xl sm:text-2xl text-slate-800 font-medium leading-relaxed break-words border-l-4 border-teal-400 pl-5">
                {lead}
              </p>
            )}
            {rest.map((p, i) => (
              <p key={i} className="text-base sm:text-lg text-slate-600 leading-relaxed break-words">
                {p}
              </p>
            ))}
          </div>

          {hasHighlights && (
            <div className="lg:col-span-2 bg-gradient-to-br from-teal-50 to-amber-50 rounded-[2rem] p-6 sm:p-8 border border-teal-100/60">
              <h4 className="text-sm font-bold text-teal-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Star className="w-4 h-4 fill-current" /> Що ви отримаєте
              </h4>
              <ul className="space-y-3">
                {highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-3 text-slate-700">
                    <CheckCircle2 className="w-5 h-5 text-teal-500 shrink-0 mt-0.5" />
                    <span className="break-words leading-snug">{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {cards.map((card, idx) => {
            const c = colorOf(card.color);
            return (
              <div key={idx} className={`${c.bg50} rounded-[2.5rem] p-8 sm:p-10 text-left transition-transform hover:-translate-y-2 duration-300`}>
                <div className="bg-white w-16 h-16 rounded-2xl flex items-center justify-center shadow-sm mb-6">
                  {renderIcon(card.icon, `w-8 h-8 ${c.text500}`)}
                </div>
                <h4 className="text-xl sm:text-2xl font-bold text-slate-800 mb-4 break-words leading-tight">{card.title}</h4>
                <p className="text-slate-600 leading-relaxed break-words">{card.text}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

// ============================================================================
//  Універсальна логіка свайпу/драгу — окремо touch (мобіла) і mouse (десктоп).
//  Pointer Events на iOS Safari іноді не спрацьовують для touch — тому явні
//  обробники на touchstart/touchmove/touchend через addEventListener з
//  { passive: false }, що дозволяє preventDefault на горизонтальному свайпі.
// ============================================================================
const useSwipeCarousel = (count, autoMs = 5000) => {
  const [index, setIndex] = useState(0);
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const containerRef = useRef(null);

  // Ref'и для трекінгу — щоб не залежати від замикань у async-обробниках
  const stateRef = useRef({
    startX: 0,
    startY: 0,
    currentDx: 0,
    isDragging: false,
    isHorizontal: false, // визначаємо у перших 10 px руху
    trackWidth: 1,
  });

  const goTo = useCallback((i) => {
    if (count <= 0) return;
    const wrapped = ((i % count) + count) % count;
    setIndex(wrapped);
  }, [count]);

  const next = useCallback(() => goTo(index + 1), [goTo, index]);
  const prev = useCallback(() => goTo(index - 1), [goTo, index]);

  // Авто-прокрутка
  useEffect(() => {
    if (count <= 1 || dragging || autoMs <= 0) return;
    const id = setInterval(() => goTo(index + 1), autoMs);
    return () => clearInterval(id);
  }, [count, dragging, autoMs, goTo, index]);

  // Спільна логіка завершення жесту
  const finalizeDrag = useCallback(() => {
    const s = stateRef.current;
    if (!s.isDragging) return;
    const threshold = s.trackWidth * 0.15;
    if (s.currentDx > threshold) prev();
    else if (s.currentDx < -threshold) next();
    s.isDragging = false;
    s.isHorizontal = false;
    s.currentDx = 0;
    setDragX(0);
    setDragging(false);
  }, [next, prev]);

  // --- Touch handlers (мобіла) ---
  useEffect(() => {
    const el = containerRef.current;
    if (!el || count <= 1) return;

    const onTouchStart = (e) => {
      if (e.touches.length !== 1) return;
      const t = e.touches[0];
      stateRef.current.startX = t.clientX;
      stateRef.current.startY = t.clientY;
      stateRef.current.currentDx = 0;
      stateRef.current.isDragging = true;
      stateRef.current.isHorizontal = false;
      stateRef.current.trackWidth = el.offsetWidth || 1;
      setDragging(true);
    };

    const onTouchMove = (e) => {
      const s = stateRef.current;
      if (!s.isDragging || e.touches.length !== 1) return;
      const t = e.touches[0];
      const dx = t.clientX - s.startX;
      const dy = t.clientY - s.startY;
      const absX = Math.abs(dx), absY = Math.abs(dy);

      // У перші ~10 px визначаємо: горизонталь чи вертикаль
      if (!s.isHorizontal && absX < 10 && absY < 10) return;
      if (!s.isHorizontal) {
        if (absY > absX) {
          // Користувач скролить сторінку — припиняємо драг
          s.isDragging = false;
          s.currentDx = 0;
          setDragX(0);
          setDragging(false);
          return;
        }
        s.isHorizontal = true;
      }

      // Це горизонтальний свайп → блокуємо нативний скрол сторінки
      if (e.cancelable) e.preventDefault();
      s.currentDx = dx;
      setDragX(dx);
    };

    const onTouchEnd = () => finalizeDrag();

    // passive:false ОБОВ'ЯЗКОВО для preventDefault на touchmove
    el.addEventListener('touchstart', onTouchStart, { passive: true });
    el.addEventListener('touchmove', onTouchMove, { passive: false });
    el.addEventListener('touchend', onTouchEnd, { passive: true });
    el.addEventListener('touchcancel', onTouchEnd, { passive: true });

    return () => {
      el.removeEventListener('touchstart', onTouchStart);
      el.removeEventListener('touchmove', onTouchMove);
      el.removeEventListener('touchend', onTouchEnd);
      el.removeEventListener('touchcancel', onTouchEnd);
    };
  }, [count, finalizeDrag]);

  // --- Mouse handlers (десктоп) ---
  const onMouseDown = useCallback((e) => {
    if (count <= 1) return;
    if (e.button !== 0) return; // тільки ліва кнопка
    const el = containerRef.current;
    stateRef.current.startX = e.clientX;
    stateRef.current.startY = e.clientY;
    stateRef.current.currentDx = 0;
    stateRef.current.isDragging = true;
    stateRef.current.isHorizontal = true; // на миші відразу drag — без визначення напрямку
    stateRef.current.trackWidth = el?.offsetWidth || 1;
    setDragging(true);

    const onMove = (ev) => {
      const s = stateRef.current;
      if (!s.isDragging) return;
      const dx = ev.clientX - s.startX;
      s.currentDx = dx;
      setDragX(dx);
    };
    const onUp = () => {
      finalizeDrag();
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [count, finalizeDrag]);

  return { index, dragX, dragging, containerRef, onMouseDown, next, prev, goTo };
};

// ============================================================================
//  Премісес: drag/swipe гелерея з плавним переходом, без зовнішніх стрілок
// ============================================================================
const Premises = ({ content, slides }) => {
  const safeSlides = slides && slides.length > 0 ? slides : [{ title: "Додайте слайди в адмінці", desc: "", image: "" }];
  const {
    index, dragX, dragging, containerRef, onMouseDown, goTo,
  } = useSwipeCarousel(safeSlides.length, 5000);

  const trackStyle = {
    transform: `translateX(calc(${-index * 100}% + ${dragX}px))`,
    transition: dragging ? 'none' : 'transform 700ms cubic-bezier(0.22, 1, 0.36, 1)',
  };

  return (
    <section className="py-24 px-6 bg-teal-500 text-white overflow-hidden relative">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-start gap-12 lg:gap-16 relative z-10">
        <div className="lg:w-1/3 text-center lg:text-left min-w-0">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold mb-6 break-words">{content.premises_title}</h2>
          {content.premises_subtitle && (
            <p className="text-teal-50 font-bold text-lg sm:text-xl mb-6 break-words border-l-4 border-amber-300 pl-4 lg:pl-5 inline-block text-left">
              {content.premises_subtitle}
            </p>
          )}
          <div className="space-y-4">
            {(content.premises_desc || '').split(/\n+/).map(s => s.trim()).filter(Boolean).map((p, i) => (
              <p key={i} className="text-teal-50/90 leading-relaxed break-words text-base sm:text-[17px]">
                {p}
              </p>
            ))}
          </div>
        </div>

        <div className="lg:w-2/3 w-full flex flex-col gap-5">
          <div
            ref={containerRef}
            className="relative rounded-[2.5rem] shadow-2xl overflow-hidden aspect-video select-none cursor-grab active:cursor-grabbing bg-teal-700/30"
            style={{ touchAction: 'pan-y' }}
            onMouseDown={onMouseDown}
          >
            <div className="flex h-full will-change-transform" style={trackStyle}>
              {safeSlides.map((slide, idx) => (
                <div key={idx} className="relative w-full h-full shrink-0 grow-0 basis-full overflow-hidden">
                  {slide.image ? (
                    <>
                      <img
                        src={slide.image}
                        alt={slide.title}
                        draggable={false}
                        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-6 text-white">
                        <p className="font-bold text-xl break-words leading-tight">{slide.title}</p>
                        {slide.desc && <p className="text-sm opacity-90 break-words">{slide.desc}</p>}
                      </div>
                    </>
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-white/80 p-6 text-center">
                      <ImageIcon className="w-20 h-20 mb-4 opacity-50" />
                      <p className="font-bold text-xl break-words">{slide.title}</p>
                      <p className="opacity-80 break-words">{slide.desc}</p>
                      <p className="text-sm mt-4 opacity-70">(Завантажте фото в адмінці)</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Точки — прям під фото */}
          {safeSlides.length > 1 && (
            <div className="flex items-center justify-center gap-2">
              {safeSlides.map((_, i) => (
                <button
                  key={i}
                  aria-label={`Слайд ${i + 1}`}
                  onClick={() => goTo(i)}
                  className={`h-2.5 rounded-full transition-all ${index === i ? 'bg-white w-10' : 'bg-white/40 hover:bg-white/70 w-2.5'}`}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

// ============================================================================
//  Карусель 16:9 для першого ряду «Напрямків» (зі стрілками НА фото)
// ============================================================================
const PhotoCarousel = ({ photos, ratioClass = "aspect-video" }) => {
  const safe = photos && photos.length > 0 ? photos : [];
  const {
    index, dragX, dragging, containerRef, onMouseDown,
    next, prev, goTo,
  } = useSwipeCarousel(safe.length, 6000);

  if (safe.length === 0) {
    return (
      <div className={`${ratioClass} w-full rounded-[2.5rem] bg-slate-100 border-2 border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400`}>
        <ImageIcon className="w-16 h-16 mb-3 opacity-60" />
        <p className="font-medium">Додайте фото каруселі в адмінці</p>
      </div>
    );
  }

  const trackStyle = {
    transform: `translateX(calc(${-index * 100}% + ${dragX}px))`,
    transition: dragging ? 'none' : 'transform 700ms cubic-bezier(0.22, 1, 0.36, 1)',
  };

  return (
    <div
      ref={containerRef}
      className={`relative ${ratioClass} w-full rounded-[2.5rem] overflow-hidden shadow-2xl bg-slate-100 select-none cursor-grab active:cursor-grabbing`}
      style={{ touchAction: 'pan-y' }}
      onMouseDown={onMouseDown}
    >
      <div className="flex h-full will-change-transform" style={trackStyle}>
        {safe.map((p, idx) => (
          <div key={idx} className="relative w-full h-full shrink-0 grow-0 basis-full">
            <img
              src={p.url}
              alt={p.alt || `Фото ${idx + 1}`}
              draggable={false}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            />
          </div>
        ))}
      </div>

      {safe.length > 1 && (
        <>
          <button
            aria-label="Попереднє фото"
            onClick={(e) => { e.stopPropagation(); prev(); }}
            className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 hover:bg-white shadow-md flex items-center justify-center text-slate-700 transition-colors z-10"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <button
            aria-label="Наступне фото"
            onClick={(e) => { e.stopPropagation(); next(); }}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 hover:bg-white shadow-md flex items-center justify-center text-slate-700 transition-colors z-10"
          >
            <ArrowRight className="w-5 h-5" />
          </button>
          <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5 z-10">
            {safe.map((_, i) => (
              <button
                key={i}
                aria-label={`Слайд ${i + 1}`}
                onClick={(e) => { e.stopPropagation(); goTo(i); }}
                className={`h-1.5 rounded-full transition-all ${index === i ? 'bg-white w-6' : 'bg-white/60 w-1.5'}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ============================================================================
//  Колаж 3 фото: велика портретна зліва, дві менші справа (ландшафт + портрет)
// ============================================================================
const DirectionCollage = ({ photos }) => {
  const byPos = {};
  (photos || []).forEach(p => { byPos[p.position] = p; });

  const Placeholder = ({ label, className }) => (
    <div className={`${className} flex flex-col items-center justify-center text-slate-400 bg-slate-50 border-2 border-dashed border-slate-300`}>
      <ImageIcon className="w-10 h-10 mb-2 opacity-60" />
      <p className="text-xs sm:text-sm font-medium px-2 text-center">{label}</p>
    </div>
  );

  const Cell = ({ p, label, wrapperClass }) => (
    <div className={`${wrapperClass} relative rounded-[2rem] overflow-hidden shadow-xl`}>
      {p?.url ? (
        <img src={p.url} alt={p.alt || label} className="absolute inset-0 w-full h-full object-cover" />
      ) : (
        <Placeholder label={label} className="absolute inset-0 rounded-[2rem]" />
      )}
    </div>
  );

  return (
    <div className="grid grid-cols-5 gap-4 w-full">
      {/* Велика портретна — займає 3 колонки і 2 рядки */}
      <Cell
        p={byPos[1]}
        label="Портрет 1920×2880 — додайте в адмінці"
        wrapperClass="col-span-3 row-span-2"
      />
      {/* Верхня менша — ландшафт 3:2 */}
      <Cell
        p={byPos[2]}
        label="Ландшафт 1920×1280"
        wrapperClass="col-span-2 aspect-[3/2]"
      />
      {/* Нижня менша — портрет 2:3 */}
      <Cell
        p={byPos[3]}
        label="Портрет 1920×2880"
        wrapperClass="col-span-2 aspect-[2/3]"
      />
    </div>
  );
};

// Картка-теза в dash-стилі (без іконкового блоку)
const DirectionDashCard = ({ d }) => {
  const c = colorOf(d.color);
  return (
    <div>
      <h4 className={`text-lg sm:text-xl font-extrabold ${c.text600} mb-2 break-words leading-tight flex items-baseline gap-2`}>
        <span aria-hidden="true">—</span>
        <span>{d.title}:</span>
      </h4>
      <p className="text-slate-600 leading-relaxed break-words">{d.text}</p>
    </div>
  );
};

const DashedCardContainer = ({ children }) => (
  <div className="border-2 border-dashed border-slate-300 rounded-[2.5rem] p-7 sm:p-10 space-y-8 bg-white/40">
    {children}
  </div>
);

const Directions = ({ content, first, second, gallery, collage }) => {
  return (
    <section id="directions" className="py-24 px-6 bg-[#FFFDF9]">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-14">
           <h2 className="text-sm font-bold text-teal-500 uppercase tracking-widest mb-3">{content.directions_kicker}</h2>
           <h3 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-800 break-words">{content.directions_title}</h3>
        </div>

        {/* Ряд 1: dash-картки зліва, карусель 16:9 справа */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center mb-12">
          <div className="order-2 lg:order-1">
            <DashedCardContainer>
              {first.map((d, idx) => <DirectionDashCard key={idx} d={d} />)}
            </DashedCardContainer>
          </div>
          <div className="order-1 lg:order-2">
            <PhotoCarousel photos={gallery} ratioClass="aspect-video" />
          </div>
        </div>

        {/* Ряд 2: колаж зліва, dash-картки справа */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div className="order-1">
            <DirectionCollage photos={collage} />
          </div>
          <div className="order-2">
            <DashedCardContainer>
              {second.map((d, idx) => <DirectionDashCard key={idx} d={d} />)}
            </DashedCardContainer>
          </div>
        </div>
      </div>
    </section>
  );
};

const Services = ({ onOpenSurvey, content, services }) => {
  return (
    <section id="services" className="py-24 px-6 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
           <h2 className="text-sm font-bold text-amber-500 uppercase tracking-widest mb-3">{content.services_kicker}</h2>
           <h3 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-800 break-words">{content.services_title}</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {services.map((pkg, idx) => {
            const c = colorOf(pkg.color);
            return (
              <div key={idx} className={`relative bg-[#FFFDF9] rounded-[2.5rem] p-8 sm:p-10 border-2 ${pkg.is_popular ? c.border500 + ' shadow-2xl shadow-amber-500/20 md:scale-105 z-10' : 'border-slate-100 shadow-lg'} flex flex-col`}>
                {pkg.is_popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-amber-400 text-amber-950 px-4 py-1.5 rounded-full text-sm font-bold whitespace-nowrap">
                    {pkg.popular_label}
                  </div>
                )}
                <div className={`${c.bg50} w-20 h-20 rounded-3xl flex items-center justify-center mb-6`}>
                  {renderIcon(pkg.icon, `w-10 h-10 ${c.text500}`)}
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-800 mb-2 break-words leading-tight">{pkg.title}</h3>
                <div className="flex items-center gap-2 text-slate-500 font-medium mb-6">
                  <Clock className="w-4 h-4 shrink-0" />
                  <span className="break-words">Вік: {pkg.age}</span>
                </div>
                <p className="text-slate-600 mb-8 flex-grow leading-relaxed break-words">{pkg.desc}</p>

                <ul className="space-y-3 mb-8">
                  {(pkg.features || []).map((f, i) => (
                    <li key={i} className="flex items-start gap-3 text-slate-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
                      <span className="break-words">{f}</span>
                    </li>
                  ))}
                </ul>

                <button onClick={onOpenSurvey} className={`w-full py-4 rounded-2xl font-bold transition-all ${pkg.is_popular ? 'bg-amber-400 text-amber-950 hover:bg-amber-500' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}`}>
                  {pkg.btn_text}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

const FAQItemRow = ({ faq, open, onClick }) => (
  <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-200 transition-all">
    <button
      className="w-full p-5 text-left flex justify-between items-start gap-3 font-bold text-base text-slate-800 hover:text-teal-600 transition-colors"
      onClick={onClick}
    >
      <span className="break-words leading-snug">{faq.q}</span>
      <div className={`p-1.5 rounded-full transition-colors shrink-0 ${open ? 'bg-teal-100 text-teal-600' : 'bg-slate-100 text-slate-400'}`}>
        {open ? <ChevronUp className="w-4 h-4 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 flex-shrink-0" />}
      </div>
    </button>
    <div className={`transition-all duration-300 ease-in-out grid ${open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
      <div className="overflow-hidden">
        <div className="px-5 pb-5 text-slate-600 leading-relaxed border-t border-slate-100 pt-4 break-words">{faq.a}</div>
      </div>
    </div>
  </div>
);

const FAQ = ({ content, faqs }) => {
  const [openIdx, setOpenIdx] = useState(null);

  return (
    <section id="faq" className="py-24 px-6 bg-[#FFFDF9]">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-800 text-center mb-12 break-words">{content.faq_title}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
          {faqs.map((faq, idx) => (
            <FAQItemRow
              key={idx}
              faq={faq}
              open={openIdx === idx}
              onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

const ContactAndMap = ({ settings, content }) => {
  const [form, setForm] = useState({ name: '', phone: '', message: '' });
  const [consent, setConsent] = useState(false);
  const [website, setWebsite] = useState('');           // honeypot
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const startedAtRef = useRef(Date.now());

  const updateField = (k, v) => {
    setForm(prev => ({ ...prev, [k]: v }));
    setFieldErrors(prev => ({ ...prev, [k]: undefined }));
    setFormError('');
  };

  const validate = () => {
    const errs = {};
    const name = form.name.trim();
    const phone = form.phone.trim();
    const message = form.message.trim();

    if (name.length < 2) errs.name = "Вкажіть імʼя (мін. 2 символи).";
    else if (name.length > 100) errs.name = "Імʼя занадто довге.";

    const digits = phone.replace(/\D/g, '');
    if (digits.length < 7) errs.phone = "Вкажіть коректний телефон.";
    else if (digits.length > 20) errs.phone = "Телефон занадто довгий.";

    if (message.length < 5) errs.message = "Опишіть запитання детальніше (мін. 5 символів).";
    else if (message.length > 2000) errs.message = "Повідомлення занадто довге.";

    if (!consent) errs.consent = "Потрібна згода на обробку персональних даних.";

    return errs;
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setSuccess(false);

    const errs = validate();
    if (Object.keys(errs).length) {
      setFieldErrors(errs);
      setFormError("Будь ласка, виправте помилки нижче.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/contact/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name.trim(),
          phone: form.phone.trim(),
          message: form.message.trim(),
          consent: true,
          website,                                   // honeypot
          startedAt: startedAtRef.current,           // time-of-load
        }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setSuccess(true);
        setForm({ name: '', phone: '', message: '' });
        setConsent(false);
        setFieldErrors({});
        startedAtRef.current = Date.now();
      } else if (res.status === 429) {
        setFormError(data.error || "Забагато спроб. Зачекайте хвилину.");
      } else if (data.errors) {
        setFieldErrors(data.errors);
        setFormError("Будь ласка, виправте помилки нижче.");
      } else {
        setFormError(data.error || "Сталася помилка на сервері.");
      }
    } catch (error) {
      console.error("Помилка відправки:", error);
      setFormError("Немає зв'язку з сервером.");
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = (field) =>
    `w-full px-5 py-4 rounded-xl text-slate-800 border ${fieldErrors[field] ? 'border-rose-400 bg-rose-50' : 'border-slate-200 bg-slate-50'} focus:outline-none focus:ring-2 focus:ring-teal-500`;

  const validMap = isHttpUrl(settings.map_url);

  return (
    <section id="contacts" className="py-24 px-6 bg-slate-100">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-12 lg:gap-16">
        <div className="lg:w-1/3 w-full">
          <div className="bg-white border border-slate-200 p-7 sm:p-8 rounded-[2.5rem] shadow-xl">
            <h4 className="text-2xl font-bold text-slate-800 mb-6 break-words">{content.contact_form_title}</h4>
            <form className="space-y-4" onSubmit={handleContactSubmit} noValidate>
              {/* Honeypot — приховано від людей, видно ботам */}
              <input
                type="text"
                name="website"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                tabIndex={-1}
                autoComplete="off"
                aria-hidden="true"
                className="absolute left-[-9999px] opacity-0 pointer-events-none h-0 w-0"
              />

              <div>
                <input
                  name="name"
                  type="text"
                  placeholder="Ваше ім'я *"
                  value={form.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className={inputCls('name')}
                  maxLength={100}
                />
                {fieldErrors.name && <p className="mt-1 text-xs text-rose-600">{fieldErrors.name}</p>}
              </div>

              <div>
                <input
                  name="phone"
                  type="tel"
                  placeholder="Номер телефону *"
                  value={form.phone}
                  onChange={(e) => updateField('phone', e.target.value)}
                  className={inputCls('phone')}
                  maxLength={20}
                />
                {fieldErrors.phone && <p className="mt-1 text-xs text-rose-600">{fieldErrors.phone}</p>}
              </div>

              <div>
                <textarea
                  name="message"
                  placeholder="Ваше запитання... *"
                  rows="3"
                  value={form.message}
                  onChange={(e) => updateField('message', e.target.value)}
                  className={`${inputCls('message')} resize-none`}
                  maxLength={2000}
                ></textarea>
                {fieldErrors.message && <p className="mt-1 text-xs text-rose-600">{fieldErrors.message}</p>}
              </div>

              <label className="flex items-start gap-3 text-sm text-slate-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => { setConsent(e.target.checked); setFieldErrors(prev => ({ ...prev, consent: undefined })); setFormError(''); }}
                  className={`mt-1 w-5 h-5 rounded border-slate-300 text-teal-500 focus:ring-teal-500 cursor-pointer shrink-0 ${fieldErrors.consent ? 'ring-2 ring-rose-400' : ''}`}
                />
                <span className="break-words">Надаю згоду на обробку персональних даних <span className="text-rose-500">*</span></span>
              </label>
              {fieldErrors.consent && <p className="text-xs text-rose-600 -mt-2">{fieldErrors.consent}</p>}

              {formError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-600 text-sm break-words">{formError}</div>
              )}
              {success && (
                <div className="p-3 rounded-xl bg-green-50 border border-green-200 text-green-700 text-sm flex items-center gap-2">
                  <Check className="w-5 h-5 shrink-0" />
                  <span>Повідомлення успішно відправлено!</span>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-teal-500 text-white px-8 py-4 rounded-xl font-bold hover:bg-teal-600 transition-colors flex items-center justify-center space-x-2 disabled:opacity-70"
              >
                {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5 shrink-0" />}
                <span>{submitting ? 'Відправка...' : content.contact_form_btn}</span>
              </button>
            </form>
          </div>
        </div>

        <div className="lg:w-2/3 w-full flex flex-col min-w-0">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-8">
            <a
              href={telHref(settings.phone)}
              className="p-5 sm:p-6 bg-white rounded-3xl shadow-sm border border-slate-200 hover:shadow-md hover:border-amber-300 transition-all group min-w-0"
            >
              <Phone className="w-6 h-6 text-amber-500 mb-2 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-slate-800 break-all leading-snug">{settings.phone}</p>
              <p className="text-xs text-slate-400 mt-1">Натисніть, щоб подзвонити</p>
            </a>
            <a
              href={mailHref(settings.email)}
              className="p-5 sm:p-6 bg-white rounded-3xl shadow-sm border border-slate-200 hover:shadow-md hover:border-teal-300 transition-all group min-w-0"
            >
              <Mail className="w-6 h-6 text-teal-500 mb-2 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-slate-800 break-all leading-snug text-sm sm:text-base">{settings.email}</p>
              <p className="text-xs text-slate-400 mt-1">Натисніть, щоб написати</p>
            </a>
            <a
              href={mapHref(settings.address)}
              target="_blank"
              rel="noopener noreferrer"
              className="p-5 sm:p-6 bg-white rounded-3xl shadow-sm border border-slate-200 hover:shadow-md hover:border-rose-300 transition-all group min-w-0"
            >
              <MapPin className="w-6 h-6 text-rose-500 mb-2 group-hover:scale-110 transition-transform" />
              <p className="font-bold text-slate-800 break-words leading-snug">{settings.address}</p>
              <p className="text-xs text-slate-400 mt-1">Відкрити в Google Maps</p>
            </a>
          </div>

          <div className="relative flex-grow w-full rounded-[2.5rem] overflow-hidden shadow-md border border-slate-200 bg-slate-200 min-h-[350px]">
            {validMap ? (
              <iframe
                src={settings.map_url}
                className="absolute inset-0 w-full h-full border-0"
                allowFullScreen=""
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                title="Карта садочка"
              ></iframe>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 bg-slate-100 p-6 text-center">
                <MapPin className="w-12 h-12 mb-3 text-slate-300" />
                <p className="font-medium">Інтерактивна карта (Google Maps)</p>
                <p className="text-sm mt-2 max-w-md">Додайте src з iframe Google Maps в адмінці (поле «Посилання на карту»).</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

const FacebookIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
  </svg>
);

const InstagramIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
  </svg>
);

const TelegramIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/>
  </svg>
);

const ThreadsIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.953 11.142c-.071-.034-.143-.067-.216-.099-.127-2.345-1.408-3.688-3.557-3.701h-.029c-1.285 0-2.354.549-3.014 1.547l1.182.811c.491-.745 1.263-.904 1.833-.904h.019c.708.005 1.243.211 1.59.612.252.292.42.696.501 1.201-.61-.103-1.27-.135-1.975-.094-1.987.115-3.265 1.273-3.179 2.883.044.817.452 1.519 1.149 1.978.59.388 1.349.578 2.138.535 1.042-.057 1.86-.454 2.43-1.181.433-.553.706-1.27.825-2.158.484.292.842.677 1.04 1.139.336.785.355 2.075-.696 3.125-.921.92-2.028 1.318-3.7 1.33-1.857-.014-3.262-.61-4.176-1.769-.857-1.087-1.298-2.658-1.317-4.665.019-2.008.46-3.579 1.317-4.665.914-1.16 2.319-1.755 4.176-1.769 1.872.014 3.31.611 4.273 1.775.471.572.829 1.291 1.07 2.13l1.396-.371c-.291-1.03-.751-1.927-1.377-2.686-1.236-1.495-3.044-2.262-5.357-2.279h-.011c-2.31.016-4.092.79-5.293 2.298C4.624 7.728 4.097 9.5 4.07 11.992l-.001.012.001.011c.027 2.493.554 4.265 1.692 5.713 1.201 1.509 2.983 2.282 5.293 2.298h.011c2.055-.014 3.503-.55 4.696-1.738 1.563-1.563 1.514-3.524.999-4.728-.371-.866-1.043-1.567-1.94-2.027zm-3.715 3.357c-.873.049-1.78-.343-1.823-1.187-.029-.564.394-1.179 1.901-1.265.179-.011.348-.014.502-.014.515 0 .991.044 1.405.135-.131 1.815-1.018 2.282-1.985 2.331z"/>
  </svg>
);

const Footer = ({ settings }) => {
  return (
    <footer className="bg-slate-900 pt-20 pb-10 px-6 text-slate-300">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8 border-b border-slate-800 pb-12 mb-8">
        <Brand
          logoUrl={settings.logo_footer}
          brand={settings.nav_brand}
          brandAccent={settings.nav_brand_accent}
          accentClass="text-teal-400"
          textClass="text-white"
          iconBg="bg-teal-500"
          height="h-14 sm:h-16"
        />
        <div className="flex space-x-3">
          {settings.facebook && <a href={settings.facebook} target="_blank" rel="noopener noreferrer" aria-label="Facebook" className="bg-slate-800 p-3 rounded-xl hover:bg-teal-500 hover:text-white transition-colors flex items-center justify-center w-12 h-12"><FacebookIcon /></a>}
          {settings.instagram && <a href={settings.instagram} target="_blank" rel="noopener noreferrer" aria-label="Instagram" className="bg-slate-800 p-3 rounded-xl hover:bg-rose-500 hover:text-white transition-colors flex items-center justify-center w-12 h-12"><InstagramIcon /></a>}
          {settings.telegram && <a href={settings.telegram} target="_blank" rel="noopener noreferrer" aria-label="Telegram" className="bg-slate-800 p-3 rounded-xl hover:bg-sky-500 hover:text-white transition-colors flex items-center justify-center w-12 h-12"><TelegramIcon /></a>}
          {settings.threads && <a href={settings.threads} target="_blank" rel="noopener noreferrer" aria-label="Threads" className="bg-slate-800 p-3 rounded-xl hover:bg-slate-100 hover:text-slate-900 transition-colors flex items-center justify-center w-12 h-12"><ThreadsIcon /></a>}
        </div>
      </div>
      <div className="text-center text-sm text-slate-500 break-words">© {new Date().getFullYear()} {settings.footer_copyright}</div>
      <div className="text-center text-xs text-slate-600 mt-3 break-words">
        Designed &amp; Developed by <span className="text-slate-300 font-medium">Kovtunovych Dmytro Valeriyovych</span>
      </div>
    </footer>
  );
};

// ============================================================================
//  Допоміжні поля для опитувальника
// ============================================================================
const QuestionBlock = ({ label, subtitle, children }) => (
  <div className="space-y-3">
    <div>
      <p className="font-semibold text-slate-700 text-base sm:text-lg leading-snug">{label}</p>
      {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
    </div>
    {children}
  </div>
);

const TextInputField = ({ value, onChange, placeholder, multiline = false, rows = 3 }) =>
  multiline ? (
    <textarea
      rows={rows}
      value={value || ''}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 focus:border-teal-500 outline-none transition-colors resize-none"
    />
  ) : (
    <input
      type="text"
      value={value || ''}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 focus:border-teal-500 outline-none transition-colors"
    />
  );

// Список з опціональним "Other" (multi-select)
const CheckboxGroupWithOther = ({ options, valueArr, otherText, onToggle, onOtherChange, gridCols = "grid-cols-1" }) => {
  const isOtherSel = (valueArr || []).includes('Other');
  return (
    <div className="space-y-3">
      <div className={`grid ${gridCols} gap-3`}>
        {options.map(opt => (
          <CheckboxOption
            key={opt}
            label={opt}
            selected={(valueArr || []).includes(opt)}
            onClick={() => onToggle(opt)}
          />
        ))}
        <CheckboxOption
          label="Інше (вкажіть)"
          selected={isOtherSel}
          onClick={() => onToggle('Other')}
        />
      </div>
      {isOtherSel && (
        <input
          type="text"
          value={otherText || ''}
          onChange={e => onOtherChange(e.target.value)}
          placeholder="Уточніть, будь ласка..."
          className="w-full px-5 py-4 rounded-2xl border-2 border-amber-300 focus:border-amber-500 outline-none transition-colors bg-amber-50/50"
        />
      )}
    </div>
  );
};

const RadioGroupWithOther = ({ options, value, otherText, onSelect, onOtherChange }) => {
  const isOther = value === 'Other';
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3">
        {options.map(opt => (
          <RadioOption key={opt} label={opt} selected={value === opt} onClick={() => onSelect(opt)} />
        ))}
        <RadioOption label="Інше (вкажіть)" selected={isOther} onClick={() => onSelect('Other')} />
      </div>
      {isOther && (
        <input
          type="text"
          value={otherText || ''}
          onChange={e => onOtherChange(e.target.value)}
          placeholder="Уточніть, будь ласка..."
          className="w-full px-5 py-4 rounded-2xl border-2 border-amber-300 focus:border-amber-500 outline-none transition-colors bg-amber-50/50"
        />
      )}
    </div>
  );
};

const TOTAL_STEPS = 6; // 1..6 = змістовні кроки

const SurveyFlow = ({ navigate, siteData }) => {
  const settings = siteData.settings || {};
  const brand = `${settings.nav_brand || 'ЗДО'} ${settings.nav_brand_accent || ''}`.trim();

  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({});
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateForm = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
    setErrorMsg('');
  };

  const toggleArrayItem = (key, value) => {
    setFormData(prev => {
      const current = prev[key] || [];
      return { ...prev, [key]: current.includes(value) ? current.filter(i => i !== value) : [...current, value] };
    });
    setErrorMsg('');
  };

  // Скласти масив значень з "Other"
  const collectWithOther = (arr, otherText) => {
    const out = (arr || []).filter(v => v !== 'Other');
    if ((arr || []).includes('Other') && otherText?.trim()) out.push(otherText.trim());
    return out;
  };
  const collectRadioWithOther = (val, otherText) => {
    if (val === 'Other') return otherText?.trim() || '';
    return val || '';
  };

  const validate = (s) => {
    if (s === 1) {
      if (!(formData.ages || []).length) return 'Оберіть хоча б один вік дитини.';
      if (!formData.formula) return 'Дайте відповідь про дитячу суміш.';
      if (!formData.eQueue) return 'Дайте відповідь про електронну чергу.';
      if (!formData.pediatrist) return 'Дайте відповідь про педіатра.';
    } else if (s === 2) {
      if (!(formData.formats || []).length) return 'Оберіть формат перебування.';
      if (!(formData.timeSlots || []).length) return 'Оберіть часові проміжки.';
      if ((formData.timeSlots || []).includes('Other') && !formData.timeSlotsOther?.trim())
        return 'Уточніть «Інше» в часових проміжках.';
      if (!(formData.days || []).length) return 'Оберіть хоча б один день тижня.';
    } else if (s === 3) {
      if (!(formData.expectations || []).length) return 'Оберіть, що для вас найважливіше.';
      if ((formData.expectations || []).includes('Other') && !formData.expectationsOther?.trim())
        return 'Уточніть «Інше» в очікуваннях.';
    } else if (s === 4) {
      if (!formData.lecturesInterest) return 'Дайте відповідь про лекції.';
      if (!formData.interactionFormats) return 'Оберіть формат взаємодії.';
      if (formData.interactionFormats === 'Other' && !formData.interactionFormatsOther?.trim())
        return 'Уточніть «Інше» формат взаємодії.';
    } else if (s === 5) {
      if (!formData.benefits) return 'Дайте відповідь про пільги.';
    } else if (s === 6) {
      if (!formData.parentName?.trim() || !formData.phone?.trim() || !formData.childName?.trim())
        return 'Заповніть обов\'язкові поля з зірочкою (*).';
      if (!formData.consent) return 'Потрібна згода на обробку персональних даних.';
    }
    return '';
  };

  const handleNext = async () => {
    if (step >= 1 && step <= 6) {
      const err = validate(step);
      if (err) { setErrorMsg(err); return; }
    }

    if (step === 6) {
      // Готуємо payload для бекенда
      setIsSubmitting(true);
      setErrorMsg('');
      try {
        const payload = {
          // Контакти
          parentName: formData.parentName,
          phone: formData.phone,
          email: formData.email,
          childName: formData.childName,
          // Крок 1
          ages: formData.ages,
          allergies: formData.allergies,
          formula: formData.formula,
          eQueue: formData.eQueue,
          pediatrist: formData.pediatrist,
          // Крок 2
          formats: formData.formats,
          timeSlots: collectWithOther(formData.timeSlots, formData.timeSlotsOther),
          days: formData.days,
          // Крок 3
          expectations: collectWithOther(formData.expectations, formData.expectationsOther),
          redFlags: formData.redFlags,
          // Крок 4
          valueInComm: formData.valueInComm,
          challenges: formData.challenges,
          lecturesInterest: formData.lecturesInterest,
          interactionFormats: collectRadioWithOther(formData.interactionFormats, formData.interactionFormatsOther),
          parentQuestions: formData.parentQuestions,
          // Крок 5
          benefits: formData.benefits,
        };
        const res = await fetch(`${API_BASE}/api/survey/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          setErrorMsg('Сталася помилка при відправці. Перевірте підключення до сервера.');
          setIsSubmitting(false);
          return;
        }
      } catch (e) {
        console.error("Помилка відправки анкети", e);
        setErrorMsg("Немає зв'язку з сервером.");
        setIsSubmitting(false);
        return;
      }
      setIsSubmitting(false);
    }

    setErrorMsg('');
    setStep(s => s + 1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const prevStep = () => {
    setErrorMsg('');
    setStep(s => s - 1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ===== Рендер контенту кожного кроку =====
  const renderStepContent = () => {
    switch (step) {
      case 0:
        return (
          <div className="text-center animate-fade-in-up">
            {settings.logo_navbar ? (
              <img src={settings.logo_navbar} alt={brand} className="h-20 sm:h-24 mx-auto mb-8 object-contain" />
            ) : (
              <div className="inline-flex justify-center items-center w-20 h-20 bg-teal-100 rounded-full mb-8">
                <Baby className="w-10 h-10 text-teal-600" />
              </div>
            )}
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-800 mb-6 break-words">Анкета попередньої реєстрації</h2>
            <p className="text-slate-600 text-base sm:text-lg mb-4 max-w-xl mx-auto break-words">
              {brand} — сучасний дитячий садок. Ми створюємо простір, де батьки можуть з впевненістю довірити дитину фахівцям.
            </p>
            <p className="text-slate-500 text-sm mb-10">(Приблизно 3-5 хвилин · 6 кроків)</p>
            <button onClick={handleNext} className="bg-teal-500 text-white px-10 py-4 rounded-full font-bold text-lg hover:bg-teal-600 transition-all shadow-lg hover:shadow-teal-500/30">
              Почати заповнення
            </button>
          </div>
        );

      case 1: // Про дитину
        return (
          <div className="space-y-8 animate-fade-in">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-800 text-center mb-8">Про дитину</h3>

            <QuestionBlock
              label="Вкажіть вік дитини на момент заповнення анкети:"
              subtitle="Якщо діток двоє чи більше — оберіть необхідні варіанти"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {['0 років - 6 місяців', '6 місяців - 1 рік', '1 рік - 1,5 роки', '1,5 роки - 2 роки', '2 роки - 3 роки', '3 роки +'].map(age => (
                  <CheckboxOption
                    key={age}
                    label={age}
                    selected={(formData.ages || []).includes(age)}
                    onClick={() => toggleArrayItem('ages', age)}
                  />
                ))}
              </div>
            </QuestionBlock>

            <QuestionBlock label="Чи є у дитини алергії? (Якщо так - то вкажіть які)">
              <TextInputField
                value={formData.allergies}
                onChange={(v) => updateForm('allergies', v)}
                placeholder="Наприклад: лактоза, цитрусові..."
              />
            </QuestionBlock>

            <QuestionBlock label="Чи є у раціоні дитини дитяча суміш?">
              <div className="flex flex-col gap-3">
                {['Так', 'Ні'].map(v => (
                  <RadioOption key={v} label={v} selected={formData.formula === v} onClick={() => updateForm('formula', v)} />
                ))}
              </div>
            </QuestionBlock>

            <QuestionBlock label="Чи зареєстровані ви в електронній черзі в садок у Рівному?">
              <div className="flex flex-col gap-3">
                {['Так', 'Ні'].map(v => (
                  <RadioOption key={v} label={v} selected={formData.eQueue === v} onClick={() => updateForm('eQueue', v)} />
                ))}
              </div>
            </QuestionBlock>

            <QuestionBlock label="Чи маєте потребу у періодичному відвідуванні педіатра?" subtitle="(На майбутнє)">
              <div className="flex flex-col gap-3">
                {['Так', 'Ні'].map(v => (
                  <RadioOption key={v} label={v} selected={formData.pediatrist === v} onClick={() => updateForm('pediatrist', v)} />
                ))}
              </div>
            </QuestionBlock>
          </div>
        );

      case 2: // Про графік відвідування
        return (
          <div className="space-y-8 animate-fade-in">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-800 text-center mb-8">Про графік відвідування</h3>

            <QuestionBlock label="Який формат перебування вам ближчий?">
              <div className="grid grid-cols-1 gap-3">
                {[
                  'Повний день (без програми "єЯсла")',
                  'Повний день (з програмою "єЯсла")',
                  'Неповний день (без програми "єЯсла")',
                  'Неповний день (з програмою "єЯсла")',
                ].map(f => (
                  <CheckboxOption
                    key={f}
                    label={f}
                    selected={(formData.formats || []).includes(f)}
                    onClick={() => toggleArrayItem('formats', f)}
                  />
                ))}
              </div>
            </QuestionBlock>

            <QuestionBlock
              label="Позначте часові проміжки, в які б хотіли, щоб дитина перебувала в садочку"
              subtitle="Оберіть бажані часові проміжки"
            >
              <CheckboxGroupWithOther
                options={[
                  'Індивідуально до 4 годин',
                  'Перша половина дня (08:00-13:00)',
                  'Друга половина дня (13:00-18:00)',
                  'Повний день (8:00-18:00)',
                  'Розширений повний день (07:00-19:00)',
                ]}
                valueArr={formData.timeSlots}
                otherText={formData.timeSlotsOther}
                onToggle={(v) => toggleArrayItem('timeSlots', v)}
                onOtherChange={(v) => updateForm('timeSlotsOther', v)}
              />
            </QuestionBlock>

            <QuestionBlock label="В які дні тижня ви б хотіли відвідувати садочок?" subtitle="Відмітьте усі бажані дні">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця', 'Субота', 'Неділя'].map(day => (
                  <CheckboxOption
                    key={day}
                    label={day}
                    selected={(formData.days || []).includes(day)}
                    onClick={() => toggleArrayItem('days', day)}
                  />
                ))}
              </div>
            </QuestionBlock>
          </div>
        );

      case 3: // Очікування від простору
        return (
          <div className="space-y-8 animate-fade-in">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-800 text-center mb-8">Очікування від простору</h3>

            <QuestionBlock
              label="Що для вас найважливіше в перші роки життя дитини?"
              subtitle="Оберіть варіанти, які відгукуються"
            >
              <CheckboxGroupWithOther
                options={[
                  'Безпечна адаптація',
                  'Сенсорний розвиток',
                  'Мовленнєве середовище',
                  'Турбота та індивідуальний підхід',
                  'Соціалізація',
                ]}
                valueArr={formData.expectations}
                otherText={formData.expectationsOther}
                onToggle={(v) => toggleArrayItem('expectations', v)}
                onOtherChange={(v) => updateForm('expectationsOther', v)}
              />
            </QuestionBlock>

            <QuestionBlock
              label="Що для вас є червоним прапорцем у виборі садочка?"
              subtitle="А ми попіклуємось, щоб цього не було."
            >
              <TextInputField
                value={formData.redFlags}
                onChange={(v) => updateForm('redFlags', v)}
                placeholder="Опишіть свої побоювання..."
                multiline
              />
            </QuestionBlock>
          </div>
        );

      case 4: // Про вас
        return (
          <div className="space-y-8 animate-fade-in">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-800 text-center mb-3">Про вас</h3>
            <p className="text-slate-600 text-base sm:text-lg text-center max-w-2xl mx-auto mb-6 break-words">
              Нам важливо підтримувати та навчати не лише діток, а також давати найкращий досвід і для батьків та опікунів. Ми віримо, що турбота про дитину починається з турботи про батьків.
            </p>

            <QuestionBlock label="Що для вас є найціннішим у комунікації з простором, де навчається дитина?">
              <TextInputField
                value={formData.valueInComm}
                onChange={(v) => updateForm('valueInComm', v)}
                placeholder="Ваша думка..."
              />
            </QuestionBlock>

            <QuestionBlock label="Які виклики у вихованні дитини ви зараз відчуваєте?">
              <TextInputField
                value={formData.challenges}
                onChange={(v) => updateForm('challenges', v)}
                placeholder="Адаптація, харчування, соціалізація..."
              />
            </QuestionBlock>

            <QuestionBlock label="Чи було б вам цікаво відвідувати лекції або онлайн-сесії від експертів (педіатрів, психологів, педагогів)?">
              <div className="flex flex-col gap-3">
                {['Так, обов\'язково', 'Так, можливо', 'Поки не впевнені'].map(v => (
                  <RadioOption key={v} label={v} selected={formData.lecturesInterest === v} onClick={() => updateForm('lecturesInterest', v)} />
                ))}
              </div>
            </QuestionBlock>

            <QuestionBlock label="Які формати взаємодії для вас комфортніші?">
              <RadioGroupWithOther
                options={['Онлайн-лекції', 'Очні зустрічі в просторі']}
                value={formData.interactionFormats}
                otherText={formData.interactionFormatsOther}
                onSelect={(v) => updateForm('interactionFormats', v)}
                onOtherChange={(v) => updateForm('interactionFormatsOther', v)}
              />
            </QuestionBlock>

            <QuestionBlock label="Які питання або потреби у вихованні дитини ви хотіли б обговорювати з іншими батьками або експертами?">
              <TextInputField
                value={formData.parentQuestions}
                onChange={(v) => updateForm('parentQuestions', v)}
                placeholder="Ваші ідеї..."
                multiline
              />
            </QuestionBlock>
          </div>
        );

      case 5: // Про підтримку (поки legacy benefits, оновимо коли пришлеш скрін)
        return (
          <div className="space-y-8 animate-fade-in">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-800 text-center mb-8">Про підтримку</h3>

            <QuestionBlock label="Чи проінформовані ви про пільги для оплати харчування?">
              <div className="flex flex-col gap-3">
                {['Так, знаємо і користуємось', 'Так, але не знаємо як оформити', 'Ні, не знаємо'].map(v => (
                  <RadioOption key={v} label={v} selected={formData.benefits === v} onClick={() => updateForm('benefits', v)} />
                ))}
              </div>
            </QuestionBlock>
          </div>
        );

      case 6: // Контакти
        return (
          <div className="space-y-7 animate-fade-in">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-800 text-center mb-3">Контакти для зв'язку</h3>
            <p className="text-slate-500 text-sm text-center max-w-md mx-auto">Залиште свої контакти — ми зв'яжемося з вами найближчим часом.</p>

            <div className="space-y-5">
              <div>
                <label className="block font-semibold text-slate-700 mb-2">Ім'я одного з батьків *</label>
                <input type="text" value={formData.parentName || ''} onChange={e => updateForm('parentName', e.target.value)} className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 focus:border-teal-500 outline-none transition-colors" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block font-semibold text-slate-700 mb-2">Номер телефону *</label>
                  <input type="tel" value={formData.phone || ''} onChange={e => updateForm('phone', e.target.value)} className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 focus:border-teal-500 outline-none transition-colors" />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-2">Email</label>
                  <input type="email" value={formData.email || ''} onChange={e => updateForm('email', e.target.value)} className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 focus:border-teal-500 outline-none transition-colors" />
                </div>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-2">Ім'я дитини *</label>
                <input type="text" value={formData.childName || ''} onChange={e => updateForm('childName', e.target.value)} className="w-full px-5 py-4 rounded-2xl border-2 border-slate-200 focus:border-teal-500 outline-none transition-colors" />
              </div>

              <label className="flex items-start gap-3 text-sm text-slate-600 cursor-pointer select-none pt-2">
                <input
                  type="checkbox"
                  checked={!!formData.consent}
                  onChange={e => updateForm('consent', e.target.checked)}
                  className="mt-1 w-5 h-5 rounded border-slate-300 text-teal-500 focus:ring-teal-500 cursor-pointer shrink-0"
                />
                <span className="break-words">Надаю згоду на обробку персональних даних <span className="text-rose-500">*</span></span>
              </label>
            </div>
          </div>
        );

      case 7: // Дякуємо
        return (
          <div className="text-center py-12 animate-fade-in-up">
            <div className="inline-flex justify-center items-center w-24 h-24 bg-green-100 rounded-full mb-8">
              <Check className="w-12 h-12 text-green-500" />
            </div>
            <h3 className="text-3xl font-extrabold text-slate-800 mb-4">Дякуємо за ваші відповіді!</h3>
            <p className="text-slate-600 text-lg mb-10 max-w-md mx-auto break-words">
              Вашу анкету успішно надіслано. Адміністрація {brand} зв'яжеться з вами найближчим часом для узгодження деталей.
            </p>
            <button onClick={() => navigate('/')} className="bg-slate-100 text-slate-700 px-8 py-3 rounded-full font-bold hover:bg-slate-200 transition-colors">
              Повернутись на головну
            </button>
          </div>
        );

      default: return null;
    }
  };

  const isQuestionStep = step > 0 && step <= TOTAL_STEPS;
  const isFinal = step === TOTAL_STEPS;

  return (
    <div className="min-h-screen bg-[#FFFDF9] pt-28 pb-12 px-4 sm:px-6 flex items-start justify-center">
      <div className="w-full max-w-3xl bg-white rounded-[2.5rem] shadow-xl border border-slate-100 p-6 sm:p-10 lg:p-12 relative overflow-hidden">
        {isQuestionStep && (
          <div className="mb-10">
            <div className="flex justify-between items-center mb-2">
              <button onClick={prevStep} className="text-slate-400 hover:text-slate-700 flex items-center gap-1 transition-colors">
                <ArrowLeft className="w-4 h-4" /> Назад
              </button>
              <span className="text-sm font-bold text-teal-500">Крок {step} з {TOTAL_STEPS}</span>
            </div>
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <div className="bg-teal-500 h-full transition-all duration-500" style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}></div>
            </div>
          </div>
        )}

        {renderStepContent()}

        {isQuestionStep && (
          <div className="mt-12 flex flex-col items-end">
            {errorMsg && (
              <div className="mb-6 w-full p-4 bg-rose-50 border border-rose-200 text-rose-600 rounded-2xl flex items-center gap-3 animate-fade-in text-left">
                <ShieldCheck className="w-6 h-6 shrink-0" />
                <span className="font-medium break-words">{errorMsg}</span>
              </div>
            )}
            <button
              onClick={handleNext}
              disabled={isSubmitting}
              className="bg-teal-500 text-white px-10 py-4 rounded-full font-bold hover:bg-teal-600 transition-all shadow-md hover:shadow-lg flex items-center gap-2 disabled:opacity-70"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Відправка...
                </>
              ) : isFinal ? (
                <>
                  Відправити
                  <Send className="w-5 h-5" />
                </>
              ) : (
                <>
                  Далі
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const AIChatbot = ({ isOpen, setIsOpen, siteData }) => {
  const settings = siteData.settings || {};
  const brand = `${settings.nav_brand || 'ЗДО'} ${settings.nav_brand_accent || ''}`.trim();

  const greeting = `Вітаю! 👋 Я віртуальний помічник садочка ${brand}. Чим можу допомогти? Запитайте про набір, групи, харчування, документи — або що завгодно інше.`;

  const [messages, setMessages] = useState([{ role: 'model', text: greeting }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Як тільки приходять справжні дані з адмінки — оновлюємо привітання,
  // але тільки якщо користувач ще нічого не писав (щоб не стерти діалог).
  useEffect(() => {
    setMessages(prev => {
      if (prev.length === 1 && prev[0].role === 'model') {
        return [{ role: 'model', text: greeting }];
      }
      return prev;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brand]);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => scrollToBottom(), [messages]);

  // Усе спілкування з Gemini проходить через Django-проксі /api/chat/.
  // API-ключ ніколи не потрапляє у фронт — живе лише в env-змінних бекенду.
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = input.trim();
    const newMessages = [...messages, { role: 'user', text: userMessage }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      // Відсилаємо лише історію без вступного привітання
      const history = newMessages.slice(1).map(m => ({
        role: m.role === 'model' ? 'model' : 'user',
        text: m.text,
      }));

      const res = await fetch(`${API_BASE}/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok && data.text) {
        setMessages(prev => [...prev, { role: 'model', text: data.text }]);
        return;
      }

      // Сервер повернув помилку — складаємо інформативне повідомлення
      const header = data.error || 'Не вдалося отримати відповідь.';
      const details = data.details ? `\n\n📋 Деталі: «${data.details}»` : '';
      const code = data.status ? `\n🔢 Код: ${data.status}` : '';
      throw new Error(header + details + code);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'model',
        text: `Вибачте, сталася помилка 😔\n\n${error.message}\n\n📞 Або зателефонуйте: ${settings.phone || ''}`,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetChat = () => {
    setMessages([{ role: 'model', text: greeting }]);
  };

  // Блокуємо скрол body коли чат відкритий на мобільному (щоб не «двіжки» сторінки під ним)
  useEffect(() => {
    if (!isOpen) return;
    const isMobile = window.matchMedia('(max-width: 640px)').matches;
    if (!isMobile) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, [isOpen]);

  return (
    <>
      {/* Плаваюча кнопка для відкриття */}
      <button
        onClick={() => setIsOpen(true)}
        aria-label="Відкрити ШІ-помічника"
        className={`fixed bottom-6 right-6 w-14 h-14 sm:w-16 sm:h-16 bg-teal-500 text-white rounded-full shadow-2xl shadow-teal-500/30 flex items-center justify-center hover:bg-teal-600 hover:scale-110 active:scale-95 transition-all z-40 ${isOpen ? 'scale-0 pointer-events-none' : 'scale-100'}`}
      >
        <MessageCircle className="w-7 h-7 sm:w-8 sm:h-8" />
      </button>

      {/* Затемнення під чатом на мобільному */}
      <div
        className={`sm:hidden fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />

      {/* Сам чат:
          - на phone: повноекранний, виїжджає знизу
          - на tablet/desktop: плаваюче віконце 400×600 у правому нижньому куті */}
      <div
        className={`fixed z-50 bg-white shadow-2xl flex flex-col overflow-hidden
          inset-x-0 bottom-0 top-[10dvh] rounded-t-3xl
          sm:inset-auto sm:bottom-6 sm:right-6 sm:top-auto sm:w-[400px] sm:h-[600px] sm:max-h-[85vh] sm:rounded-3xl
          origin-bottom sm:origin-bottom-right transition-all duration-300
          ${isOpen
            ? 'translate-y-0 opacity-100 sm:scale-100'
            : 'translate-y-full opacity-0 pointer-events-none sm:translate-y-0 sm:scale-0'}`}
      >
        {/* Drag-індикатор зверху (для мобільного — підказка що це панель) */}
        <div className="sm:hidden flex justify-center pt-2 pb-1">
          <div className="w-12 h-1.5 rounded-full bg-slate-300"></div>
        </div>

        {/* Шапка */}
        <div className="bg-teal-500 p-4 flex justify-between items-center text-white">
          <div className="flex items-center gap-3 min-w-0">
            <div className="bg-white/20 p-1.5 rounded-full shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-bold leading-tight truncate">Помічник {brand}</h3>
              <p className="text-xs text-teal-100 leading-tight">Зазвичай відповідає миттєво</p>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={resetChat}
              title="Очистити діалог"
              aria-label="Очистити діалог"
              className="p-2 rounded-full hover:bg-white/20 active:scale-95 transition-all"
            >
              <X className="w-4 h-4 opacity-80" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              title="Закрити"
              aria-label="Закрити"
              className="p-2 rounded-full hover:bg-white/20 active:scale-95 transition-all"
            >
              <ChevronDown className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Стрічка повідомлень */}
        <div className="flex-grow p-4 overflow-y-auto bg-slate-50 space-y-3" style={{ WebkitOverflowScrolling: 'touch' }}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[88%] p-3.5 rounded-2xl text-[15px] sm:text-sm whitespace-pre-wrap break-words shadow-sm leading-relaxed ${msg.role === 'user' ? 'bg-amber-400 text-amber-950 rounded-br-md' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-md'}`}>
                {msg.text}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md p-3.5 shadow-sm flex items-center gap-2 text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin text-teal-500" />
                <span className="text-sm">друкую...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Інпут — товщий для зручної мобільної взаємодії; pb для safe area */}
        <div className="p-3 sm:p-3 bg-white border-t border-slate-100 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <div className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-full border border-slate-200 focus-within:border-teal-300 focus-within:ring-2 focus-within:ring-teal-100 transition-colors">
            <input
              type="text"
              inputMode="text"
              autoComplete="off"
              autoCorrect="on"
              placeholder="Ваше запитання..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              disabled={isLoading}
              className="flex-grow bg-transparent px-3 py-1 outline-none text-base sm:text-sm disabled:opacity-50 min-w-0"
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              aria-label="Відправити"
              className="bg-teal-500 hover:bg-teal-600 text-white p-3 rounded-full disabled:opacity-50 active:scale-95 transition-all shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

const DEFAULT_DATA = {
  settings: {
    phone: "+38 (0362) 12-34-56",
    email: "zdo52@ukr.net",
    address: "м. Рівне, ЗДО №52",
    map_url: "",
    facebook: "",
    instagram: "",
    telegram: "",
    threads: "",
    logo_navbar: "",
    logo_footer: "",
    nav_brand: "ЗДО",
    nav_brand_accent: "№52",
    nav_cta_text: "Заповнити анкету",
    footer_copyright: "Заклад дошкільної освіти №52 м. Рівного. Всі права захищено.",
  },
  content: {
    hero_badge: "Набір на 2026/2027 рік відкрито",
    hero_title: "Простір де зростає щастя",
    hero_title_accent: "щастя",
    hero_desc: "",
    hero_image: "",
    hero_btn_primary: "Детальніше про нас",
    hero_btn_secondary: "Контакти",
    hero_ai_btn_text: "Є питання? Запитай ШІ-помічника",
    hero_badge_value: "15+ років",
    hero_badge_label: "Досвіду та любові",
    about_kicker: "Про наш садок",
    about_title: "Місце, де цікаво рости",
    about_desc: "",
    directions_kicker: "Розвиток",
    directions_title: "Наші ключові напрямки",
    premises_title: "Приміщення",
    premises_subtitle: "",
    premises_desc: "",
    services_kicker: "Вікові групи",
    services_title: "Оберіть свій формат",
    faq_title: "Відповіді на часті питання",
    contact_form_title: "Написати нам",
    contact_form_btn: "Відправити",
  },
  about_cards: [],
  directions_first: [],
  directions_second: [],
  directions_gallery: [],
  directions_collage: [],
  premises: [],
  services: [],
  faqs: [],
};

export default function App() {
  const [path, navigate] = useRoute();
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [siteData, setSiteData] = useState(DEFAULT_DATA);

  useEffect(() => {
    fetch(`${API_BASE}/api/content/`)
      .then(res => res.json())
      .then(data => {
        setSiteData(prev => ({
          ...prev,
          ...data,
          settings: { ...prev.settings, ...(data.settings || {}) },
          content: { ...prev.content, ...(data.content || {}) },
          about_cards: data.about_cards || [],
          directions_first: data.directions_first || [],
          directions_second: data.directions_second || [],
          directions_gallery: data.directions_gallery || [],
          directions_collage: data.directions_collage || [],
          premises: data.premises || [],
          services: data.services || [],
          faqs: data.faqs || [],
        }));
      })
      .catch(err => console.error("Бекенд ще не запущено або помилка:", err));
  }, []);

  // Динамічно оновлюємо title вкладки і favicon коли підвантажились налаштування з адмінки
  useEffect(() => {
    const brand = `${siteData.settings.nav_brand || ''} ${siteData.settings.nav_brand_accent || ''}`.trim();
    if (brand) {
      document.title = `${brand} — Приватний дитячий садочок`;
    }
    const logoUrl = siteData.settings.logo_navbar;
    if (logoUrl) {
      let link = document.querySelector("link[rel~='icon']");
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      link.href = logoUrl;
    }
  }, [siteData.settings.nav_brand, siteData.settings.nav_brand_accent, siteData.settings.logo_navbar]);

  const isAnketa = path.startsWith('/anketa');

  return (
    <div className="min-h-screen bg-[#FFFDF9] text-slate-800 font-sans selection:bg-teal-200 selection:text-teal-900">
      <Navbar navigate={navigate} currentPath={path} settings={siteData.settings} />

      {isAnketa ? (
        <SurveyFlow navigate={navigate} siteData={siteData} />
      ) : (
        <>
          <main>
            <Hero onOpenChat={() => setIsChatOpen(true)} content={siteData.content} />
            <About content={siteData.content} cards={siteData.about_cards} highlights={siteData.content.about_highlights || []} />
            <Directions
              content={siteData.content}
              first={siteData.directions_first}
              second={siteData.directions_second}
              gallery={siteData.directions_gallery}
              collage={siteData.directions_collage}
            />
            <Premises content={siteData.content} slides={siteData.premises} />
            <Services onOpenSurvey={() => navigate('/anketa')} content={siteData.content} services={siteData.services} />
            <FAQ content={siteData.content} faqs={siteData.faqs} />
            <ContactAndMap settings={siteData.settings} content={siteData.content} />
          </main>
          <Footer settings={siteData.settings} />
        </>
      )}

      <AIChatbot isOpen={isChatOpen} setIsOpen={setIsChatOpen} siteData={siteData} />
    </div>
  );
}
