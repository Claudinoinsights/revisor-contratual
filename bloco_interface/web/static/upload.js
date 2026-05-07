/* MVP-LEAN-01 Task 3 — Client-side upload validation + state.
 * Vanilla JS sem dependências externas.
 * - .pdf extension check + size <= 10MB antes do POST
 * - Estado loaded: classe .upload-zone--loaded + filename + filesize
 * - Toggle CTA "Iniciar análise" enabled/disabled conforme D1 (contrato) ter PDF válido
 * - Drag-drop: dragover + drop events
 */
(function () {
  'use strict';

  var MAX_SIZE_BYTES = 10 * 1024 * 1024;

  function formatSize(bytes) {
    if (bytes < 1024) { return bytes + ' B'; }
    if (bytes < 1024 * 1024) { return (bytes / 1024).toFixed(1) + ' KB'; }
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  function validateFile(file) {
    if (!file) { return { ok: false, error: 'Nenhum arquivo' }; }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return { ok: false, error: 'Apenas PDF é aceito' };
    }
    if (file.size > MAX_SIZE_BYTES) {
      return { ok: false, error: 'Arquivo excede 10MB' };
    }
    return { ok: true };
  }

  function setLoaded(zone, file) {
    zone.classList.add('upload-zone--loaded');
    var loadedDiv = zone.querySelector('.upload-zone__loaded');
    if (!loadedDiv) { return; }
    loadedDiv.hidden = false;
    var nameEl = loadedDiv.querySelector('.upload-zone__filename');
    var sizeEl = loadedDiv.querySelector('.upload-zone__filesize');
    if (nameEl) { nameEl.textContent = file.name; }
    if (sizeEl) { sizeEl.textContent = formatSize(file.size); }
  }

  function clearLoaded(zone) {
    zone.classList.remove('upload-zone--loaded');
    var loadedDiv = zone.querySelector('.upload-zone__loaded');
    if (loadedDiv) { loadedDiv.hidden = true; }
  }

  function toggleCta(contratoInput) {
    var cta = document.getElementById('upload-cta');
    if (!cta) { return; }
    var hasContrato = contratoInput && contratoInput.files && contratoInput.files.length > 0;
    if (hasContrato) {
      cta.removeAttribute('disabled');
      cta.setAttribute('aria-disabled', 'false');
    } else {
      cta.setAttribute('disabled', 'disabled');
      cta.setAttribute('aria-disabled', 'true');
    }
  }

  function handleFileInput(zone, input, contratoInput) {
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      var v = validateFile(file);
      if (!v.ok) {
        alert(v.error);
        input.value = '';
        clearLoaded(zone);
      } else {
        setLoaded(zone, file);
      }
      toggleCta(contratoInput);
    });
  }

  function handleDragDrop(zone, input, contratoInput) {
    zone.addEventListener('dragover', function (e) {
      e.preventDefault();
      zone.classList.add('upload-zone--dragover');
    });
    zone.addEventListener('dragleave', function () {
      zone.classList.remove('upload-zone--dragover');
    });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      zone.classList.remove('upload-zone--dragover');
      var file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!file) { return; }
      var v = validateFile(file);
      if (!v.ok) {
        alert(v.error);
        return;
      }
      // Atribuir arquivo ao input via DataTransfer
      var dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      setLoaded(zone, file);
      toggleCta(contratoInput);
    });
  }

  function init() {
    var zones = document.querySelectorAll('.upload-zone');
    if (zones.length === 0) { return; }
    var contratoZone = document.querySelector('[data-tipo="contrato"]');
    var contratoInput = contratoZone ? contratoZone.querySelector('.upload-zone__input') : null;
    zones.forEach(function (zone) {
      var input = zone.querySelector('.upload-zone__input');
      if (!input) { return; }
      handleFileInput(zone, input, contratoInput);
      handleDragDrop(zone, input, contratoInput);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
