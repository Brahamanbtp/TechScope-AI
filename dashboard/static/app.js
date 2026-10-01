(() => {
  const status = document.querySelector('#offline-status');
  const updateStatus = () => { if (status) status.textContent = navigator.onLine ? '' : 'Offline mode: showing cached content'; };
  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  updateStatus();
  const articles = [...document.querySelectorAll('article.card')];
  let index = 0;
  const focusArticle = () => articles[index]?.focus();
  document.addEventListener('keydown', event => {
    if (event.key === 'j') { index = Math.min(index + 1, articles.length - 1); focusArticle(); }
    if (event.key === 'k') { index = Math.max(index - 1, 0); focusArticle(); }
  });
})();
