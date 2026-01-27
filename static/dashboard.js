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
		console.log('🔍 Check user data');
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

			console.log('✅ Пользователь загружен:', currentUser.name, 'Points:', currentUser.points);

			// Load user's enrolled courses
			await loadMyCourses();

			// Load friends list
			await loadFriends();

			// Load friend requests
			await loadFriendRequests();

			// Load teacher assignments (NEW!)
			await loadTeacherAssignments();

		} else {
			alert('Sie sind nicht angemeldet!');
			window.location.href = '/';
		}
	} catch (err) {
		console.error('❌ Fehler beim Laden der Daten:', err);
		alert('Verbindungsfehler zum Server');
		window.location.href = '/';
	}
}

// ===== MEINE KURSE LADEN =====
async function loadMyCourses() {
	try {
		console.log('📚 Lade kurse: ');
		const res = await fetch('/api/my-courses', { credentials: 'include' });

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}`);
		}

		const courses = await res.json();
		console.log('✅ Kursen geladen:', courses.length);

		const container = document.getElementById('myCourses');

		if (!courses || courses.length === 0) {
			container.innerHTML = `
				<div style="text-align: center; padding: 40px; color: var(--muted);">
					<div style="font-size: 48px; margin-bottom: 12px;">📚</div>
					<p>Du hast dich noch für keine Kurse angemeldet.</p>
					<a href="kurse.html" style="display: inline-block; margin-top: 16px; padding: 10px 20px; background: var(--accent); color: white; border-radius: 8px; text-decoration: none; font-weight: 700;">Kurse durchsuchen</a>
				</div>
			`;
			return;
		}

		const coursesToShow = courses.slice(0, 3);

		container.innerHTML = coursesToShow.map(course => {
			const badgeClass = course.category === 'Development' ? 'blue' : 'yellow';
			const progress = Math.floor(Math.random() * 100);

			return `
				<article class="course">
					<div class="course-badge ${badgeClass}">${course.category || 'Coding'}</div>
					<h4 class="course-title">${course.title}</h4>
					<p class="course-sub">${course.description || 'Ein interaktiver Kurs zum Programmieren lernen'}</p>
					<div class="course-meta">
						<div class="progress-line">
							<div class="progress" style="width:${progress}%"></div>
						</div>
						<div class="course-stats">${course.total_lessons || 0} lessons • ${course.duration || '8h'} • ${course.rating || 4.7}★</div>
					</div>
				</article>
			`;
		}).join('');

	} catch (err) {
		console.error('❌ Fehler beim Laden der Kurse:', err);
		const container = document.getElementById('myCourses');
		container.innerHTML = `
			<div style="text-align: center; padding: 40px; color: var(--muted);">
				<div style="font-size: 48px; margin-bottom: 12px;">⚠️</div>
				<p>Fehler beim Laden der Kurse</p>
			</div>
		`;
	}
}

// ===== LEHRER-AUFGABEN LADEN (NEU!) =====
async function loadTeacherAssignments() {
	try {
		console.log('📝 Lade Aufgaben vom Lehrer...');
		const res = await fetch('/api/student/teacher-assignments', { credentials: 'include' });

		if (!res.ok) {
			console.warn('⚠️ Keine Aufgaben oder Fehler:', res.status);
			return;
		}

		const data = await res.json();
		const assignments = data.assignments || [];

		console.log('✅ Lehrer-Aufgaben geladen:', assignments.length);

		// Update task stats
		const totalAssignments = assignments.length;
		const completedAssignments = assignments.filter(a => a.completed).length;
		const pendingAssignments = totalAssignments - completedAssignments;

		// Update "Aufgaben" stat in dashboard
		const coursesEl = document.querySelector('.stat-value.courses');
		if (coursesEl) {
			coursesEl.textContent = pendingAssignments; // Show pending assignments
		}

		// Show notification if there are pending assignments
		if (pendingAssignments > 0) {
			showAssignmentsNotification(pendingAssignments, assignments.slice(0, 3));
		}

	} catch (err) {
		console.error('❌ Fehler beim Laden der Aufgaben:', err);
	}
}

// ===== AUFGABEN-BENACHRICHTIGUNG ANZEIGEN =====
function showAssignmentsNotification(count, recentAssignments) {
	const sidebar = document.querySelector('.sidebar-footer');
	if (!sidebar) return;

	// Check if notification already exists
	if (document.getElementById('assignmentsNotif')) return;

	const notif = document.createElement('div');
	notif.id = 'assignmentsNotif';
	notif.style.cssText = 'background: rgba(124,58,237,0.1); padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 1px solid rgba(124,58,237,0.3); cursor: pointer; transition: all 0.2s;';

	notif.innerHTML = `
		<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
			<div>
				<div style="font-weight: 700; font-size: 13px;">📝 Neue Aufgaben</div>
				<div style="font-size: 12px; opacity: 0.9;">${count} ${count === 1 ? 'Aufgabe' : 'Aufgaben'} vom Lehrer</div>
			</div>
		</div>
		<div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">
			${recentAssignments.map(a => `• ${a.title}`).join('<br>')}
		</div>
	`;

	notif.addEventListener('click', () => {
		window.location.href = '/bewertungen.html';
	});

	notif.addEventListener('mouseenter', () => {
		notif.style.background = 'rgba(124,58,237,0.15)';
		notif.style.transform = 'translateX(4px)';
	});

	notif.addEventListener('mouseleave', () => {
		notif.style.background = 'rgba(124,58,237,0.1)';
		notif.style.transform = 'translateX(0)';
	});

	sidebar.insertBefore(notif, sidebar.firstChild);
}

// ===== FREUNDE LADEN =====
async function loadFriends() {
	try {
		console.log('👥 Загрузка друзей...');
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

		console.log('✅ Friends', topFriends.length);

	} catch (err) {
		console.error('❌ Fehler beim Laden der Freunde:', err);
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
	notif.style.cssText = 'background: rgba(37,99,235,0.1); padding: 10px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(37,99,235,0.3); cursor: pointer;';
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

		// Update completion stat
		const completionEl = document.querySelector('.stat-value.completion');
		if (completionEl) {
			completionEl.innerHTML = `${completionRate}<span class="muted">%</span>`;
		}

		console.log('✅ Stats geladen: Tasks:', totalTasks, 'Completion:', completionRate + '%');

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
     		else if(t==='Lehrer-Aufgaben' || t==='Teacher Aufgaben' || t==='Bewertungen') window.location.href='bewertungen.html';
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