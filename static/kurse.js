let currentUser = null;
let myCourses = [];
let allCourses = [];
let currentFilter = 'all';

// ========================
// BENUTZERDATEN LADEN
// ========================
async function loadUserData() {
    try {
        const res = await fetch('/api/check-auth', { credentials: 'include' });
        const data = await res.json();

        if (!data.authenticated) {
            alert('Sie sind nicht angemeldet!');
            return window.location.href = '/';
        }

        currentUser = data.user;
        document.getElementById('welcomeHeader').textContent = `Willkommen, ${currentUser.name} 👋`;
        document.getElementById('sidebarName').textContent = currentUser.name;
        document.getElementById('sidebarAvatar').src = currentUser.avatar_url || `/img/kid-avatar.jpg`;

    } catch (err) {
        console.error('Fehler beim Laden der Benutzerdaten:', err);
        alert('Verbindungsfehler zum Server');
        window.location.href = '/';
    }
}

// ========================
// KURSE LADEN
// ========================
async function loadCourses() {
    try {
        const res = await fetch('/api/courses', { credentials: 'include' });
        allCourses = await res.json();

        const myRes = await fetch('/api/my-courses', { credentials: 'include' });
        myCourses = await myRes.json();

        renderFilterBar();
        renderCourses();

    } catch (err) {
        console.error('Fehler beim Laden der Kurse:', err);
        alert('Fehler beim Laden der Kurse vom Server');
    }
}

// ========================
// RENDER FILTER
// ========================
function renderFilterBar() {
    const filterBar = document.getElementById('filterBar');
    const categories = ['all', ...new Set(allCourses.map(c => c.category))];
    filterBar.innerHTML = '';
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
        btn.className = `filter-btn ${currentFilter === cat ? 'active' : ''}`;
        btn.addEventListener('click', () => {
            currentFilter = cat;
            renderFilterBar();
            renderCourses();
        });
        filterBar.appendChild(btn);
    });
}

// ========================
// RENDER COURSES
// ========================
function renderCourses() {
    const container = document.getElementById('coursesContainer');
    container.innerHTML = '';

    const coursesToShow = currentFilter === 'all'
        ? allCourses
        : allCourses.filter(c => c.category === currentFilter);

    coursesToShow.forEach(course => {
        const enrolled = myCourses.some(c => c.id === course.id);

        const card = document.createElement('div');
        card.className = 'course-card';

      // Картинка курса
const img = document.createElement('img');
img.src = course.image_url; // теперь обязательно указываем картинку в каждом курсе
img.alt = course.title;
card.appendChild(img);


        // Бейдж категории
        const badge = document.createElement('div');
        badge.className = 'category-badge';
        badge.style.background = course.color || '#3b82f6';
        badge.textContent = course.category;
        card.appendChild(badge);

        // Название
        const title = document.createElement('h4');
        title.textContent = course.title;
        card.appendChild(title);

        // Описание
        const desc = document.createElement('p');
        desc.textContent = course.description;
        card.appendChild(desc);

        // Прогресс
        const progressLine = document.createElement('div');
        progressLine.className = 'progress-line';
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.style.width = '0%';
        progressLine.appendChild(progressBar);
        card.appendChild(progressLine);

        setTimeout(() => {
            progressBar.style.width = `${course.progress || 0}%`;
        }, 50);

        // Статистика
        const stats = document.createElement('div');
        stats.className = 'stats';
        stats.textContent = `${course.lessonsCompleted || 0}/${course.totalLessons || 0} lessons • ${course.duration || 'N/A'} • ${course.rating || 0}★`;
        card.appendChild(stats);

        // Кнопка enroll
        const btn = document.createElement('button');
        btn.className = `btn-enroll ${enrolled ? 'enrolled' : 'not-enrolled'}`;
        btn.textContent = enrolled ? 'Abmelden' : 'Anmelden';
        btn.addEventListener('click', () => toggleEnrollment(course.id, btn));
        card.appendChild(btn);

        container.appendChild(card);
    });
}

// ========================
// ENROLL / UNENROLL
// ========================
async function toggleEnrollment(courseId, btn) {
    const enrolled = myCourses.some(c => c.id === courseId);
    try {
        const res = await fetch('/api/enroll', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ course_id: courseId, enroll: !enrolled })
        });
        const data = await res.json();
        if (!res.ok || !data.success) throw new Error(data.message || 'Fehler');

        if (!enrolled) {
            myCourses.push(allCourses.find(c => c.id === courseId));
            btn.className = 'btn-enroll enrolled';
            btn.textContent = 'Abmelden';
        } else {
            myCourses = myCourses.filter(c => c.id !== courseId);
            btn.className = 'btn-enroll not-enrolled';
            btn.textContent = 'Anmelden';
        }
    } catch (err) {
        console.error(err);
        alert('Fehler beim Aktualisieren der Anmeldung');
    }
}

// ========================
// SIDEBAR NAVIGATION
// ========================
function initSidebarNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            const text = this.textContent.trim();
            if(text === 'Dashboard'){
                window.location.href = 'dashboard.html';
            } else if(text === 'Kurse'){
                window.location.href = 'kurse.html';
            }

			else if(text === 'Einstellungen'){
                window.location.href = 'einstellungen.html';
            }
			else {
                alert('Diese Funktion ist noch in Entwicklung!');
            }
        });
    });
}

// ========================
// INITIALISIERUNG
// ========================
document.addEventListener('DOMContentLoaded', async () => {
    await loadUserData();
    await loadCourses();
    initSidebarNavigation();
});
