// The left and right arrow keys flip between strips, following the page's
// <link rel="prev"> and <link rel="next">.
document.addEventListener("keydown", (event) => {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (event.target.closest("input, textarea, select, [contenteditable]")) return;
  const rel = { ArrowLeft: "prev", ArrowRight: "next" }[event.key];
  const link = rel && document.querySelector(`link[rel="${rel}"]`);
  if (link) window.location.href = link.href;
});
