(function () {
  var cache = null;
  var pending = null;
  var categories = [
    { prefix: 'account-sign-in', label: 'Login Issues' },
    { prefix: 'wi-fi', label: 'Connectivity Issues' },
    { prefix: 'chrome', label: 'Browser Issues' },
    { prefix: 'printer', label: 'Hardware Issues' }
  ];
  function loadIndex(url) {
    if (cache) return Promise.resolve(cache);
    if (!pending) {
      pending = fetch(url).then(function (response) {
        if (!response.ok) throw new Error('Search index failed to load');
        return response.json();
      }).then(function (data) {
        cache = Array.isArray(data) ? data : [];
        return cache;
      }).catch(function () {
        cache = [];
        return cache;
      });
    }
    return pending;
  }
  function score(item, query) {
    if (item.title === query) return 100;
    if (item.keywords.indexOf(query) !== -1) return 70;
    if (item.title.indexOf(query) !== -1) return 40;
    if (item.keywords.some(function (keyword) { return keyword.indexOf(query) !== -1; })) return 40;
    return 0;
  }
  function title(text) {
    return text.split('-').map(function (word) { return word.charAt(0).toUpperCase() + word.slice(1); }).join(' ');
  }
  function category(item) {
    var match = categories.find(function (entry) { return item.title.indexOf(entry.prefix) === 0; });
    return match ? match.label : (item.lang === 'es' ? 'Spanish' : 'English');
  }
  function rank(entries) {
    return entries.sort(function (a, b) { return b.score - a.score || a.index - b.index; });
  }
  function attachSearch(root) {
    var input = root.querySelector('.site-search-input');
    var results = root.querySelector('.site-search-results');
    if (!input || !results) return;
    var timer = null;
    var indexUrl = input.getAttribute('data-search-index') || 'assets/search-index.json';
    function render(items, query) {
      if (!query) {
        results.innerHTML = '';
        results.classList.remove('is-visible');
        return;
      }
      if (!items.length) {
        results.innerHTML = '<div class="search-result"><strong>No matching fixes found.</strong></div>';
        results.classList.add('is-visible');
        return;
      }
      results.innerHTML = items.map(function (item) {
        return '<a class="search-result" href="' + input.dataset.urlPrefix + item.url + '"><strong>' + title(item.title) + '</strong><span>' + category(item) + ' | ' + item.lang.toUpperCase() + '</span></a>';
      }).join('');
      results.classList.add('is-visible');
    }
    function run() {
      var query = input.value.trim().toLowerCase();
      loadIndex(indexUrl).then(function (index) {
        var matches = rank(index.map(function (item, index) {
          return { item: item, score: score(item, query), index: index };
        }).filter(function (entry) { return entry.score > 0; })).slice(0, 10).map(function (entry) { return entry.item; });
        render(matches, query);
      });
    }
    input.addEventListener('input', function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(run, 150);
    });
    input.addEventListener('focus', function () { if (input.value.trim()) run(); });
    document.addEventListener('click', function (event) {
      if (!event.target.closest('.site-search')) results.classList.remove('is-visible');
    });
    loadIndex(indexUrl);
  }
  document.querySelectorAll('.site-search').forEach(attachSearch);
})();
