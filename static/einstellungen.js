// ============================================
// EINSTELLUNGEN - PROFESSIONELLER JS
// ============================================

let currentUser = null;
let originalAvatar = null;
let currentAvatar = null;
let avatarChanged = false;
let profileChanged = false;

// ============================================
// INITIALISIERUNG
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
	console.log('🚀 Einstellungen werden geladen...');
	try {
		await loadUserData();
		initializeEventListeners();
		initializeThemeToggle();
		initializeNavigation();
		console.log('✅ Einstellungen erfolgreich geladen!');
	} catch (error) {
		// Nur anzeigen, wenn wirklich ein unerwarteter Fehler auftritt
	}
});

// ============================================
// BENUTZERDATEN LADEN
// ============================================

async function loadUserData() {
	try {
		const response = await fetch('/api/check-auth', { credentials: 'include' });
		const data = await response.json();

		if (!data.authenticated) {
			alert('Sie sind nicht angemeldet!');
			return window.location.href = '/';
		}

		currentUser = data.user;
		await loadUserProfile();
		updateUI(currentUser);
	} catch (error) {
		console.error('❌ Fehler beim Laden der Benutzerdaten:', error);
		alert('Verbindungsfehler zum Server');
		window.location.href = '/';
	}
}

// ============================================
// BENUTZERPROFIL LADEN
// ============================================

async function loadUserProfile() {
	try {
		const response = await fetch('/api/profile', { credentials: 'include' });
		if (!response.ok) throw new Error('Profil konnte nicht geladen werden');
		const profile = await response.json();

		originalAvatar = profile.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(currentUser.name)}`;
		currentAvatar = originalAvatar;

		updateFormWithProfile(profile);
		updateAvatars(currentAvatar);
	} catch (error) {
		console.error('Fehler beim Laden des Profils:', error);
		originalAvatar = currentAvatar = `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(currentUser.name)}`;
		updateAvatars(currentAvatar);
	}
}

// ============================================
// UI AKTUALISIEREN
// ============================================

function updateUI(user) {
	const sidebarName = document.getElementById('sidebarName');
	if (sidebarName) sidebarName.textContent = user.name;

	const nameParts = user.name.split(' ');
	document.getElementById('firstName').value = nameParts[0] || '';
	document.getElementById('lastName').value = nameParts.slice(1).join(' ') || '';
	document.getElementById('email').value = user.email;
}

function updateFormWithProfile(profile) {
	if (profile.birthdate) document.getElementById('birthdate').value = profile.birthdate;
	if (profile.country) document.getElementById('country').value = profile.country;
	if (profile.bio) {
		document.getElementById('bio').value = profile.bio;
		updateBioCounter();
	}
	if (profile.favorite_language) document.getElementById('favoriteLanguage').value = profile.favorite_language;
	if (profile.experience_level) document.getElementById('experienceLevel').value = profile.experience_level;

	if (profile.profile_visible !== undefined) document.getElementById('profileVisible').checked = profile.profile_visible;
	if (profile.friend_requests !== undefined) document.getElementById('friendRequests').checked = profile.friend_requests;
	if (profile.email_notifications !== undefined) document.getElementById('emailNotifications').checked = profile.email_notifications;
}

function updateAvatars(avatarUrl) {
	[document.getElementById('avatarPreview'), document.getElementById('sidebarAvatar')].forEach(avatar => {
		if (avatar) {
			avatar.src = avatarUrl;
			avatar.style.animation = 'none';
			setTimeout(() => { avatar.style.animation = 'fadeIn 0.5s ease-out'; }, 10);
		}
	});
}

// ============================================
// EVENTLISTENER INITIALISIEREN
// ============================================

function initializeEventListeners() {
	const fileInput = document.getElementById('fileInput');
	if (fileInput) fileInput.addEventListener('change', handleFileSelect);

	const profileForm = document.getElementById('profileForm');
	if (profileForm) {
		profileForm.addEventListener('submit', handleProfileSubmit);
		profileForm.addEventListener('input', () => { profileChanged = true; });
	}

	const bioField = document.getElementById('bio');
	if (bioField) bioField.addEventListener('input', updateBioCounter);

	window.addEventListener('beforeunload', e => {
		if (profileChanged || avatarChanged) {
			e.preventDefault();
			e.returnValue = '';
		}
	});
}

// ============================================
// THEME TOGGLE
// ============================================

function initializeThemeToggle() {
	const themeToggle = document.getElementById('themeToggle');
	if (!themeToggle) return;

	if (localStorage.getItem('theme') === 'dark') {
		themeToggle.checked = true;
		applyDarkTheme();
	}

	themeToggle.addEventListener('change', e => {
		if (e.target.checked) { applyDarkTheme(); localStorage.setItem('theme','dark'); }
		else { applyLightTheme(); localStorage.setItem('theme','light'); }
	});
}

function applyDarkTheme() {
	document.documentElement.style.setProperty('--bg','#0b1220');
	document.documentElement.style.setProperty('--surface','#0f1724');
	document.documentElement.style.setProperty('--text','#e6eef8');
	document.documentElement.style.setProperty('--muted','#9fb0c8');
	document.documentElement.style.setProperty('--shadow','0 8px 30px rgba(2,6,23,0.6)');
}

function applyLightTheme() {
	['--bg','--surface','--text','--muted','--shadow'].forEach(prop => document.documentElement.style.removeProperty(prop));
}

// ============================================
// NAVIGATION
// ============================================

document.querySelectorAll('.nav-item').forEach(item => {
		item.addEventListener('click', function() {
			document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
			this.classList.add('active');

			const text = this.textContent.trim();
			if(text === 'Dashboard'){
				window.location.href = 'dashboard.html';
			} else if(text === 'Kurse'){
				window.location.href = 'kurse.html';
			} else if(text === 'Einstellungen'){
				window.location.href = 'einstellungen.html';
			} else {
				alert('Diese Funktion ist noch in Entwicklung!');
			}
		});
	});

// ============================================
// DATEIUPLOAD / AVATAR
// ============================================

function handleFileSelect(event) {
	const file = event.target.files[0];
	if (!file) return;

	const maxSize = 5 * 1024 * 1024;
	if (file.size > maxSize) { showError('Die Datei ist zu groß! Max 5MB'); event.target.value = ''; return; }

	const validTypes = ['image/jpeg','image/png','image/jpg','image/gif'];
	if (!validTypes.includes(file.type)) { showError('Ungültiges Dateiformat!'); event.target.value = ''; return; }

	const reader = new FileReader();
	reader.onload = e => { currentAvatar = e.target.result; updateAvatars(currentAvatar); avatarChanged = true; showSuccess('Foto hochgeladen! Vergiss nicht zu speichern.'); };
	reader.onerror = () => showError('Fehler beim Lesen der Datei');
	reader.readAsDataURL(file);
}

function generateRandomAvatar() {
	const randomSeed = Math.random().toString(36).substring(2,15);
	const styles = ['adventurer','avataaars','bottts','fun-emoji','lorelei','micah','miniavs','pixel-art'];
	const randomStyle = styles[Math.floor(Math.random()*styles.length)];
	currentAvatar = `https://api.dicebear.com/7.x/${randomStyle}/svg?seed=${randomSeed}`;
	updateAvatars(currentAvatar); avatarChanged = true; showSuccess('Zufälliger Avatar generiert! Vergiss nicht zu speichern.');
}

function resetAvatar() {
	if (confirm('Möchtest du das Profilbild wirklich zurücksetzen?')) {
		currentAvatar = originalAvatar;
		updateAvatars(currentAvatar);
		avatarChanged = false;
		const fileInput = document.getElementById('fileInput');
		if (fileInput) fileInput.value = '';
		showSuccess('Avatar zurückgesetzt!');
	}
}

// ============================================
// PROFIL SPEICHERN
// ============================================

async function handleProfileSubmit(event) {
	event.preventDefault();

	const firstName = document.getElementById('firstName').value.trim();
	const lastName = document.getElementById('lastName').value.trim();
	const bio = document.getElementById('bio').value.trim();
	const birthdate = document.getElementById('birthdate').value;
	const country = document.getElementById('country').value;
	const favoriteLanguage = document.getElementById('favoriteLanguage').value;
	const experienceLevel = document.getElementById('experienceLevel').value;

	if (!firstName || !lastName) { showError('Bitte fülle Vor- und Nachname aus!'); return; }
	if (bio.length > 500) { showError('Die Biografie darf maximal 500 Zeichen lang sein!'); return; }

	const fullName = `${firstName} ${lastName}`;
	const profileData = {
		name: fullName,
		birthdate: birthdate || null,
		country: country || null,
		bio: bio || null,
		favorite_language: favoriteLanguage || null,
		experience_level: experienceLevel || null,
		avatar_url: currentAvatar
	};

	const submitBtn = event.target.querySelector('button[type="submit"]');
	const originalText = submitBtn.innerHTML;
	submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Speichern...'; submitBtn.disabled = true;

	try {
		const response = await fetch('/api/profile', {
			method: 'PUT',
			headers: { 'Content-Type':'application/json' },
			credentials: 'include',
			body: JSON.stringify(profileData)
		});

		const result = await response.json();
		if (!response.ok || !result.success) throw new Error(result.message || 'Fehler beim Speichern');

		currentUser.name = fullName;
		originalAvatar = currentAvatar;
		profileChanged = false; avatarChanged = false;
		document.getElementById('sidebarName').textContent = fullName;
		showSuccess('✅ Profil erfolgreich gespeichert!');
		window.scrollTo({top:0, behavior:'smooth'});
	} catch (error) {
		console.error('Fehler beim Speichern:', error);
		showError('Fehler beim Speichern des Profils: ' + error.message);
	} finally {
		submitBtn.innerHTML = originalText;
		submitBtn.disabled = false;
	}
}

// ============================================
// PRIVACY SETTINGS
// ============================================

async function savePrivacySettings() {
	const privacyData = {
		profile_visible: document.getElementById('profileVisible').checked,
		friend_requests: document.getElementById('friendRequests').checked,
		email_notifications: document.getElementById('emailNotifications').checked
	};

	try {
		const response = await fetch('/api/privacy', {
			method:'PUT',
			headers:{ 'Content-Type':'application/json' },
			credentials:'include',
			body: JSON.stringify(privacyData)
		});
		const result = await response.json();
		if (!response.ok || !result.success) throw new Error(result.message || 'Fehler beim Speichern');
		showSuccess('🔐 Datenschutzeinstellungen gespeichert!');
	} catch (error) {
		console.error('Fehler beim Speichern der Datenschutzeinstellungen:', error);
		showError('Fehler beim Speichern der Datenschutzeinstellungen');
	}
}

// ============================================
// CANCEL CHANGES
// ============================================

function cancelChanges() {
	if (!profileChanged && !avatarChanged) return window.location.href='dashboard.html';
	if (confirm('Möchtest du alle Änderungen verwerfen?')) window.location.reload();
}

// ============================================
// BIO COUNTER
// ============================================

function updateBioCounter() {
	const bioField = document.getElementById('bio');
	const counter = document.getElementById('bioCounter');
	if (!bioField || !counter) return;
	const length = bioField.value.length;
	const maxLength = 500;
	counter.textContent = `${length} / ${maxLength} Zeichen`;
	counter.style.color = length > maxLength ? '#ef4444' : length > maxLength*0.9 ? '#f59e0b' : 'var(--muted)';
	bioField.style.borderColor = counter.style.color === 'var(--muted)' ? '#e2e8f0' : counter.style.color;
}

// ============================================
// MESSAGES
// ============================================

function showSuccess(message) {
	const el = document.getElementById('successMessage');
	const errorEl = document.getElementById('errorMessage');
	if (errorEl) errorEl.style.display = 'none';
	if (el) { el.textContent = message; el.style.display='flex'; setTimeout(()=>el.style.display='none',4000); }
}

function showError(message) {
	const el = document.getElementById('errorMessage');
	const successEl = document.getElementById('successMessage');
	if (successEl) successEl.style.display='none';
	if (el) { el.textContent = message; el.style.display='flex'; setTimeout(()=>el.style.display='none',5000); }
}

// ============================================
// EXPORT
// ============================================

window.generateRandomAvatar = generateRandomAvatar;
window.resetAvatar = resetAvatar;
window.savePrivacySettings = savePrivacySettings;
window.cancelChanges = cancelChanges;
