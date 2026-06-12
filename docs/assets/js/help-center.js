(() => {
  const state = { index: [], active: -1, browsePage: 0, browseCategory: 'all', lang: localStorage.getItem('dp_lang') || 'all' };
  const maxResults = 50;
  const pageSize = 50;
  const labels = {
    all: 'All languages',
    en: 'English',
    es: 'Espanol'
  };
  const categoryLabels = {
    all: 'All categories',
    network: 'WiFi / Network issues',
    auth: 'Login / Authentication',
    browser: 'Chrome / Browser errors',
    os: 'Windows / OS issues',
    device: 'Device issues',
    printer: 'Printer issues'
  };
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
  const normalize = (value) => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const score = (item, query) => {
    const hay = normalize(`${item.title} ${item.category} ${item.slug}`);
    const q = normalize(query.trim());
    if (!q) return 0;
    if (hay.includes(q)) return 100 - Math.min(hay.indexOf(q), 30);
    let cursor = 0;
    let points = 0;
    for (const ch of q) {
      const found = hay.indexOf(ch, cursor);
      if (found === -1) return 0;
      points += Math.max(1, 12 - (found - cursor));
      cursor = found + 1;
    }
    return points;
  };
  const highlight = (title, query) => {
    const q = query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (!q) return escapeHtml(title);
    return escapeHtml(title).replace(new RegExp(`(${q})`, 'ig'), '<mark>$1</mark>');
  };
  const itemUrl = (item) => `${item.lang}/${item.slug}.html`;
  const renderResults = (query) => {
    const box = $('search-results');
    if (!box) return;
    state.active = -1;
    if (!query.trim()) {
      box.innerHTML = '';
      return;
    }
    const results = state.index
      .map((item) => ({ item, points: score(item, query) }))
      .filter((entry) => entry.points > 0 && (state.lang === 'all' || entry.item.lang === state.lang))
      .sort((a, b) => b.points - a.points || a.item.title.localeCompare(b.item.title))
      .slice(0, maxResults);
    box.innerHTML = results.map(({ item }, index) => `
      <a class="result-link fade-in" id="result-${index}" href="${itemUrl(item)}" role="option" aria-selected="false">
        <strong>${highlight(item.title, query)}</strong>
        <span class="result-meta"><span>${labels[item.lang]}</span><span>${categoryLabels[item.category]}</span></span>
      </a>
    `).join('') || '<p>No close matches yet. Try fewer words.</p>';
  };
  const moveActive = (delta) => {
    const options = Array.from(document.querySelectorAll('.result-link'));
    if (!options.length) return;
    state.active = (state.active + delta + options.length) % options.length;
    options.forEach((option, index) => option.setAttribute('aria-selected', String(index === state.active)));
    options[state.active].scrollIntoView({ block: 'nearest' });
  };
  const renderBrowse = () => {
    const list = $('browse-list');
    const count = $('browse-count');
    if (!list) return;
    const filtered = state.index.filter((item) =>
      (state.browseCategory === 'all' || item.category === state.browseCategory) &&
      (state.lang === 'all' || item.lang === state.lang)
    );
    const start = state.browsePage * pageSize;
    const visible = filtered.slice(start, start + pageSize);
    list.innerHTML = visible.map((item) => `
      <a class="browse-item" href="${itemUrl(item)}">
        <strong>${escapeHtml(item.title)}</strong>
        <span class="result-meta"><span>${labels[item.lang]}</span><span>${categoryLabels[item.category]}</span></span>
      </a>
    `).join('');
    if (count) count.textContent = `${filtered.length} fixes, showing ${visible.length}`;
    const prev = $('browse-prev');
    const next = $('browse-next');
    if (prev) prev.disabled = state.browsePage === 0;
    if (next) next.disabled = start + pageSize >= filtered.length;
  };
  const setup = async () => {
    const response = await fetch('assets/search-index.json');
    state.index = await response.json();
    const input = $('help-search');
    const lang = $('language-filter');
    const category = $('browse-category');
    if (lang) {
      lang.value = state.lang;
      lang.addEventListener('change', () => {
        state.lang = lang.value;
        localStorage.setItem('dp_lang', state.lang);
        renderResults(input ? input.value : '');
        renderBrowse();
      });
    }
    if (input) {
      let timer = 0;
      input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => renderResults(input.value), 110);
      });
      input.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowDown') { event.preventDefault(); moveActive(1); }
        if (event.key === 'ArrowUp') { event.preventDefault(); moveActive(-1); }
        if (event.key === 'Enter' && state.active >= 0) {
          const selected = document.getElementById(`result-${state.active}`);
          if (selected) selected.click();
        }
      });
      input.focus({ preventScroll: true });
    }
    document.querySelectorAll('[data-category]').forEach((link) => {
      link.addEventListener('click', () => {
        state.browseCategory = link.getAttribute('data-category') || 'all';
        state.browsePage = 0;
        const panel = $('browse-panel');
        if (panel) panel.dataset.open = 'true';
        if (category) category.value = state.browseCategory;
        renderBrowse();
      });
    });
    const toggle = $('browse-toggle');
    if (toggle) toggle.addEventListener('click', () => {
      const panel = $('browse-panel');
      if (panel) panel.dataset.open = panel.dataset.open === 'true' ? 'false' : 'true';
      renderBrowse();
    });
    if (category) category.addEventListener('change', () => {
      state.browseCategory = category.value;
      state.browsePage = 0;
      renderBrowse();
    });
    const prev = $('browse-prev');
    const next = $('browse-next');
    if (prev) prev.addEventListener('click', () => { state.browsePage = Math.max(0, state.browsePage - 1); renderBrowse(); });
    if (next) next.addEventListener('click', () => { state.browsePage += 1; renderBrowse(); });
    renderBrowse();
  };
  setup().catch(() => {
    const box = $('search-results');
    if (box) box.innerHTML = '<p>Search is not available right now. Browse by category below.</p>';
  });
})();
