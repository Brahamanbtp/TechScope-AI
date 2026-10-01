(() => {
  const articles = [...document.querySelectorAll('article.card')];
  let index = 0;
  const focusArticle = () => articles[index]?.focus();
  document.addEventListener('keydown', event => {
    if (event.key === 'j') { index = Math.min(index + 1, articles.length - 1); focusArticle(); }
    if (event.key === 'k') { index = Math.max(index - 1, 0); focusArticle(); }
  });
})();
