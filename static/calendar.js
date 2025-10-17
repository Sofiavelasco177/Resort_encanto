// Room annual calendar modal renderer
(function(){
  function byId(id){ return document.getElementById(id); }

  function qs(el, sel){ return el.querySelector(sel); }
  function qsa(el, sel){ return Array.from(el.querySelectorAll(sel)); }

  function monthName(m){
    const names = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
    return names[m];
  }

  function daysInMonth(y,m){ // m: 0-11
    return new Date(y, m+1, 0).getDate();
  }

  function weekdayMon0(date){ // Monday=0..Sunday=6
    const d = date.getDay(); // Sun=0..Sat=6
    return (d+6)%7;
  }

  function renderCalendar(container, data){
    const year = data.year;
    const map = new Map(); // 'YYYY-MM-DD' -> status
    (data.days||[]).forEach(d => map.set(d.date, d.status));

    // Clear
    container.innerHTML = '';

    // Grid container
    const wrap = document.createElement('div');
    wrap.className = 'calendar-year';

    for (let m=0; m<12; m++){
      const monthBox = document.createElement('div');
      monthBox.className = 'calendar-month';
      const title = document.createElement('div');
      title.className = 'calendar-month-title';
      title.textContent = monthName(m) + ' ' + year;
      monthBox.appendChild(title);

      // headers Mon..Sun
      const grid = document.createElement('div');
      grid.className = 'calendar-grid';
      const dows = ['L','M','X','J','V','S','D'];
      dows.forEach(txt=>{ const el=document.createElement('div'); el.className='calendar-dow'; el.textContent=txt; grid.appendChild(el); });

      const first = new Date(year, m, 1);
      const offset = weekdayMon0(first);
      const count = daysInMonth(year, m);
      // empties
      for (let i=0;i<offset;i++){
        const e = document.createElement('div'); e.className='calendar-day empty'; grid.appendChild(e);
      }
      for (let d=1; d<=count; d++){
        const dateStr = `${year}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const status = map.get(dateStr) || 'disponible';
        const cell = document.createElement('div');
        cell.className = `calendar-day status-${status}`;
        cell.textContent = d;
        grid.appendChild(cell);
      }

      monthBox.appendChild(grid);
      wrap.appendChild(monthBox);
    }

    container.appendChild(wrap);
  }

  async function loadAndRender(modal){
    const url = modal.getAttribute('data-url');
    let year = parseInt(modal.getAttribute('data-year')) || (new Date()).getFullYear();
    modal.__year = year;
    const body = modal.querySelector('.calendar-body');
    const yearEl = modal.querySelector('.calendar-year'); // not the grid; header span
    const yearSpan = modal.querySelector('.calendar-controls .calendar-year');
    if (yearSpan) yearSpan.textContent = year;
    if (!body) return;
    body.innerHTML = '<div class="text-muted small">Cargando…</div>';
    const sep = url.includes('?') ? '&' : '?';
    const resp = await fetch(`${url}${sep}year=${encodeURIComponent(year)}`);
    const data = await resp.json();
    body.innerHTML='';
    renderCalendar(body, data);
  }

  function onShown(e){
    const modal = e.target.closest('.hab-calendar-modal');
    if (modal) loadAndRender(modal);
  }

  function onClick(e){
    const prev = e.target.closest('.cal-prev');
    const next = e.target.closest('.cal-next');
    if (!prev && !next) return;
    const modal = e.target.closest('.hab-calendar-modal');
    if (!modal) return;
    let y = modal.__year || parseInt(modal.getAttribute('data-year')) || (new Date()).getFullYear();
    y = prev ? (y-1) : (y+1);
    modal.setAttribute('data-year', String(y));
    const span = modal.querySelector('.calendar-controls .calendar-year');
    if (span) span.textContent = y;
    loadAndRender(modal);
  }

  document.addEventListener('shown.bs.modal', onShown);
  document.addEventListener('click', onClick);
})();
