// ===== GLOBALE VARIABLEN =====
let currentUser = null;

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
			currentUser = data.user;

			document.querySelector('.main-header h1').textContent = `Willkommen, ${currentUser.name}! 👋`;
			document.querySelector('.prof-name').textContent = currentUser.name;
			document.querySelector('.profile-name').textContent = currentUser.name;

			// Update points display
			document.querySelector('.prof-score').textContent = `${currentUser.points || 0} Punkte`;

			// Update stats
			const pointsStatEl = document.querySelector('.stat-value.points');
			if (pointsStatEl) {
				pointsStatEl.textContent = currentUser.points || 0;
			}

			let avatarUrl = currentUser.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(currentUser.name)}`;
			document.querySelectorAll('.profile img, .avatar img').forEach(img => img.src = avatarUrl);

			// Load friends list
			await loadFriends();

			// Load friend requests
			await loadFriendRequests();

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

// ===== FREUNDE LADEN =====
async function loadFriends() {
	try {
		const res = await fetch('/api/friends/list', { credentials: 'include' });
		const friends = await res.json();

		const friendsList = document.querySelector('.friends-list');
		if (!friendsList) return;

		if (friends.length === 0) {
			friendsList.innerHTML = '<p style="color: var(--muted); text-align: center; padding: 20px;">Noch keine Freunde. Füge Freunde hinzu!</p>';
			return;
		}

		// Sort by points and take top 5
		friends.sort((a, b) => (b.points || 0) - (a.points || 0));
		const topFriends = friends.slice(0, 5);

		friendsList.innerHTML = topFriends.map(friend => {
			const avatarUrl = friend.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(friend.name)}`;
			return `
				<div class="friend">
					<div class="avatar xs">
						<img src="${avatarUrl}" alt="${friend.name}">
					</div>
					<div class="friend-name">${friend.name}</div>
					<div class="friend-score">${friend.points || 0}</div>
				</div>
			`;
		}).join('');

	} catch (err) {
		console.error('Fehler beim Laden der Freunde:', err);
	}
}

// ===== FREUNDSCHAFTSANFRAGEN LADEN =====
async function loadFriendRequests() {
	try {
		const res = await fetch('/api/friends/requests', { credentials: 'include' });
		const requests = await res.json();

		if (requests.length > 0) {
			showFriendRequestsNotification(requests);
		}
	} catch (err) {
		console.error('Fehler beim Laden der Anfragen:', err);
	}
}

// ===== FREUNDSCHAFTSANFRAGEN BENACHRICHTIGUNG =====
function showFriendRequestsNotification(requests) {
	const sidebar = document.querySelector('.sidebar-footer');
	if (!sidebar) return;

	// Check if notification already exists
	if (document.getElementById('friendRequestsNotif')) return;

	const notif = document.createElement('div');
	notif.id = 'friendRequestsNotif';
	notif.style.cssText = 'background: rgba(37,99,235,0.1); padding: 10px; border-radius: 10px; margin-top: 10px; border: 1px solid rgba(37,99,235,0.3); cursor: pointer;';
	notif.innerHTML = `
		<div style="display: flex; align-items: center; justify-content: space-between;">
			<div>
				<div style="font-weight: 700; font-size: 13px;">🔔 Neue Anfragen</div>
				<div style="font-size: 12px; opacity: 0.9;">${requests.length} Freundschaftsanfrage(n)</div>
			</div>
		</div>
	`;

	notif.addEventListener('click', () => {
		window.location.href = '/freunde.html';
	});

	sidebar.insertBefore(notif, sidebar.firstChild);
}

// ===== FREUNDE SUCHEN =====
async function searchFriends(query) {
	if (!query || query.length < 2) return [];

	try {
		const res = await fetch(`/api/friends/search?q=${encodeURIComponent(query)}`, {
			credentials: 'include'
		});
		const users = await res.json();
		return users;
	} catch (err) {
		console.error('Fehler bei der Suche:', err);
		return [];
	}
}

// ===== FREUNDSCHAFTSANFRAGE SENDEN =====
async function sendFriendRequest(friendId) {
	try {
		const res = await fetch('/api/friends/request', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify({ friend_id: friendId })
		});

		const data = await res.json();

		if (data.success) {
			alert(data.message);
			return true;
		} else {
			alert(data.message);
			return false;
		}
	} catch (err) {
		console.error('Fehler beim Senden der Anfrage:', err);
		alert('Fehler beim Senden der Freundschaftsanfrage');
		return false;
	}
}

// ===== FREUNDSCHAFTSANFRAGE AKZEPTIEREN =====
async function acceptFriendRequest(friendId) {
	try {
		const res = await fetch('/api/friends/accept', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify({ friend_id: friendId })
		});

		const data = await res.json();

		if (data.success) {
			alert(data.message);
			await loadFriends();
			await loadFriendRequests();
			return true;
		} else {
			alert(data.message);
			return false;
		}
	} catch (err) {
		console.error('Fehler beim Akzeptieren:', err);
		alert('Fehler beim Akzeptieren der Anfrage');
		return false;
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

// ===== STATS LADEN =====
async function loadUserStats() {
	try {
		const res = await fetch('/api/ai/my-tasks', { credentials: 'include' });
		const tasks = await res.json();

		const completedTasks = tasks.filter(t => t.completed).length;
		const totalTasks = tasks.length;
		const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

		// Update stats display
		const statsElements = {
			'.stat-value.courses': totalTasks,
			'.stat-value.completion': `${completionRate}<span class="muted">%</span>`
		};

		for (const [selector, value] of Object.entries(statsElements)) {
			const el = document.querySelector(selector);
			if (el) {
				el.innerHTML = value;
			}
		}
	} catch (err) {
		console.error('Fehler beim Laden der Stats:', err);
	}
}

// ===== INITIALISIERUNG =====
document.addEventListener('DOMContentLoaded', async () => {
	console.log('🚀 Dashboard wird geladen...');
	updateTodayDate();
	await loadUserData();
	await loadUserStats();

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
			else if(t==='Freunde') window.location.href='freunde.html';
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
