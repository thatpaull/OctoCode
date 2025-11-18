let currentUser = null;
let originalAvatar = null;
let currentAvatar = null;
let avatarChanged = false;
let profileChanged = false;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Loading teacher settings...');
    try {
        await loadUserData();
        initializeEventListeners();
        console.log('Settings loaded successfully!');
    } catch (error) {
        console.error('Error loading settings:', error);
    }
});

async function loadUserData() {
    try {
        const response = await fetch('/api/check-auth', { credentials: 'include' });
        const data = await response.json();

        if (!data.authenticated || data.user.role !== 'teacher') {
            alert('Sie sind nicht als Lehrer angemeldet!');
            return window.location.href = '/index.html';
        }

        currentUser = data.user;
        await loadUserProfile();
        updateUI(currentUser);
    } catch (error) {
        console.error('Error loading user data:', error);
        alert('Verbindungsfehler zum Server');
        window.location.href = '/index.html';
    }
}

async function loadUserProfile() {
    try {
        const response = await fetch('/api/profile', { credentials: 'include' });
        if (!response.ok) throw new Error('Profile loading failed');
        const profile = await response.json();

        originalAvatar = profile.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(currentUser.name)}`;
        currentAvatar = originalAvatar;

        updateFormWithProfile(profile);
        updateAvatars(currentAvatar);
    } catch (error) {
        console.error('Error loading profile:', error);
        originalAvatar = currentAvatar = `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(currentUser.name)}`;
        updateAvatars(currentAvatar);
    }
}

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

    if (profile.profile_visible !== undefined) document.getElementById('profileVisible').checked = profile.profile_visible;
    if (profile.email_notifications !== undefined) document.getElementById('emailNotifications').checked = profile.email_notifications;

    const pushNotifications = document.getElementById('pushNotifications');
    if (pushNotifications) pushNotifications.checked = true;
}

function updateAvatars(avatarUrl) {
    [document.getElementById('avatarPreview'), document.getElementById('sidebarAvatar')].forEach(avatar => {
        if (avatar) {
            avatar.src = avatarUrl;
        }
    });
}

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

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('Die Datei ist zu groß! Max 5MB');
        event.target.value = '';
        return;
    }

    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showError('Ungültiges Dateiformat!');
        event.target.value = '';
        return;
    }

    const reader = new FileReader();
    reader.onload = e => {
        currentAvatar = e.target.result;
        updateAvatars(currentAvatar);
        avatarChanged = true;
        showSuccess('Foto hochgeladen! Vergessen Sie nicht zu speichern.');
    };
    reader.onerror = () => showError('Fehler beim Lesen der Datei');
    reader.readAsDataURL(file);
}

function generateRandomAvatar() {
    const randomSeed = Math.random().toString(36).substring(2, 15);
    const styles = ['adventurer', 'avataaars', 'bottts', 'fun-emoji', 'lorelei', 'micah', 'miniavs', 'pixel-art'];
    const randomStyle = styles[Math.floor(Math.random() * styles.length)];
    currentAvatar = `https://api.dicebear.com/7.x/${randomStyle}/svg?seed=${randomSeed}`;
    updateAvatars(currentAvatar);
    avatarChanged = true;
    showSuccess('Zufälliger Avatar generiert! Vergessen Sie nicht zu speichern.');
}

function resetAvatar() {
    if (confirm('Möchten Sie das Profilbild wirklich zurücksetzen?')) {
        currentAvatar = originalAvatar;
        updateAvatars(currentAvatar);
        avatarChanged = false;
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';
        showSuccess('Avatar zurückgesetzt!');
    }
}

async function handleProfileSubmit(event) {
    event.preventDefault();

    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const bio = document.getElementById('bio').value.trim();
    const birthdate = document.getElementById('birthdate').value;
    const country = document.getElementById('country').value;

    if (!firstName || !lastName) {
        showError('Bitte füllen Sie Vor- und Nachname aus!');
        return;
    }
    if (bio.length > 500) {
        showError('Die Biografie darf maximal 500 Zeichen lang sein!');
        return;
    }

    const fullName = `${firstName} ${lastName}`;
    const profileData = {
        name: fullName,
        birthdate: birthdate || null,
        country: country || null,
        bio: bio || null,
        avatar_url: currentAvatar
    };

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> Speichern...';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(profileData)
        });

        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || 'Fehler beim Speichern');

        currentUser.name = fullName;
        originalAvatar = currentAvatar;
        profileChanged = false;
        avatarChanged = false;
        document.getElementById('sidebarName').textContent = fullName;
        showSuccess('✅ Profil erfolgreich gespeichert!');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
        console.error('Error saving profile:', error);
        showError('Fehler beim Speichern des Profils: ' + error.message);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function savePrivacySettings() {
    const privacyData = {
        profile_visible: document.getElementById('profileVisible').checked,
        email_notifications: document.getElementById('emailNotifications').checked
    };

    try {
        const response = await fetch('/api/privacy', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(privacyData)
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || 'Fehler beim Speichern');
        showSuccess('🔒 Datenschutzeinstellungen gespeichert!');
    } catch (error) {
        console.error('Error saving privacy settings:', error);
        showError('Fehler beim Speichern der Datenschutzeinstellungen');
    }
}

function updateBioCounter() {
    const bioField = document.getElementById('bio');
    const counter = document.getElementById('bioCounter');
    if (!bioField || !counter) return;
    const length = bioField.value.length;
    const maxLength = 500;
    counter.textContent = `${length} / ${maxLength} Zeichen`;

    if (length > maxLength) {
        counter.style.color = '#ef4444';
        bioField.style.borderColor = '#ef4444';
    } else if (length > maxLength * 0.9) {
        counter.style.color = '#f59e0b';
        bioField.style.borderColor = '#f59e0b';
    } else {
        counter.style.color = '#64748b';
        bioField.style.borderColor = '#e2e8f0';
    }
}

function showSuccess(message) {
    const el = document.getElementById('successMessage');
    const errorEl = document.getElementById('errorMessage');
    if (errorEl) errorEl.style.display = 'none';
    if (el) {
        el.textContent = message;
        el.style.display = 'flex';
        setTimeout(() => el.style.display = 'none', 4000);
    }
}

function showError(message) {
    const el = document.getElementById('errorMessage');
    const successEl = document.getElementById('successMessage');
    if (successEl) successEl.style.display = 'none';
    if (el) {
        el.textContent = message;
        el.style.display = 'flex';
        setTimeout(() => el.style.display = 'none', 5000);
    }
}

function logout() {
    if (confirm('Möchten Sie sich wirklich abmelden?')) {
        fetch('/api/logout', { method: 'POST', credentials: 'include' })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                window.location.href = '/index.html';
            })
            .catch(err => console.error(err));
    }
}

window.generateRandomAvatar = generateRandomAvatar;
window.resetAvatar = resetAvatar;
window.savePrivacySettings = savePrivacySettings;
window.logout = logout;
