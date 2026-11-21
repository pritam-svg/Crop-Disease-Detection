(() => {
  const translations = {
    en: {heading:'Overview dashboard',total:'Total completed scans',healthy:'Healthy scans',diseased:'Diseased scans',inconclusive:'Inconclusive scans',categories:'Recognized categories',activity:'Scan activity',distribution:'Detected disease distribution',recent:'Recent analyses'},
    bn: {heading:'ফসলের স্বাস্থ্য ড্যাশবোর্ড',total:'মোট সম্পন্ন স্ক্যান',healthy:'সুস্থ স্ক্যান',diseased:'রোগ শনাক্ত স্ক্যান',inconclusive:'অনিশ্চিত স্ক্যান',categories:'শনাক্তযোগ্য শ্রেণি',activity:'স্ক্যান কার্যকলাপ',distribution:'রোগ শনাক্তকরণের বণ্টন',recent:'সাম্প্রতিক বিশ্লেষণ'},
    hi: {heading:'फसल स्वास्थ्य डैशबोर्ड',total:'कुल पूर्ण स्कैन',healthy:'स्वस्थ स्कैन',diseased:'रोग वाले स्कैन',inconclusive:'अनिश्चित स्कैन',categories:'पहचानी जाने वाली श्रेणियाँ',activity:'स्कैन गतिविधि',distribution:'रोग पहचान वितरण',recent:'हाल के विश्लेषण'}
  };
  const lang = document.getElementById('languageSelect');
  const theme = document.getElementById('themeToggle');
  const search = document.getElementById('historySearch');
  const filter = document.getElementById('statusFilter');
  function translate(language) {
    document.documentElement.lang = language;
    document.querySelectorAll('[data-i18n]').forEach(node => {
      node.textContent = translations[language][node.dataset.i18n] || translations.en[node.dataset.i18n];
    });
    localStorage.setItem('agrovision_dashboard_language', language);
  }
  lang.value = localStorage.getItem('agrovision_dashboard_language') || 'en';
  translate(translations[lang.value] ? lang.value : 'en');
  lang.addEventListener('change', () => translate(lang.value));
  function setTheme(dark) {
    document.body.classList.toggle('dark-theme', dark);
    theme.textContent = dark ? '☀ Light mode' : '☾ Dark mode';
    localStorage.setItem('agrovision_dashboard_dark', dark ? '1' : '0');
  }
  setTheme(localStorage.getItem('agrovision_dashboard_dark') === '1');
  theme.addEventListener('click', () => setTheme(!document.body.classList.contains('dark-theme')));
  function filterHistory() {
    const term = search.value.trim().toLowerCase();
    document.querySelectorAll('.history-item').forEach(row => {
      row.hidden = !!((filter.value && row.dataset.status !== filter.value) || (term && !row.dataset.search.includes(term)));
    });
  }
  search?.addEventListener('input', filterHistory);
  filter?.addEventListener('change', filterHistory);
})();