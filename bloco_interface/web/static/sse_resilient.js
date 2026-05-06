/* MVP-LEAN-01 Task 4 — SSE resilient client for S5 Processing.
 * Per ux-spec §3 S5 linhas 414-436 + connection drop micro-PATCH α.
 *
 * Mecanismos:
 *   1. Heartbeat — server emite ping a cada 10s; client reseta lastEventTs
 *   2. Timeout — setInterval 5s; se Date.now() - lastEventTs > 60000 → synthetic phase-error
 *   3. EventSource onerror — 1 retry com backoff 5s; falha → mesma synthetic
 *   4. Audit — POST /audit/connection-drop quando drop detectado
 */
(function () {
  'use strict';

  var TIMEOUT_MS = 60000; // 60s sem evento = synthetic phase-error
  var TIMEOUT_CHECK_INTERVAL_MS = 5000; // checa a cada 5s
  var RETRY_BACKOFF_MS = 5000; // 1 retry com 5s backoff

  var pane = document.querySelector('.processing-pane');
  if (!pane) { return; }

  var streamUrl = pane.getAttribute('data-stream-url');
  var jobId = pane.getAttribute('data-job-id');
  if (!streamUrl) { return; }

  var lastEventTs = Date.now();
  var lastPhase = null;
  var retryAttempted = false;
  var eventSource = null;
  var timeoutInterval = null;
  var startedAtMs = Date.now();

  function setPhaseState(phase, state, extra) {
    var li = pane.querySelector('[data-phase="' + cssEscape(phase) + '"]');
    if (!li) { return; }
    li.setAttribute('data-state', state);
    var labelStatus = state === 'running' ? 'em curso'
      : state === 'done' ? 'concluído'
      : state === 'error' ? 'erro'
      : 'pendente';
    var srStatus = li.querySelector('.processing-phase__sr-status');
    if (srStatus) { srStatus.textContent = '(' + labelStatus + ')'; }
    if (state === 'done' && extra && extra.elapsed_s != null) {
      var elapsedEl = li.querySelector('.processing-phase__elapsed');
      if (elapsedEl) { elapsedEl.textContent = extra.elapsed_s + 's'; }
    }
    li.setAttribute('aria-label',
      'Fase ' + (li.querySelector('.processing-phase__index') ? li.querySelector('.processing-phase__index').textContent : '') +
      ': ' + phase + ' (' + labelStatus + ')');
    lastPhase = phase;
  }

  function cssEscape(s) {
    if (window.CSS && window.CSS.escape) { return window.CSS.escape(s); }
    return s.replace(/[^a-zA-Z0-9_-]/g, '\\$&');
  }

  function updateTotalElapsed() {
    var totalEl = pane.querySelector('[data-testid="total-elapsed"]');
    if (totalEl) { totalEl.textContent = Math.floor((Date.now() - startedAtMs) / 1000); }
  }

  function emitSyntheticPhaseError() {
    var data = {
      phase: lastPhase || 'unknown',
      diagnostic: 'Conexão com servidor perdida',
      cause: 'Sem resposta do servidor por 60s — pipeline pode ter parado ou ainda estar executando no backend',
      solution: 'Re-execute a análise. Se persistir, verifique conectividade ou reinicie a app',
      alternative: 'Verifique audit.jsonl para confirmar se o pipeline completou no backend mesmo sem resposta UI',
      synthetic: true,
    };
    showError(data);
    reportConnectionDrop();
    cleanup();
  }

  function reportConnectionDrop() {
    if (!jobId) { return; }
    var formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('last_phase', lastPhase || 'unknown');
    fetch('/audit/connection-drop', { method: 'POST', body: formData, credentials: 'same-origin' })
      .catch(function () { /* best-effort, não bloquear UX */ });
  }

  function showError(data) {
    setPhaseState(data.phase, 'error');
    var errEl = document.createElement('div');
    errEl.className = 'processing-error';
    errEl.setAttribute('role', 'alert');
    errEl.setAttribute('aria-live', 'assertive');
    errEl.setAttribute('data-testid', 'processing-error');
    errEl.innerHTML =
      '<p><strong>' + escapeHtml(data.diagnostic || 'Erro') + '</strong></p>' +
      (data.cause ? '<p>' + escapeHtml(data.cause) + '</p>' : '') +
      (data.solution ? '<p><em>Solução:</em> ' + escapeHtml(data.solution) + '</p>' : '') +
      (data.alternative ? '<p><em>Alternativa:</em> ' + escapeHtml(data.alternative) + '</p>' : '');
    pane.appendChild(errEl);
  }

  function escapeHtml(s) {
    if (s == null) { return ''; }
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function handleEvent(eventName, data) {
    lastEventTs = Date.now();
    if (eventName === 'ping') { return; } // heartbeat silent
    if (eventName === 'phase-start') {
      setPhaseState(data.phase, 'running');
    } else if (eventName === 'phase-done') {
      setPhaseState(data.phase, 'done', { elapsed_s: data.elapsed_s });
    } else if (eventName === 'phase-error') {
      showError(data);
      cleanup();
    } else if (eventName === 'complete') {
      // Pipeline completou — UX redirect/swap para S6 Resultado (Task 5 implementa)
      setTimeout(function () { window.location.href = '/verdict?job_id=' + encodeURIComponent(jobId); }, 500);
      cleanup();
    }
  }

  function attachEventListeners(es) {
    ['ping', 'phase-start', 'phase-done', 'phase-error', 'complete'].forEach(function (name) {
      es.addEventListener(name, function (evt) {
        try {
          var data = JSON.parse(evt.data);
          handleEvent(name, data);
        } catch (e) { /* ignore parse error */ }
      });
    });
  }

  function startTimeoutCheck() {
    timeoutInterval = setInterval(function () {
      updateTotalElapsed();
      if (Date.now() - lastEventTs > TIMEOUT_MS) {
        emitSyntheticPhaseError();
      }
    }, TIMEOUT_CHECK_INTERVAL_MS);
  }

  function cleanup() {
    if (eventSource) { eventSource.close(); eventSource = null; }
    if (timeoutInterval) { clearInterval(timeoutInterval); timeoutInterval = null; }
  }

  function connect() {
    eventSource = new EventSource(streamUrl);
    attachEventListeners(eventSource);
    eventSource.onerror = function () {
      if (retryAttempted) {
        emitSyntheticPhaseError();
        return;
      }
      retryAttempted = true;
      cleanup();
      setTimeout(function () {
        eventSource = new EventSource(streamUrl);
        attachEventListeners(eventSource);
        eventSource.onerror = function () { emitSyntheticPhaseError(); };
        startTimeoutCheck();
      }, RETRY_BACKOFF_MS);
    };
  }

  // Cancel button (link visual; backend stub — tech debt para Task 6)
  var cancelBtn = pane.querySelector('.processing-cancel');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function () {
      cleanup();
      window.location.href = '/';
    });
  }

  connect();
  startTimeoutCheck();
})();
