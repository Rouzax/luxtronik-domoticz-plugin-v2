# GitHub Hero Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a dark, techy single-page landing site for the Luxtronik Domoticz Plugin, deployed via GitHub Pages on the `gh-pages` branch.

**Architecture:** Plain HTML/CSS/JS — three static files (`index.html`, `style.css`, `script.js`) in a `docs/` directory. Dark theme with cyan accent. No build step, no dependencies.

**Tech Stack:** HTML5, CSS3 (custom properties, grid, flexbox), vanilla JS (lightbox only)

**Repo:** `https://github.com/Rouzax/luxtronik-domoticz-plugin-v2`

**Screenshot URLs:**
- Utility: `https://github.com/user-attachments/assets/2e36ea32-a578-4e54-835f-b9cfd6835e24`
- Temperature: `https://github.com/user-attachments/assets/2f9d1438-6572-4afe-9de3-2fe99d69ca8e`
- Switch: `https://github.com/user-attachments/assets/fa9195f6-0780-49e6-961f-196bc92405cb`

---

### Task 1: Project scaffold and CSS foundation

**Files:**
- Create: `site/index.html`
- Create: `site/style.css`
- Create: `site/script.js`

**Step 1: Create `site/style.css` with CSS custom properties and base styles**

```css
/* === Custom Properties === */
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: #1a2332;
    --bg-stats: #0f1623;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent: #06b6d4;
    --accent-glow: rgba(6, 182, 212, 0.3);
    --accent-dim: rgba(6, 182, 212, 0.1);
    --border: rgba(6, 182, 212, 0.15);
    --border-hover: rgba(6, 182, 212, 0.4);
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    --max-width: 1100px;
}

/* === Reset & Base === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
    font-family: var(--font-sans);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

img { max-width: 100%; height: auto; display: block; }

.container { max-width: var(--max-width); margin: 0 auto; padding: 0 1.5rem; }
```

**Step 2: Create `site/index.html` with boilerplate and all section stubs**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Luxtronik Domoticz Plugin v2</title>
    <meta name="description" content="Real-time heat pump monitoring and control for Domoticz. 62 devices, 5 languages, smart COP tracking.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- Hero -->
    <section id="hero" class="hero"></section>

    <!-- Stats -->
    <section id="stats" class="stats"></section>

    <!-- Features -->
    <section id="features" class="features"></section>

    <!-- Screenshots -->
    <section id="screenshots" class="screenshots"></section>

    <!-- Footer -->
    <footer id="footer" class="footer"></footer>

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox" hidden></div>

    <script src="script.js"></script>
</body>
</html>
```

**Step 3: Create empty `site/script.js`**

```js
// Lightbox functionality — implemented in Task 5
```

**Step 4: Verify files exist**

Run: `ls -la site/`
Expected: `index.html`, `style.css`, `script.js`

**Step 5: Commit**

```bash
git add site/
git commit -m "feat(site): scaffold hero page with CSS foundation"
```

---

### Task 2: Hero banner section

**Files:**
- Modify: `site/index.html` — hero section
- Modify: `site/style.css` — hero styles

**Step 1: Add hero HTML content**

Replace the hero section stub in `index.html` with:

```html
<section id="hero" class="hero">
    <div class="hero__grid-overlay"></div>
    <div class="container hero__content">
        <span class="hero__version">v2.0.2</span>
        <h1 class="hero__title">Luxtronik<span class="hero__title-accent">Ex</span></h1>
        <p class="hero__tagline">Real-time heat pump monitoring & control for Domoticz</p>
        <div class="hero__actions">
            <a href="https://github.com/Rouzax/luxtronik-domoticz-plugin-v2" class="btn btn--primary">View on GitHub</a>
            <a href="https://github.com/Rouzax/luxtronik-domoticz-plugin-v2/releases/latest" class="btn btn--outline">Download Latest</a>
        </div>
    </div>
</section>
```

**Step 2: Add hero CSS**

Append to `style.css`:

```css
/* === Hero === */
.hero {
    position: relative;
    min-height: 90vh;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    overflow: hidden;
    background: radial-gradient(ellipse at 50% 0%, rgba(6, 182, 212, 0.08) 0%, transparent 60%),
                linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.hero__grid-overlay {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 60px 60px;
    opacity: 0.4;
    mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
    -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
}

.hero__content { position: relative; z-index: 1; }

.hero__version {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.25rem 1rem;
    margin-bottom: 1.5rem;
}

.hero__title {
    font-size: clamp(3rem, 8vw, 6rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 1rem;
}

.hero__title-accent {
    color: var(--accent);
    text-shadow: 0 0 30px var(--accent-glow);
}

.hero__tagline {
    font-size: clamp(1.1rem, 2.5vw, 1.4rem);
    color: var(--text-secondary);
    max-width: 600px;
    margin: 0 auto 2.5rem;
}

.hero__actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }

/* === Buttons === */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.75rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.2s ease;
    cursor: pointer;
    text-decoration: none;
}

.btn--primary {
    background: var(--accent);
    color: var(--bg-primary);
}
.btn--primary:hover {
    background: #22d3ee;
    box-shadow: 0 0 20px var(--accent-glow);
    text-decoration: none;
}

.btn--outline {
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--border-hover);
}
.btn--outline:hover {
    background: var(--accent-dim);
    border-color: var(--accent);
    text-decoration: none;
}
```

**Step 3: Open in browser and verify**

Run: `python3 -m http.server 8001 -d site/ &` then check `http://localhost:8001`
Expected: Dark page, centered title with "Ex" in cyan glow, grid overlay, two buttons

**Step 4: Commit**

```bash
git add site/
git commit -m "feat(site): add hero banner with grid overlay and CTAs"
```

---

### Task 3: Stats bar section

**Files:**
- Modify: `site/index.html` — stats section
- Modify: `site/style.css` — stats styles

**Step 1: Add stats HTML**

Replace the stats section stub:

```html
<section id="stats" class="stats">
    <div class="container stats__grid">
        <div class="stats__item">
            <span class="stats__number">62</span>
            <span class="stats__label">Devices & Sensors</span>
        </div>
        <div class="stats__item">
            <span class="stats__number">5</span>
            <span class="stats__label">Languages</span>
        </div>
        <div class="stats__item">
            <span class="stats__number">14</span>
            <span class="stats__label">Device Groups</span>
        </div>
        <div class="stats__item">
            <span class="stats__number">Real-time</span>
            <span class="stats__label">Monitoring</span>
        </div>
    </div>
</section>
```

**Step 2: Add stats CSS**

```css
/* === Stats Bar === */
.stats {
    background: var(--bg-stats);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 2.5rem 0;
}

.stats__grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
    text-align: center;
}

.stats__item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    position: relative;
}

.stats__item:not(:last-child)::after {
    content: '';
    position: absolute;
    right: -1rem;
    top: 10%;
    height: 80%;
    width: 1px;
    background: var(--border);
}

.stats__number {
    font-size: clamp(1.5rem, 3vw, 2.2rem);
    font-weight: 800;
    color: var(--accent);
    font-family: var(--font-mono);
}

.stats__label {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

@media (max-width: 640px) {
    .stats__grid { grid-template-columns: repeat(2, 1fr); }
    .stats__item:nth-child(2)::after { display: none; }
}
```

**Step 3: Verify in browser**

Expected: Horizontal stats strip below hero with cyan numbers, subtle dividers

**Step 4: Commit**

```bash
git add site/
git commit -m "feat(site): add key stats bar section"
```

---

### Task 4: Feature highlights section

**Files:**
- Modify: `site/index.html` — features section
- Modify: `site/style.css` — feature card styles

**Step 1: Add features HTML**

Replace the features section stub:

```html
<section id="features" class="features">
    <div class="container">
        <h2 class="section__title">Features</h2>
        <div class="features__grid">
            <div class="feature-card">
                <div class="feature-card__icon">&#x26A1;</div>
                <h3 class="feature-card__title">Smart COP Tracking</h3>
                <p class="feature-card__desc">Separate efficiency metrics for heating, hot water, and combined &mdash; only measured during steady-state operation.</p>
            </div>
            <div class="feature-card">
                <div class="feature-card__icon">&#x1F6E1;</div>
                <h3 class="feature-card__title">Intelligent Gating</h3>
                <p class="feature-card__desc">Blocks sensor updates when the compressor is idle, preventing misleading readings from skewing your data.</p>
            </div>
            <div class="feature-card">
                <div class="feature-card__icon">&#x1F512;</div>
                <h3 class="feature-card__title">Secure Write Control</h3>
                <p class="feature-card__desc">All commands validated against an explicit allowlist before touching your heat pump&rsquo;s EEPROM.</p>
            </div>
            <div class="feature-card">
                <div class="feature-card__icon">&#x1F504;</div>
                <h3 class="feature-card__title">Multi-Instance Support</h3>
                <p class="feature-card__desc">Run multiple plugin instances for homes with more than one heat pump, each fully independent.</p>
            </div>
            <div class="feature-card">
                <div class="feature-card__icon">&#x1F310;</div>
                <h3 class="feature-card__title">5 Languages</h3>
                <p class="feature-card__desc">Full translations for EN, NL, DE, FR, and PL &mdash; including device names, descriptions, and selector options.</p>
            </div>
            <div class="feature-card">
                <div class="feature-card__icon">&#x1F517;</div>
                <h3 class="feature-card__title">Stable Device IDs</h3>
                <p class="feature-card__desc">Hardware-based identifiers that persist across IP changes and device renames &mdash; no more broken history.</p>
            </div>
        </div>
    </div>
</section>
```

**Step 2: Add feature card CSS**

```css
/* === Section Title === */
.section__title {
    text-align: center;
    font-size: clamp(1.8rem, 4vw, 2.5rem);
    font-weight: 700;
    margin-bottom: 3rem;
    color: var(--text-primary);
}

/* === Features === */
.features {
    padding: 5rem 0;
    background: var(--bg-primary);
}

.features__grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
}

.feature-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 0 20px var(--accent-dim);
}

.feature-card__icon {
    font-size: 1.8rem;
    margin-bottom: 0.75rem;
}

.feature-card__title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.feature-card__desc {
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.6;
}

@media (max-width: 900px) {
    .features__grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
    .features__grid { grid-template-columns: 1fr; }
}
```

**Step 3: Verify in browser**

Expected: 3-column grid of cards with icons, hover glow effect, responsive

**Step 4: Commit**

```bash
git add site/
git commit -m "feat(site): add feature highlights grid"
```

---

### Task 5: Screenshots gallery with lightbox

**Files:**
- Modify: `site/index.html` — screenshots section + lightbox markup
- Modify: `site/style.css` — gallery + lightbox styles
- Modify: `site/script.js` — lightbox logic

**Step 1: Add screenshots HTML**

Replace the screenshots section stub:

```html
<section id="screenshots" class="screenshots">
    <div class="container">
        <h2 class="section__title">In Action</h2>
        <div class="screenshots__grid">
            <figure class="screenshot" data-full="https://github.com/user-attachments/assets/2e36ea32-a578-4e54-835f-b9cfd6835e24">
                <img src="https://github.com/user-attachments/assets/2e36ea32-a578-4e54-835f-b9cfd6835e24" alt="Utility Devices in Domoticz" loading="lazy">
                <figcaption>Utility Devices</figcaption>
            </figure>
            <figure class="screenshot" data-full="https://github.com/user-attachments/assets/2f9d1438-6572-4afe-9de3-2fe99d69ca8e">
                <img src="https://github.com/user-attachments/assets/2f9d1438-6572-4afe-9de3-2fe99d69ca8e" alt="Temperature Devices in Domoticz" loading="lazy">
                <figcaption>Temperature Devices</figcaption>
            </figure>
            <figure class="screenshot" data-full="https://github.com/user-attachments/assets/fa9195f6-0780-49e6-961f-196bc92405cb">
                <img src="https://github.com/user-attachments/assets/fa9195f6-0780-49e6-961f-196bc92405cb" alt="Switch Devices in Domoticz" loading="lazy">
                <figcaption>Switch Devices</figcaption>
            </figure>
        </div>
    </div>
</section>
```

**Step 2: Replace lightbox placeholder HTML**

```html
<div id="lightbox" class="lightbox" hidden>
    <button class="lightbox__close" aria-label="Close">&times;</button>
    <img class="lightbox__img" src="" alt="">
</div>
```

**Step 3: Add gallery + lightbox CSS**

```css
/* === Screenshots === */
.screenshots {
    padding: 5rem 0;
    background: var(--bg-secondary);
}

.screenshots__grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
}

.screenshot {
    cursor: pointer;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--border);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.screenshot:hover {
    border-color: var(--border-hover);
    box-shadow: 0 0 20px var(--accent-dim);
}

.screenshot img {
    width: 100%;
    display: block;
}

.screenshot figcaption {
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: var(--text-muted);
    background: var(--bg-card);
    text-align: center;
}

@media (max-width: 900px) {
    .screenshots__grid { grid-template-columns: 1fr; max-width: 600px; margin: 0 auto; }
}

/* === Lightbox === */
.lightbox {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.lightbox[hidden] { display: none; }

.lightbox__img {
    max-width: 90vw;
    max-height: 90vh;
    border-radius: 8px;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
}

.lightbox__close {
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
    background: none;
    border: none;
    color: var(--text-primary);
    font-size: 2rem;
    cursor: pointer;
    line-height: 1;
    padding: 0.5rem;
}
```

**Step 4: Implement lightbox JS in `site/script.js`**

```js
(function () {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = lightbox.querySelector('.lightbox__img');
    const lightboxClose = lightbox.querySelector('.lightbox__close');

    document.querySelectorAll('.screenshot').forEach(function (fig) {
        fig.addEventListener('click', function () {
            lightboxImg.src = fig.dataset.full;
            lightboxImg.alt = fig.querySelector('img').alt;
            lightbox.hidden = false;
        });
    });

    lightboxClose.addEventListener('click', function () {
        lightbox.hidden = true;
        lightboxImg.src = '';
    });

    lightbox.addEventListener('click', function (e) {
        if (e.target === lightbox) {
            lightbox.hidden = true;
            lightboxImg.src = '';
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !lightbox.hidden) {
            lightbox.hidden = true;
            lightboxImg.src = '';
        }
    });
})();
```

**Step 5: Verify in browser**

Expected: 3-column screenshot grid, clicking opens full-size in dark overlay, Escape/click-outside closes

**Step 6: Commit**

```bash
git add site/
git commit -m "feat(site): add screenshots gallery with lightbox"
```

---

### Task 6: Footer section

**Files:**
- Modify: `site/index.html` — footer section
- Modify: `site/style.css` — footer styles

**Step 1: Add footer HTML**

Replace the footer stub:

```html
<footer id="footer" class="footer">
    <div class="container footer__content">
        <div class="footer__brand">
            <span class="footer__name">Luxtronik<span class="hero__title-accent">Ex</span></span>
            <span class="footer__sub">Made for Domoticz</span>
        </div>
        <nav class="footer__links">
            <a href="https://github.com/Rouzax/luxtronik-domoticz-plugin-v2">GitHub</a>
            <a href="https://github.com/Rouzax/luxtronik-domoticz-plugin-v2/releases">Releases</a>
            <a href="https://github.com/Rouzax/luxtronik-domoticz-plugin-v2/issues">Issues</a>
        </nav>
        <span class="footer__version">v2.0.2</span>
    </div>
</footer>
```

**Step 2: Add footer CSS**

```css
/* === Footer === */
.footer {
    padding: 2.5rem 0;
    background: var(--bg-primary);
    border-top: 1px solid var(--border);
}

.footer__content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
}

.footer__brand {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.footer__name {
    font-weight: 700;
    font-size: 1.1rem;
}

.footer__sub {
    font-size: 0.8rem;
    color: var(--text-muted);
}

.footer__links {
    display: flex;
    gap: 1.5rem;
}

.footer__links a {
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.footer__links a:hover { color: var(--accent); }

.footer__version {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--text-muted);
}

@media (max-width: 640px) {
    .footer__content { flex-direction: column; text-align: center; }
}
```

**Step 3: Verify in browser**

Expected: Clean footer with brand, nav links, version

**Step 4: Commit**

```bash
git add site/
git commit -m "feat(site): add footer section"
```

---

### Task 7: Deploy to gh-pages

**Step 1: Verify the complete page looks correct**

Open `http://localhost:8001` and scroll through all sections. Check mobile responsiveness at 375px width.

**Step 2: Configure GitHub Pages**

Enable GitHub Pages in repo settings to serve from `gh-pages` branch root, OR use `gh-pages` with the site files at root.

Create the `gh-pages` branch with only the site files:

```bash
git subtree split --prefix site -b gh-pages
git push origin gh-pages
```

Alternatively, push the `site/` contents to a `gh-pages` branch:

```bash
cd site
git init
git checkout -b gh-pages
git add .
git commit -m "deploy: hero page"
git remote add origin https://github.com/Rouzax/luxtronik-domoticz-plugin-v2.git
git push origin gh-pages --force
cd ..
rm -rf site/.git
```

**Step 3: Enable GitHub Pages**

Run: `gh api repos/Rouzax/luxtronik-domoticz-plugin-v2/pages -X POST -f source.branch=gh-pages -f source.path=/`

Or enable manually in Settings > Pages > Source: `gh-pages` branch, `/` root.

**Step 4: Verify deployment**

Expected URL: `https://rouzax.github.io/luxtronik-domoticz-plugin-v2/`

**Step 5: Commit any remaining changes on main**

```bash
git add .
git commit -m "feat(site): complete hero page for GitHub Pages deployment"
```
