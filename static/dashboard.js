// ===== HEUTIGE DATUM =====
function updateTodayDate() {
	const todayEl = document.getElementById('todayDate');
	if (!todayEl) return;

	const months = [
		'Januar','Februar','März','April','Mai','Juni',
		'Juli','August','September','Oktober','November','Dezember'
	];

	const today = new Date();
	const day = today.getDate();
	const month = months[today.getMonth()];
	const year = today.getFullYear();

	todayEl.textContent = `${day} ${month}, ${year}`;
}

// ===== BENUTZERDATEN LADEN =====
async function loadUserData() {
	try {
		const res = await fetch('/api/check-auth', { credentials: 'include' });
		const data = await res.json();

		if (data.authenticated) {
			const user = data.user;

			document.querySelector('.main-header h1').textContent = `Willkommen, ${user.name}! 👋`;
			document.querySelector('.prof-name').textContent = user.name;
			document.querySelector('.profile-name').textContent = user.name;

			let avatarUrl = user.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(user.name)}`;
			document.querySelectorAll('.profile img, .avatar img').forEach(img => img.src = avatarUrl);

		} else {
			alert('Sie sind nicht angemeldet!');
			window.location.href = '/';
		}
	} catch (err) {
		console.error('Fehler beim Laden der Daten:', err);
		alert('Verbindungsfehler zum Server');
		window.location.href = '/';
	}
}

// ===== ABMELDUNG =====
async function logout() {
	if (!confirm('Möchten Sie sich wirklich abmelden?')) return;
	try {
		const res = await fetch('/api/logout', { method:'POST', credentials:'include' });
		const data = await res.json();
		alert(data.message);
		window.location.href = '/';
	} catch(err) {
		console.error(err);
		alert('Fehler beim Abmelden');
	}
}

// ===== INITIALISIERUNG =====
document.addEventListener('DOMContentLoaded', () => {
	console.log('🚀 Dashboard wird geladen...');
	updateTodayDate();
	loadUserData();

	// Chart.js
	const ctx = document.getElementById('activityChart');
	if (ctx) {
		new Chart(ctx.getContext('2d'), {
			type: 'line',
			data: {
				labels: ['15 Mon','16 Tue','17 Wed','18 Thu','19 Fri','20 Sat','21 Sun'],
				datasets: [
					{
						label: 'Theorie',
						data: [20,35,28,45,32,30,38],
						tension:0.36,
						borderWidth:2,
						borderColor:'rgba(124,58,237,0.95)',
						backgroundColor:'rgba(124,58,237,0.06)',
						pointRadius:4,
						pointHoverRadius:6
					},
					{
						label:'Praxis',
						data:[18,22,30,28,26,15,22],
						tension:0.36,
						borderWidth:2,
						borderColor:'rgba(37,99,235,0.95)',
						backgroundColor:'rgba(37,99,235,0.06)',
						pointRadius:4,
						pointHoverRadius:6
					}
				]
			},
			options:{
				plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},
				scales:{
					x:{grid:{display:false},ticks:{color:'#94a3b8'}},
					y:{beginAtZero:true,grid:{color:'rgba(15,23,42,0.04)'},ticks:{stepSize:10,color:'#94a3b8'}}
				},
				maintainAspectRatio:false
			}
		});
	}

	// Dunkles Thema
	const themeToggle = document.getElementById('themeToggle');
	if (themeToggle) themeToggle.addEventListener('change', e => {
		const dark = e.target.checked;
		const root = document.documentElement.style;
		if(dark){
			root.setProperty('--bg','#0b1220');
			root.setProperty('--surface','#0f1724');
			root.setProperty('--text','#e6eef8');
			root.setProperty('--muted','#9fb0c8');
			root.setProperty('--shadow','0 8px 30px rgba(2,6,23,0.6)');
		}else{
			root.removeProperty('--bg');
			root.removeProperty('--surface');
			root.removeProperty('--text');
			root.removeProperty('--muted');
			root.removeProperty('--shadow');
		}
	});

	// Drag für Kurse
	document.querySelectorAll('.course').forEach(c=>{
		c.setAttribute('draggable','true');
		c.addEventListener('dragstart',()=>c.style.opacity=0.6);
		c.addEventListener('dragend',()=>c.style.opacity=1);
	});

	// Navigation
	document.querySelectorAll('.nav-item').forEach(item=>{
		item.addEventListener('click',function(){
			document.querySelectorAll('.nav-item').forEach(i=>i.classList.remove('active'));
			this.classList.add('active');
			const t = this.textContent.trim();
			if(t==='Dashboard') window.location.href='dashboard.html';
			else if(t==='Kurse') window.location.href='kurse.html';
			else if(t==='Einstellungen') window.location.href='einstellungen.html';
						else if(t==='AI') window.location.href='ai.html';

			else alert('Diese Funktion ist noch in Entwicklung!');
		});
	});

	// Logout Button
	const sidebar = document.querySelector('.sidebar-footer');
	if(sidebar && !document.getElementById('logoutBtn')){
		const btn = document.createElement('button');
		btn.id='logoutBtn';
		btn.textContent='🚪 Abmelden';
		btn.style.cssText='width:100%;padding:12px;background:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.3);border-radius:10px;font-weight:700;cursor:pointer;margin-top:12px;transition:all 0.2s;';
		btn.addEventListener('mouseenter',()=>{btn.style.background='#ef4444';btn.style.color='#fff';});
		btn.addEventListener('mouseleave',()=>{btn.style.background='rgba(239,68,68,0.1)';btn.style.color='#ef4444';});
		btn.addEventListener('click',logout);
		sidebar.appendChild(btn);
	}

	console.log('✅ Dashboard bereit!');
});
