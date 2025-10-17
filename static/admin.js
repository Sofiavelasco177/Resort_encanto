// Admin shared behaviors

document.addEventListener('DOMContentLoaded', () => {
  // Hospedaje Admin behaviors
  const host = document.getElementById('hospedaje-admin-page');
  if (!host) return; // Run only on hospedaje admin

  // View toggle (cards/table)
  const cards = document.getElementById('view-cards');
  const table = document.getElementById('view-table');
  const viewBtns = document.querySelectorAll('.view-btn');
  const viewKey = 'adminRoomsView';
  const setView = (v) => {
    if (!cards || !table) return;
    const isCards = v === 'cards';
    cards.classList.toggle('hidden', !isCards);
    table.classList.toggle('hidden', isCards);
    viewBtns.forEach(b => {
      b.classList.toggle('btn-light', b.dataset.view===v);
      b.classList.toggle('btn-outline-light', b.dataset.view!==v);
    });
    try { localStorage.setItem(viewKey, v); } catch(e){}
  };
  viewBtns.forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
  try { setView(localStorage.getItem(viewKey) || 'cards'); } catch(e){ setView('cards'); }

  // Add form collapse persistence
  const addCollapse = document.getElementById('addRoomCollapse');
  const collapseKey = 'adminAddRoomOpen';
  if (addCollapse && window.bootstrap) {
    const inst = bootstrap.Collapse.getOrCreateInstance(addCollapse, { toggle: false });
    try { (localStorage.getItem(collapseKey) === '1') ? inst.show() : inst.hide(); } catch(e){}
    addCollapse.addEventListener('shown.bs.collapse', () => { try{ localStorage.setItem(collapseKey,'1'); }catch(e){} });
    addCollapse.addEventListener('hidden.bs.collapse', () => { try{ localStorage.setItem(collapseKey,'0'); }catch(e){} });
  }

  // Filters
  const planSel = document.getElementById('filter-plan');
  const estadoSel = document.getElementById('filter-estado');
  const guestsInp = document.getElementById('filter-guests');
  const priceOrderSel = document.getElementById('filter-price-order');
  const btnApply = document.getElementById('btn-apply-filters');
  const btnReset = document.getElementById('btn-reset-filters');
  const filterKey = 'adminRoomsFilters';

  function readFilters() {
    return {
      plan: planSel?.value || '',
      estado: estadoSel?.value || '',
      guests: parseInt(guestsInp?.value || '0') || 0,
      price: priceOrderSel?.value || ''
    };
  }

  function saveFilters() {
    try { localStorage.setItem(filterKey, JSON.stringify(readFilters())); } catch(e){}
  }

  function loadFilters() {
    try {
      const obj = JSON.parse(localStorage.getItem(filterKey) || '{}');
      if (planSel && obj.plan !== undefined) planSel.value = obj.plan;
      if (estadoSel && obj.estado !== undefined) estadoSel.value = obj.estado;
      if (guestsInp && obj.guests !== undefined) guestsInp.value = obj.guests || '';
      if (priceOrderSel && obj.price !== undefined) priceOrderSel.value = obj.price;
    } catch(e){}
  }

  function applyFilters() {
    const { plan, estado, guests, price } = readFilters();
    // Cards
    const blocks = Array.from(document.querySelectorAll('#view-cards .admin-room-card'));
    blocks.forEach(el => {
      const p = (el.getAttribute('data-plan') || '').trim();
      const st = (el.getAttribute('data-estado') || '').trim();
      const cap = parseInt(el.getAttribute('data-cupo') || '0');
      let visible = true;
      if (plan && p !== plan) visible = false;
      if (estado && st !== estado) visible = false;
      if (guests > 0 && cap < guests) visible = false;
      el.style.display = visible ? '' : 'none';
    });
    // Table rows
    const rows = Array.from(document.querySelectorAll('#view-table tbody tr.room-row'));
    rows.forEach(tr => {
      const p = (tr.getAttribute('data-plan') || '').trim();
      const st = (tr.getAttribute('data-estado') || '').trim();
      const cap = parseInt(tr.getAttribute('data-cupo') || '0');
      let visible = true;
      if (plan && p !== plan) visible = false;
      if (estado && st !== estado) visible = false;
      if (guests > 0 && cap < guests) visible = false;
      tr.style.display = visible ? '' : 'none';
    });

    // Sorting by price
    if (price) {
      const dir = price === 'asc' ? 1 : -1;
      // Cards reorder
      const grid = document.getElementById('view-cards');
      if (grid) {
        const items = Array.from(grid.querySelectorAll('.admin-room-card'));
        items.sort((a,b) => (parseFloat(a.dataset.precio||'0') - parseFloat(b.dataset.precio||'0')) * dir);
        items.forEach(i => grid.appendChild(i));
      }
      // Table reorder
      const tb = document.querySelector('#view-table tbody');
      if (tb) {
        const items = Array.from(tb.querySelectorAll('tr.room-row'));
        items.sort((a,b) => (parseFloat(a.dataset.precio||'0') - parseFloat(b.dataset.precio||'0')) * dir);
        items.forEach(i => tb.appendChild(i));
      }
    }
    saveFilters();
  }

  function resetFilters() {
    if (planSel) planSel.value = '';
    if (estadoSel) estadoSel.value = '';
    if (guestsInp) guestsInp.value = '';
    if (priceOrderSel) priceOrderSel.value = '';
    applyFilters();
  }

  // Wire buttons
  if (btnApply) btnApply.addEventListener('click', applyFilters);
  if (btnReset) btnReset.addEventListener('click', resetFilters);
  // Init
  loadFilters();
  applyFilters();
});
