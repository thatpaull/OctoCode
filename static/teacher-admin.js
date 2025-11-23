let currentModalType = '';
let students = [];
let courses = [];
let tasks = [];

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('🚀 Initializing Teacher Dashboard...');
    await checkTeacherAuth();
    await loadData();
    setupNavigation();

    console.log('🎨 Rendering all sections...');
    renderDashboard();
    renderStudents();
    renderCourses();
    renderTasks();
    console.log('✅ Initialization complete');
}

async function checkTeacherAuth() {
    try {
        const res = await fetch('/api/check-auth', { credentials: 'include' });
        const data = await res.json();

        if (!data.authenticated || data.user.role !== 'teacher') {
            alert('Sie sind nicht als Lehrer angemeldet!');
            window.location.href = '/index.html';
            return;
        }

        document.querySelector('.teacher-name').textContent = data.user.name;
        if (data.user.avatar_url) {
            document.querySelector('.teacher-profile img').src = data.user.avatar_url;
        }
    } catch (error) {
        console.error('Auth check error:', error);
        window.location.href = '/index.html';
    }
}

async function loadData() {
    try {
        const studentsRes = await fetch('/api/teacher/students', { credentials: 'include' });
        if (studentsRes.ok) {
            students = await studentsRes.json();
            console.log('✅ Loaded students:', students.length);
        } else {
            console.error('❌ Failed to load students:', studentsRes.status);
            students = [];
        }
    } catch (error) {
        console.error('❌ Error loading students:', error);
        students = [];
    }

    try {
        const coursesRes = await fetch('/api/courses', { credentials: 'include' });
        if (coursesRes.ok) {
            courses = await coursesRes.json();
            console.log('✅ Loaded courses:', courses.length, courses);
        } else {
            console.error('❌ Failed to load courses:', coursesRes.status);
            courses = [];
        }
    } catch (error) {
        console.error('❌ Error loading courses:', error);
        courses = [];
    }

    try {
        const tasksRes = await fetch('/api/teacher/tasks', { credentials: 'include' });
        if (tasksRes.ok) {
            tasks = await tasksRes.json();
            console.log('✅ Loaded tasks:', tasks.length);
        } else {
            console.error('❌ Failed to load tasks:', tasksRes.status);
            tasks = [];
        }
    } catch (error) {
        console.error('❌ Error loading tasks:', error);
        tasks = [];
    }

    // Загружаем статистику
    try {
        const statsRes = await fetch('/api/teacher/stats', { credentials: 'include' });
        if (statsRes.ok) {
            const stats = await statsRes.json();
            console.log('✅ Loaded stats:', stats);
            updateDashboardStats(stats);
        }
    } catch (error) {
        console.error('❌ Error loading stats:', error);
    }
}

function updateDashboardStats(stats) {
    const totalStudentsEl = document.getElementById('totalStudents');
    const totalCoursesEl = document.getElementById('totalCourses');
    const totalTasksEl = document.getElementById('totalTasks');

    if (totalStudentsEl) totalStudentsEl.textContent = stats.totalStudents || 0;
    if (totalCoursesEl) totalCoursesEl.textContent = stats.totalCourses || 0;
    if (totalTasksEl) totalTasksEl.textContent = stats.totalTasks || 0;
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            const tab = item.getAttribute('data-tab');
            showTab(tab);
        });
    });
}

function showTab(tabName) {
    const allTabs = document.querySelectorAll('.tab-content');
    allTabs.forEach(tab => tab.classList.remove('active'));

    const targetTab = document.getElementById(`${tabName}-content`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    const titles = {
        'dashboard': '📊 Dashboard',
        'students': '👥 Schülerverwaltung',
        'courses': '📚 Kursverwaltung',
        'tasks': '📝 Aufgabenverwaltung',
        'settings': '⚙️ Einstellungen'
    };

    document.getElementById('pageTitle').textContent = titles[tabName] || 'Dashboard';
}

function renderDashboard() {
    const activityList = document.getElementById('activityList');
    const leaderboard = document.getElementById('leaderboard');

    if (activityList) {
        if (students.length === 0) {
            activityList.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">Keine Aktivitäten</div>';
        } else {
            activityList.innerHTML = students.slice(0, 5).map(student => `
                <div class="activity-item">
                    <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(student.name)}" alt="${student.name}" class="activity-avatar">
                    <div class="activity-info">
                        <div class="activity-name">${student.name}</div>
                        <div class="activity-action">hat eine Aufgabe abgeschlossen</div>
                    </div>
                    <div class="activity-time">${formatDate(student.created_at)}</div>
                </div>
            `).join('');
        }
    }

    if (leaderboard) {
        if (students.length === 0) {
            leaderboard.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">Keine Schüler</div>';
        } else {
            const sortedStudents = [...students].sort((a, b) => (b.points || 0) - (a.points || 0));
            leaderboard.innerHTML = sortedStudents.slice(0, 5).map((student, idx) => `
                <div class="leaderboard-item">
                    <div class="rank">${idx + 1}</div>
                    <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(student.name)}" alt="${student.name}">
                    <div class="student-name">${student.name}</div>
                    <div class="student-points">${student.points || 0} Punkte</div>
                </div>
            `).join('');
        }
    }
}

function renderStudents() {
    const studentsGrid = document.getElementById('studentsGrid');
    if (!studentsGrid) {
        console.error('❌ studentsGrid element not found');
        return;
    }

    console.log('🎨 Rendering students:', students.length);

    if (students.length === 0) {
        studentsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <h3 style="margin: 0; font-size: 18px;">Keine Schüler gefunden</h3>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Warten Sie auf neue Registrierungen</p>
            </div>
        `;
        return;
    }

    studentsGrid.innerHTML = students.map(student => `
        <div class="student-card">
            <div class="student-header">
                <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(student.name)}" alt="${student.name}">
                <div class="student-status active"></div>
            </div>
            <h4>${student.name}</h4>
            <p class="student-email">${student.email}</p>

            <div class="student-stats">
                <div class="stat-item">
                    <div class="stat-value">${student.points || 0}</div>
                    <div class="stat-label">Punkte</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${student.coursesCompleted || 0}</div>
                    <div class="stat-label">Kurse</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${student.progress || 0}%</div>
                    <div class="stat-label">Fortschritt</div>
                </div>
            </div>

            <div class="progress-bar">
                <div class="progress-fill" style="width: ${student.progress || 0}%"></div>
            </div>

            <div class="card-actions">
                <button class="btn-icon" onclick="viewStudent(${student.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    Details
                </button>
                <button class="btn-icon" onclick="editStudent(${student.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    Bearbeiten
                </button>
            </div>
        </div>
    `).join('');
}

function renderCourses() {
    const coursesList = document.getElementById('coursesList');
    if (!coursesList) {
        console.error('❌ coursesList element not found');
        return;
    }

    console.log('🎨 Rendering courses:', courses.length);

    if (courses.length === 0) {
        coursesList.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
                <h3 style="margin: 0; font-size: 18px;">Keine Kurse gefunden</h3>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Erstellen Sie Ihren ersten Kurs!</p>
            </div>
        `;
        return;
    }

    coursesList.innerHTML = courses.map(course => `
        <div class="course-card-admin">
            <div class="course-color-bar" style="background-color: ${course.color || '#3b82f6'}"></div>
            <div class="course-content">
                <div class="course-main">
                    <div>
                        <h3>${course.title || 'Unbenannter Kurs'}</h3>
                        <span class="course-category" style="background-color: ${course.color || '#3b82f6'}20; color: ${course.color || '#3b82f6'}">
                            ${course.category || 'Allgemein'}
                        </span>
                    </div>
                    <span class="status-badge ${course.status || 'active'}">
                        ${course.status === 'active' ? 'Aktiv' : 'Entwurf'}
                    </span>
                </div>

                <div class="course-stats-row">
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="9" cy="7" r="4"></circle>
                        </svg>
                        <span>${course.students || 0} Schüler</span>
                    </div>
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                        </svg>
                        <span>${course.total_lessons || 0} Lektionen</span>
                    </div>
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        <span>${course.duration || 'N/A'}</span>
                    </div>
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="8" r="7"></circle>
                            <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>
                        </svg>
                        <span>${course.rating || 0} ⭐</span>
                    </div>
                </div>

                <div class="course-actions">
                    <button class="btn-secondary" onclick="editCourse(${course.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        Bearbeiten
                    </button>
                    <button class="btn-secondary">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                        Vorschau
                    </button>
                    <button class="btn-danger" onclick="deleteCourse(${course.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `).join('');

    console.log('✅ Courses rendered successfully');
}

function renderTasks() {
    const tasksTableBody = document.getElementById('tasksTableBody');
    if (!tasksTableBody) {
        console.error('❌ tasksTableBody element not found');
        return;
    }

    console.log('🎨 Rendering tasks:', tasks.length);

    if (tasks.length === 0) {
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #666;">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <h3 style="margin: 0; font-size: 18px;">Keine Aufgaben gefunden</h3>
                    <p style="margin: 8px 0 0 0; font-size: 14px;">Erstellen Sie Ihre erste Aufgabe!</p>
                </td>
            </tr>
        `;
        return;
    }

    tasksTableBody.innerHTML = tasks.map(task => `
        <tr>
            <td class="task-title">${task.title}</td>
            <td>
                <span class="difficulty-badge ${(task.difficulty || 'mittel').toLowerCase()}">
                    ${task.difficulty || 'Mittel'}
                </span>
            </td>
            <td>${task.topic || '-'}</td>
            <td>
                <span class="language-badge">${task.language || 'Python'}</span>
            </td>
            <td>${task.submissions || 0}</td>
            <td>
                <span class="completion-rate">
                    ${task.submissions > 0 ? Math.round(((task.completed || 0) / task.submissions) * 100) : 0}%
                </span>
            </td>
            <td>${task.estimated_time || 30} min</td>
            <td>
                <div class="table-actions">
                    <button class="btn-icon-sm" onclick="editTask(${task.id})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon-sm">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </button>
                    <button class="btn-icon-sm danger" onclick="deleteTask(${task.id})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function filterStudents() {
    const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
    const filteredStudents = students.filter(s =>
        s.name.toLowerCase().includes(searchTerm) ||
        s.email.toLowerCase().includes(searchTerm)
    );

    const studentsGrid = document.getElementById('studentsGrid');
    studentsGrid.innerHTML = filteredStudents.map(student => `
        <div class="student-card">
            <div class="student-header">
                <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(student.name)}" alt="${student.name}">
                <div class="student-status active"></div>
            </div>
            <h4>${student.name}</h4>
            <p class="student-email">${student.email}</p>

            <div class="student-stats">
                <div class="stat-item">
                    <div class="stat-value">${student.points || 0}</div>
                    <div class="stat-label">Punkte</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${student.coursesCompleted || 0}</div>
                    <div class="stat-label">Kurse</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${student.progress || 0}%</div>
                    <div class="stat-label">Fortschritt</div>
                </div>
            </div>

            <div class="progress-bar">
                <div class="progress-fill" style="width: ${student.progress || 0}%"></div>
            </div>

            <div class="card-actions">
                <button class="btn-icon" onclick="viewStudent(${student.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    Details
                </button>
                <button class="btn-icon" onclick="editStudent(${student.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    Bearbeiten
                </button>
            </div>
        </div>
    `).join('');
}

function formatDate(dateString) {
    if (!dateString) return 'Kürzlich';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Heute';
    if (diffDays === 1) return 'Gestern';
    if (diffDays < 7) return `vor ${diffDays} Tagen`;
    return date.toLocaleDateString('de-DE');
}

function openModal(type, data = null) {
    currentModalType = type;
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    const titles = {
        'addStudent': 'Neuer Schüler',
        'editStudent': 'Schüler bearbeiten',
        'viewStudent': 'Schülerdetails',
        'addCourse': 'Neuer Kurs',
        'editCourse': 'Kurs bearbeiten',
        'addTask': 'Neue Aufgabe',
        'editTask': 'Aufgabe bearbeiten'
    };

    modalTitle.textContent = titles[type] || 'Modal';

    if (type === 'viewStudent') {
        const student = students.find(s => s.id === data);
        if (student) {
            modalBody.innerHTML = `
                <div class="student-details">
                    <div class="detail-header">
                        <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(student.name)}" alt="${student.name}" class="detail-avatar">
                        <div>
                            <h3>${student.name}</h3>
                            <p>${student.email}</p>
                        </div>
                    </div>
                    <div class="detail-stats">
                        <div class="detail-stat">
                            <span class="label">Punkte</span>
                            <span class="value">${student.points || 0}</span>
                        </div>
                        <div class="detail-stat">
                            <span class="label">Abgeschlossene Kurse</span>
                            <span class="value">${student.coursesCompleted || 0}</span>
                        </div>
                        <div class="detail-stat">
                            <span class="label">Aktive Kurse</span>
                            <span class="value">${student.activeCourses || 0}</span>
                        </div>
                        <div class="detail-stat">
                            <span class="label">Registriert seit</span>
                            <span class="value">${formatDate(student.created_at)}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('active');
    currentModalType = '';
}

function saveModal() {
    console.log('Saving...', currentModalType);
    alert('Änderungen gespeichert!');
    closeModal();
}

function viewStudent(id) {
    openModal('viewStudent', id);
}

function editStudent(id) {
    openModal('editStudent', id);
}

function editCourse(id) {
    openModal('editCourse', id);
}

function editTask(id) {
    openModal('editTask', id);
}

function deleteCourse(id) {
    if (confirm('Möchten Sie diesen Kurs wirklich löschen?')) {
        courses = courses.filter(c => c.id !== id);
        renderCourses();
        alert('Kurs gelöscht!');
    }
}

function deleteTask(id) {
    if (confirm('Möchten Sie diese Aufgabe wirklich löschen?')) {
        tasks = tasks.filter(t => t.id !== id);
        renderTasks();
        alert('Aufgabe gelöscht!');
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

document.getElementById('modal').addEventListener('click', (e) => {
    if (e.target.id === 'modal') {
        closeModal();
    }
});
