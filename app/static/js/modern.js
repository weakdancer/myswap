(function () {
  'use strict';
  // A direct username URL keeps the original sessionless navigation model.
  var workspace = document.querySelector('[data-workspace-form]');
  if (workspace) workspace.addEventListener('submit', function (event) {
    event.preventDefault();
    var name = workspace.querySelector('input[name="username"]').value.trim();
    if (/^[a-zA-Z0-9]+$/.test(name)) window.location.assign('/' + encodeURIComponent(name));
  });
  document.querySelectorAll('[data-open-composer]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      var composer = document.getElementById('new-swap');
      if (!composer) return;
      event.preventDefault(); composer.open = true;
      composer.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      var input = composer.querySelector('textarea');
      if (input) input.focus({ preventScroll: true });
    });
  });
  var search = document.querySelector('[data-note-search]');
  if (search) {
    var cards = Array.from(document.querySelectorAll('[data-note-card]'));
    var empty = document.querySelector('[data-search-empty]');
    var status = document.querySelector('[data-search-status]');
    var filter = function () {
      var query = search.value.trim().toLocaleLowerCase(); var visible = 0;
      cards.forEach(function (card) {
        var match = (card.dataset.noteSearchText || '').toLocaleLowerCase().includes(query);
        card.hidden = !match; if (match) visible++;
      });
      if (empty) empty.hidden = visible !== 0;
      if (status) status.textContent = query ? '找到 ' + visible + ' 段文字。' : '';
    };
    search.addEventListener('input', filter);
    var clear = document.querySelector('[data-clear-search]');
    if (clear) clear.addEventListener('click', function () { search.value = ''; filter(); search.focus(); });
  }
  document.querySelectorAll('[data-count-target]').forEach(function (input) {
    var target = document.getElementById(input.dataset.countTarget);
    var count = function () { if (target) target.textContent = Array.from(input.value).length + ' 字符'; };
    input.addEventListener('input', count); count();
  });
  var source = document.querySelector('[data-preview-source]');
  var output = document.querySelector('[data-preview-output]');
  var placeholder = document.querySelector('[data-preview-placeholder]');
  if (source && output) source.addEventListener('input', function () {
    // Construct nodes rather than interpreting user text as HTML.
    output.replaceChildren();
    var text = source.value; var pattern = /https?:\/\/[^\s<>]+/g; var start = 0; var match;
    while ((match = pattern.exec(text))) {
      output.appendChild(document.createTextNode(text.slice(start, match.index)));
      var anchor = document.createElement('a'); anchor.href = match[0]; anchor.textContent = match[0];
      anchor.target = '_blank'; anchor.rel = 'noopener noreferrer'; output.appendChild(anchor);
      start = match.index + match[0].length;
    }
    output.appendChild(document.createTextNode(text.slice(start)));
    if (placeholder) placeholder.hidden = text.length > 0;
  });
  var forms = Array.from(document.querySelectorAll('[data-dirty-form]'));
  var snapshots = new Map(); var submitting = false;
  function snapshot(form) {
    return JSON.stringify(Array.from(form.elements).filter(function (field) { return field.name && field.type !== 'password' && field.type !== 'hidden'; }).map(function (field) { return [field.name, field.value]; }));
  }
  forms.forEach(function (form) {
    snapshots.set(form, snapshot(form));
    form.addEventListener('input', function () {
      var state = document.querySelector('[data-editor-state]');
      if (state) { var changed = snapshot(form) !== snapshots.get(form); state.textContent = changed ? '有未保存的修改' : '未修改'; state.classList.toggle('dirty', changed); }
    });
    form.addEventListener('submit', function (event) {
      // A cancelled or invalid submission must still protect unsaved edits.
      if (!event.defaultPrevented) submitting = true;
    });
  });
  var leaveDialog = document.querySelector('[data-unsaved-dialog]'); var pendingDestination = null;
  function hasChanges() { return forms.some(function (form) { return snapshot(form) !== snapshots.get(form); }); }
  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || link.target === '_blank' || link.hasAttribute('download') || !leaveDialog || !hasChanges()) return;
    var destination = new URL(link.href, window.location.href);
    if (!/^https?:$/.test(destination.protocol) || (destination.pathname === window.location.pathname && destination.search === window.location.search && destination.hash)) return;
    event.preventDefault(); pendingDestination = destination.href;
    if (!leaveDialog.open) leaveDialog.showModal();
  });
  if (leaveDialog) {
    leaveDialog.querySelector('[data-leave-keep]').addEventListener('click', function () { pendingDestination = null; leaveDialog.close(); });
    leaveDialog.querySelector('[data-leave-discard]').addEventListener('click', function () {
      var destination = pendingDestination; submitting = true; leaveDialog.close();
      if (destination) window.location.assign(destination);
    });
    leaveDialog.addEventListener('cancel', function () { pendingDestination = null; });
  }
  window.addEventListener('beforeunload', function (event) {
    if (!submitting && forms.some(function (form) { return snapshot(form) !== snapshots.get(form); })) {
      event.preventDefault(); event.returnValue = '';
    }
  });
  document.querySelectorAll('[data-password-match]').forEach(function (form) {
    var primary = form.querySelector('[data-password-primary]');
    var confirm = form.querySelector('[data-password-confirm]');
    if (!primary || !confirm) return;
    var validate = function () { confirm.setCustomValidity(primary.value !== confirm.value ? '两次输入的密码不一致。' : ''); };
    primary.addEventListener('input', validate); confirm.addEventListener('input', validate);
  });
  var copy = document.querySelector('[data-copy-link]'); var toast = document.querySelector('[data-toast]'); var toastTimer;
  if (copy) copy.addEventListener('click', async function () {
    var url = new URL(window.location.href); url.search = ''; url.hash = '';
    var message = '链接已复制，可以分享这段文字了。';
    try { await navigator.clipboard.writeText(url.href); }
    catch (error) { message = '复制未成功，请从浏览器地址栏复制链接。'; }
    if (toast) { toast.textContent = message; toast.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(function () { toast.hidden = true; }, 4500); }
  });
  // When browser history restores the page, edits should still be protected.
  window.addEventListener('pageshow', function () { submitting = false; });
}());
