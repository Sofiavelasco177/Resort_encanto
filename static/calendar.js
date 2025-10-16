// Simple annual calendar renderer for room schedules
// Expects payload from /hospedaje/calendar/<id>?year=YYYY
(function(){
  const MONTH_NAMES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  const WEEKDAY = ['L','M','X','J','V','S','D'];

  function toDate(str){
    const [y,m,d] = str.split('-').map(Number);
    return new Date(y, m-1, d);
  }

  function groupByMonth(days){
    const map = new Map();
    days.forEach(it => {
      const dt = toDate(it.date);
      const key = dt.getMonth();
      if(!map.has(key)) map.set(key, []);
      map.get(key).push({ dt, status: it.status });
    });
    // sort days inside each month
    for (const arr of map.values()) arr.sort((a,b)=>a.dt-b.dt);
    return map;
  }

  function buildMonthGrid(monthIdx, year, items){
    const wrap = document.createElement('div');
    wrap.className = 'calendar-month';
    const title = document.createElement('div');
    title.className = 'calendar-month-title';
    title.textContent = MONTH_NAMES[monthIdx];
    wrap.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'calendar-grid';
    // header
    WEEKDAY.forEach(w => {
      const h = document.createElement('div');
      h.className = 'calendar-dow';
      h.textContent = w;
      grid.appendChild(h);
    });
    // empty cells before first day
    const first = new Date(year, monthIdx, 1);
    let start = (first.getDay()+6)%7; // Monday=0
    for(let i=0;i<start;i++){
      const emp = document.createElement('div');
      emp.className = 'calendar-day empty';
      grid.appendChild(emp);
    }
    // days
    const lastDay = new Date(year, monthIdx+1, 0).getDate();
    const statusMap = new Map(items.map(it => [it.dt.getDate(), it.status]));
    for(let d=1; d<=lastDay; d++){
      const cell = document.createElement('div');
      const st = statusMap.get(d) || 'disponible';
      cell.className = `calendar-day status-${st}`;
      cell.title = `${d} ${MONTH_NAMES[monthIdx]} ${year} — ${st}`;
      cell.textContent = d;
      grid.appendChild(cell);
    }
    wrap.appendChild(grid);
    return wrap;
  }

  async function fetchCalendar(url){
    const res = await fetch(url, { credentials: 'same-origin' });
    if(!res.ok) throw new Error('No se pudo cargar calendario');
    return res.json();
  }

  function render(container, payload){
    const { year, days } = payload;
    container.innerHTML = '';
    const controls = container.parentElement.querySelector('.calendar-controls');
    if (controls) controls.querySelector('.calendar-year').textContent = year;
    const byMonth = groupByMonth(days);
    const yearWrap = document.createElement('div');
    yearWrap.className = 'calendar-year';
    for(let m=0;m<12;m++){
      const items = byMonth.get(m) || [];
      yearWrap.appendChild(buildMonthGrid(m, year, items));
    }
    container.appendChild(yearWrap);
  }

  async function loadInto(modalEl){
    if(!modalEl) return;
    const body = modalEl.querySelector('.calendar-body');
    const urlBase = modalEl.getAttribute('data-url');
      let currentYear = parseInt(modalEl.getAttribute('data-year'), 10);
      if (isNaN(currentYear)) currentYear = new Date().getFullYear();
    async function load(year){
      modalEl.setAttribute('data-year', String(year));
      body.innerHTML = '<div class="text-center text-muted py-3">Cargando calendario…</div>';
      try {
        const payload = await fetchCalendar(`${urlBase}?year=${year}`);
        render(body, payload);
          currentYear = year;
        } catch(e){
        body.innerHTML = `<div class="text-danger">${e.message}</div>`;
      }
    }
    // controls
    const prev = modalEl.querySelector('.cal-prev');
    const next = modalEl.querySelector('.cal-next');
    if(prev) prev.onclick = ()=> load(currentYear-1);
    if(next) next.onclick = ()=> load(currentYear+1);
    await load(currentYear);
  }

  // Auto-bind for Bootstrap modals
  document.addEventListener('shown.bs.modal', function (ev) {
    const modal = ev.target;
    if(modal && modal.classList.contains('hab-calendar-modal')){
      // load only first time or when data-year changes
      loadInto(modal);
    }
  });

  // Expose minimal API
  window.RoomCalendar = { loadInto };
})();
