/* ============================================================
   Secure Pass Pro — main.js
   - Animated shield strength indicator
   - Password generator widget demo
   - Scroll reveal
   - Install tab switcher
   - Copy to clipboard
   - Nav scroll state
============================================================ */

'use strict';

/* ── SHIELD STRENGTH ANIMATION ─────────────────────────── */
const PASSWORDS = [
  { text: 'qwerty',           strength: 0 },
  { text: 'P@ss123',          strength: 1 },
  { text: 'M4xim#2025!',      strength: 2 },
  { text: 'kX9#mP2@qL5!zR8$', strength: 3 },
];

const STRENGTH_CONFIG = [
  { label: 'Слабый',    color: '#ef4444', bars: 1, shieldColor: '#ef4444' },
  { label: 'Средний',   color: '#f97316', bars: 2, shieldColor: '#f97316' },
  { label: 'Хороший',   color: '#eab308', bars: 3, shieldColor: '#eab308' },
  { label: 'Надёжный',  color: '#22c55e', bars: 4, shieldColor: '#22c55e' },
];

let pwIndex = 0;
let isAnimating = false;

function updateShieldWidget(idx) {
  const cfg = STRENGTH_CONFIG[idx];
  const pw  = PASSWORDS[idx];

  // password text
  const pwText = document.getElementById('widget-pw-text');
  if (pwText) pwText.textContent = pw.text;

  // strength bars
  const bars = document.querySelectorAll('.strength-bar');
  bars.forEach((bar, i) => {
    bar.style.background = i < cfg.bars ? cfg.color : 'var(--border)';
    bar.style.transition = `background 0.35s ease ${i * 0.06}s`;
  });

  // strength label
  const valEl = document.getElementById('strength-val');
  if (valEl) {
    valEl.textContent = cfg.label;
    valEl.style.color = cfg.color;
  }

  // shield SVG fill + glow
  const shieldPath = document.getElementById('shield-path');
  const shieldDisplay = document.querySelector('.shield-display');
  if (shieldPath) {
    shieldPath.style.transition = 'fill 0.4s ease';
    shieldPath.style.fill = cfg.shieldColor;
  }
  if (shieldDisplay) {
    shieldDisplay.style.setProperty('--shield-color', cfg.shieldColor);
    const svg = shieldDisplay.querySelector('.shield-svg');
    if (svg) svg.style.filter = `drop-shadow(0 0 16px ${cfg.shieldColor}88)`;
  }
}

function cyclePasswords() {
  if (isAnimating) return;
  isAnimating = true;

  const pwText = document.getElementById('widget-pw-text');
  if (pwText) {
    pwText.style.opacity = '0';
    pwText.style.transform = 'translateY(-6px)';
    pwText.style.transition = 'opacity 0.25s, transform 0.25s';
  }

  setTimeout(() => {
    pwIndex = (pwIndex + 1) % PASSWORDS.length;
    updateShieldWidget(pwIndex);

    if (pwText) {
      pwText.style.opacity = '1';
      pwText.style.transform = 'translateY(0)';
    }

    setTimeout(() => { isAnimating = false; }, 400);
  }, 250);
}

// Auto-cycle every 2.4s
function startShieldCycle() {
  updateShieldWidget(0);
  setInterval(cyclePasswords, 2400);
}

/* ── SCREENSHOT TOGGLE ─────────────────────────────────── */
function initScreenshotToggle() {
  const btns      = document.querySelectorAll('.scr-btn');
  const imgDark   = document.getElementById('scr-dark');
  const imgLight  = document.getElementById('scr-light');
  const caption   = document.getElementById('scr-caption');

  const captions = {
    dark:  '🟢 Надёжный пароль · Стойкость: ~2.9e+39 · столетия на взлом',
    light: '🟢 Надёжный пароль · Тёмная и светлая тема на выбор',
  };

  function switchTo(theme) {
    btns.forEach(b => b.classList.toggle('active', b.dataset.scr === theme));

    const showDark  = theme === 'dark';
    const showLight = theme === 'light';

    if (imgDark)  imgDark.classList.toggle('active', showDark);
    if (imgLight) imgLight.classList.toggle('active', showLight);
    if (caption)  caption.textContent = captions[theme] || '';
  }

  btns.forEach(btn => {
    btn.addEventListener('click', () => switchTo(btn.dataset.scr));
  });

  // Auto-cycle every 4s
  let current = 'dark';
  setInterval(() => {
    current = current === 'dark' ? 'light' : 'dark';
    switchTo(current);
  }, 4000);
}

/* ── GENERATE BUTTON CLICK (no-op, widget removed) ──────── */
function initGenerateBtn() { /* screenshot showcase, no widget */ }
function initWidgetCopy()   { /* screenshot showcase, no widget */ }

/* ── CODE BLOCK COPY ───────────────────────────────────── */
function initCodeCopy() {
  document.querySelectorAll('.code-copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const block = btn.closest('.code-block');
      if (!block) return;
      const code = block.querySelector('pre code');
      if (!code) return;
      const text = code.innerText || code.textContent;
      navigator.clipboard.writeText(text).catch(() => {});
      const orig = btn.textContent;
      btn.textContent = '✓ Скопировано';
      setTimeout(() => { btn.textContent = orig; }, 1500);
    });
  });
}

/* ── INSTALL TABS ──────────────────────────────────────── */
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;

      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const panel = document.getElementById(`tab-${target}`);
      if (panel) panel.classList.add('active');
    });
  });
}

/* ── SCROLL REVEAL ─────────────────────────────────────── */
function initScrollReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(el => el.classList.add('visible'));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(el => observer.observe(el));
}

/* ── STATS COUNTER ANIMATION ───────────────────────────── */
function animateCounter(el, target, suffix = '') {
  const duration = 1400;
  const start = performance.now();
  const isFloat = String(target).includes('.');
  const from = 0;

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const val = from + (target - from) * ease;

    el.textContent = isFloat
      ? val.toFixed(1) + suffix
      : Math.round(val) + suffix;

    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function initCounters() {
  const statEls = document.querySelectorAll('.stat-num[data-count]');
  if (!('IntersectionObserver' in window)) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseFloat(el.dataset.count);
        const suffix = el.dataset.suffix || '';
        animateCounter(el, target, suffix);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  statEls.forEach(el => observer.observe(el));
}

/* ── NAV SCROLL STATE ──────────────────────────────────── */
function initNav() {
  const nav = document.querySelector('nav');
  if (!nav) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      nav.style.borderBottomColor = 'rgba(30, 37, 64, 0.8)';
    } else {
      nav.style.borderBottomColor = 'var(--border)';
    }
  }, { passive: true });
}

/* ── MOBILE NAV TOGGLE ─────────────────────────────────── */
function initMobileNav() {
  const toggle = document.getElementById('nav-toggle');
  const links  = document.getElementById('nav-links');
  if (!toggle || !links) return;

  toggle.addEventListener('click', () => {
    const open = links.style.display === 'flex';
    links.style.display = open ? '' : 'flex';
    links.style.flexDirection = 'column';
    links.style.position = 'absolute';
    links.style.top = '64px';
    links.style.left = '0';
    links.style.right = '0';
    links.style.background = 'var(--bg-card)';
    links.style.padding = '20px 24px';
    links.style.borderBottom = '1px solid var(--border)';
    toggle.textContent = open ? '☰' : '✕';
  });

  // Close on link click
  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      links.style.display = '';
      toggle.textContent = '☰';
    });
  });
}

/* ── SMOOTH ANCHOR SCROLL ──────────────────────────────── */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const id = a.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
}

/* ── SCROLL TO TOP ─────────────────────────────────────── */
function initScrollTop() {
  const btn = document.getElementById('scroll-top');
  if (!btn) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }, { passive: true });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ── HERO WIDGET (DEPRECATED, kept for compatibility) ── */
function initHeroWidget() {
  // Widget removed in favor of screenshot showcase
  // Keeping function to avoid errors if called
}

/* ── INIT ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Start shield animation
  startShieldCycle();
  
  // Initialize all features
  initScreenshotToggle();
  initGenerateBtn();
  initWidgetCopy();
  initCodeCopy();
  initTabs();
  initScrollReveal();
  initCounters();
  initNav();
  initMobileNav();
  initSmoothScroll();
  initScrollTop();
  initHeroWidget();
});

// Also run on load in case DOMContentLoaded already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  // Already loaded, but our DOMContentLoaded handler will handle it
}