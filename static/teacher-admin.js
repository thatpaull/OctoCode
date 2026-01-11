let currentModalType = '';
let students = [];
let courses = [];
let tasks = [];
let quizResults = [];
let pdfQuizzes = [];

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('🚀 Initializing Teacher Dashboard...');

    await checkTeacherAuth();

    // Load all data in parallel for faster loading
    console.log('📊 Loading data...');
    await Promise.all([
        loadData(),
        loadQuizResults(),
        loadPDFQuizzes()
    ]);

    setupNavigation();

    console.log('🎨 Rendering all sections...');
    renderDashboard();
    renderStudents();
    renderCourses();
    renderTasks();
    renderQuizResults();
    renderPDFQuizzes();

    console.log('✅ Initialization complete');
    console.log(`📊 Loaded: ${students.length} students, ${courses.length} courses, ${tasks.length} tasks`);
    console.log(`📄 Loaded: ${pdfQuizzes.length} PDF quizzes, ${quizResults.length} quiz results`);
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
            console.log('✅ Loaded courses:', courses.length);
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

async function loadPDFQuizzes() {
    console.log('📄 Loading PDF quizzes...');
    try {
        const res = await fetch('/api/teacher/pdf-quizzes', { credentials: 'include' });
        console.log('📄 Response status:', res.status);

        if (res.ok) {
            const data = await res.json();
            pdfQuizzes = data.quizzes || [];
            console.log('✅ Loaded PDF quizzes:', pdfQuizzes.length);
        } else {
            console.warn('⚠️ Failed to load PDF quizzes:', res.status);
            pdfQuizzes = [];
        }
    } catch (error) {
        console.error('❌ Error loading PDF quizzes:', error);
        pdfQuizzes = [];
    }
}

async function loadQuizResults() {
    console.log('📊 Loading quiz results...');
    try {
        const res = await fetch('/api/teacher/quiz-results', { credentials: 'include' });
        console.log('Quiz results response status:', res.status);

        if (res.ok) {
            const data = await res.json();
            console.log('Quiz results data:', data);

            if (data.success && data.results) {
                quizResults = data.results;
                console.log('✅ Loaded quiz results:', quizResults.length);
            } else {
                console.warn('⚠️ No quiz results in response');
                quizResults = [];
            }
        } else {
            console.error('❌ Failed to load quiz results:', res.status);
            const errorText = await res.text();
            console.error('Error response:', errorText);
            quizResults = [];
        }
    } catch (error) {
        console.error('❌ Error loading quiz results:', error);
        quizResults = [];
    }
}

function renderPDFQuizzes() {
    console.log('🎨 Rendering PDF quizzes:', pdfQuizzes.length);
    const container = document.getElementById('pdfQuizzesContainer');

    if (!container) {
        console.error('❌ pdfQuizzesContainer element not found');
        return;
    }

    if (!pdfQuizzes || pdfQuizzes.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="12" y1="18" x2="12" y2="12"></line>
                    <line x1="9" y1="15" x2="15" y2="15"></line>
                </svg>
                <h3 style="margin: 0; font-size: 18px;">Keine PDF-Quizzes erstellt</h3>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Laden Sie ein PDF hoch, um ein Quiz zu generieren</p>
            </div>
        `;
        return;
    }

    container.innerHTML = pdfQuizzes.map(quiz => `
        <div class="course-card-admin">
            <div class="course-color-bar" style="background-color: #7c3aed"></div>
            <div class="course-content">
                <div class="course-main">
                    <div>
                        <h3>${quiz.title}</h3>
                        <span class="course-category" style="background-color: rgba(124,58,237,0.1); color: #7c3aed">
                            📄 ${quiz.filename}
                        </span>
                    </div>
                    <span class="status-badge active">
                        PDF-Quiz
                    </span>
                </div>
                <div class="course-stats-row">
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                        </svg>
                        <span>${quiz.course_title}</span>
                    </div>
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="9" cy="7" r="4"></circle>
                        </svg>
                        <span>${quiz.student_attempts} Versuche</span>
                    </div>
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                        </svg>
                        <span>Ø ${quiz.avg_score}%</span>
                    </div>
                    <div class="stat-box">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        <span>${formatDate(quiz.created_at)}</span>
                    </div>
                </div>
                <div class="course-actions">
                    <button class="btn-secondary" onclick="viewPDFQuizResults(${quiz.id})">
                        📊 Ergebnisse ansehen
                    </button>
                    <button class="btn-secondary" onclick="viewQuizDetails(${quiz.id})">
                        👁️ Quiz ansehen
                    </button>
                    <button class="btn-danger" onclick="deletePDFQuiz(${quiz.id})">
                        🗑️ Löschen
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// PDF Upload Modal
function openPDFUploadModal() {
    console.log('📄 Opening PDF upload modal, courses available:', courses.length);

    if (courses.length === 0) {
        alert('Bitte warten Sie, bis die Kurse geladen sind, oder laden Sie die Seite neu.');
        return;
    }

    currentModalType = 'uploadPDF';
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.textContent = '📄 PDF hochladen & Quiz generieren';

    modalBody.innerHTML = `
        <form id="pdfUploadForm" class="form" onsubmit="event.preventDefault(); return false;">
            <div class="form-group">
                <label>Quiz-Titel *</label>
                <input type="text" id="pdfQuizTitle" name="title" required placeholder="z.B. Python Grundlagen Test">
            </div>
            
            <div class="form-group">
                <label>Kurs auswählen *</label>
                <select id="pdfQuizCourse" name="course_id" required>
                    <option value="">-- Kurs wählen --</option>
                    ${courses.map(c => `<option value="${c.id}">${c.title}</option>`).join('')}
                </select>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Anzahl Fragen</label>
                    <select id="pdfQuizQuestions" name="num_questions">
                        <option value="5">5 Fragen</option>
                        <option value="10" selected>10 Fragen</option>
                        <option value="15">15 Fragen</option>
                        <option value="20">20 Fragen</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Schwierigkeit</label>
                    <select id="pdfQuizDifficulty" name="difficulty">
                        <option value="easy">Einfach</option>
                        <option value="medium" selected>Mittel</option>
                        <option value="hard">Schwer</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label>PDF-Datei hochladen *</label>
                <input type="file" id="pdfFile" name="pdf_file" accept=".pdf" required style="padding: 8px;">
                <small style="color: var(--muted); font-size: 12px; margin-top: 4px; display: block;">
                    Maximal 10MB. Das Quiz wird automatisch aus dem PDF-Inhalt generiert.
                </small>
            </div>
            
            <div id="uploadProgress" style="display: none; margin-top: 16px;">
                <div style="background: #f1f5f9; border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 12px;">
                        <span id="progressText">PDF wird verarbeitet...</span>
                    </div>
                    <div style="width: 100%; height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden;">
                        <div id="progressBar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s;"></div>
                    </div>
                </div>
            </div>
        </form>
    `;

    modal.classList.add('active');
}

// Handle PDF Upload
async function handlePDFUpload() {
    console.log('📤 Starting PDF upload...');

    const titleEl = document.getElementById('pdfQuizTitle');
    const courseEl = document.getElementById('pdfQuizCourse');
    const fileEl = document.getElementById('pdfFile');
    const questionsEl = document.getElementById('pdfQuizQuestions');
    const difficultyEl = document.getElementById('pdfQuizDifficulty');

    if (!titleEl || !courseEl || !fileEl) {
        console.error('❌ Form elements not found');
        alert('Fehler: Formular-Elemente nicht gefunden. Bitte Seite neu laden.');
        return;
    }

    const title = titleEl.value.trim();
    const courseId = courseEl.value;
    const pdfFile = fileEl.files[0];
    const numQuestions = questionsEl ? questionsEl.value : '10';
    const difficulty = difficultyEl ? difficultyEl.value : 'medium';

    console.log('📋 Form data:', { title, courseId, numQuestions, difficulty, fileName: pdfFile?.name });

    if (!title || !courseId || !pdfFile) {
        alert('Bitte füllen Sie alle Pflichtfelder aus');
        return;
    }

    if (!pdfFile.name.toLowerCase().endsWith('.pdf')) {
        alert('Bitte wählen Sie eine PDF-Datei aus');
        return;
    }

    // Create FormData manually to ensure all fields are included
    const formData = new FormData();
    formData.append('title', title);
    formData.append('course_id', courseId);
    formData.append('num_questions', numQuestions);
    formData.append('difficulty', difficulty);
    formData.append('pdf_file', pdfFile);

    // Show progress
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const saveBtn = document.querySelector('.modal-footer .btn-primary');

    progressDiv.style.display = 'block';
    saveBtn.disabled = true;
    saveBtn.style.opacity = '0.5';

    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        progressBar.style.width = progress + '%';

        if (progress < 30) {
            progressText.textContent = 'PDF wird hochgeladen...';
        } else if (progress < 60) {
            progressText.textContent = 'Text wird extrahiert...';
        } else {
            progressText.textContent = 'KI generiert Quiz-Fragen...';
        }
    }, 500);

    try {
        console.log('📡 Sending request to /api/teacher/upload-pdf-quiz...');
        const res = await fetch('/api/teacher/upload-pdf-quiz', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        console.log('📥 Response received:', res.status, res.statusText);
        clearInterval(progressInterval);
        progressBar.style.width = '100%';

        let data;
        try {
            const responseText = await res.text();
            console.log('📄 Response text:', responseText.substring(0, 200));
            data = JSON.parse(responseText);
        } catch (jsonError) {
            console.error('❌ JSON parse error:', jsonError);
            throw new Error(`Server error: ${res.status} ${res.statusText}. Bitte versuchen Sie es erneut.`);
        }

        console.log('✅ Parsed response:', data);

        if (!res.ok) {
            throw new Error(data.message || `Server error: ${res.status}`);
        }

        if (data.success) {
            progressText.textContent = '✅ Quiz erfolgreich erstellt!';
            setTimeout(() => {
                closeModal();
                alert(data.message);
                loadPDFQuizzes().then(() => renderPDFQuizzes());
            }, 1000);
        } else {
            throw new Error(data.message || 'Unbekannter Fehler');
        }

    } catch (error) {
        clearInterval(progressInterval);
        console.error('❌ PDF upload error:', error);
        progressDiv.style.display = 'none';
        saveBtn.disabled = false;
        saveBtn.style.opacity = '1';
        alert('Fehler: ' + error.message);
    }
}

// View PDF Quiz Results
async function viewPDFQuizResults(quizId) {
    try {
        const res = await fetch(`/api/teacher/quiz/${quizId}/details`, { credentials: 'include' });
        const data = await res.json();

        if (!data.success) {
            alert('Fehler beim Laden der Ergebnisse');
            return;
        }

        // Filter quiz results for this specific quiz
        const quizSpecificResults = quizResults.filter(r => r.quiz_id === quizId);

        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = `📊 Ergebnisse: ${data.quiz.title}`;

        if (quizSpecificResults.length === 0) {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                        <path d="M9 11H3v2h6m-6 6h6v2H3m10 2l-1.5-1.5L10 21v-6l1.5 1.5L13 15"></path>
                    </svg>
                    <h3 style="margin: 0; font-size: 18px;">Noch keine Ergebnisse</h3>
                    <p style="margin: 8px 0 0 0; font-size: 14px;">Kein Schüler hat dieses Quiz absolviert</p>
                </div>
            `;
        } else {
            const avgScore = quizSpecificResults.reduce((sum, r) => sum + r.score, 0) / quizSpecificResults.length;
            const passedCount = quizSpecificResults.filter(r => r.passed).length;

            modalBody.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem;">
                    <div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #1e3a8a; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Gesamt</div>
                        <div style="font-size: 24px; font-weight: 800; color: #2563eb;">${quizSpecificResults.length}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #d1fae5, #a7f3d0); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #065f46; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Bestanden</div>
                        <div style="font-size: 24px; font-weight: 800; color: #10b981;">${passedCount}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #78350f; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Ø Punkte</div>
                        <div style="font-size: 24px; font-weight: 800; color: #f59e0b;">${Math.round(avgScore)}%</div>
                    </div>
                </div>
                
                <h4 style="margin: 0 0 1rem 0; color: #1e293b;">Schüler-Ergebnisse</h4>
                ${quizSpecificResults.map(result => `
                    <div style="background: white; border: 2px solid ${result.passed ? '#10b981' : '#ef4444'}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <img src="${result.student_avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(result.student_name)}" 
                                     style="width: 40px; height: 40px; border-radius: 10px;">
                                <div>
                                    <div style="font-weight: 700; color: #1e293b;">${result.student_name}</div>
                                    <div style="font-size: 12px; color: #64748b;">${formatDate(result.submitted_at)}</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 24px; font-weight: 800; color: ${result.passed ? '#10b981' : '#ef4444'};">
                                    ${result.score}%
                                </div>
                                <div style="font-size: 12px; color: #64748b;">
                                    ${result.correct_answers || 0} / ${result.total_questions || 0} richtig
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            `;
        }

        modal.classList.add('active');

    } catch (error) {
        console.error('Error loading PDF quiz results:', error);
        alert('Fehler beim Laden der Ergebnisse');
    }
}

// Delete PDF Quiz
async function deletePDFQuiz(quizId) {
    if (!confirm('Möchten Sie dieses PDF-Quiz wirklich löschen? Alle Schüler-Ergebnisse gehen verloren.')) {
        return;
    }

    try {
        const res = await fetch(`/api/teacher/quiz/${quizId}/delete`, {
            method: 'DELETE',
            credentials: 'include'
        });

        const data = await res.json();

        if (data.success) {
            alert('Quiz erfolgreich gelöscht');
            await loadPDFQuizzes();
            renderPDFQuizzes();
        } else {
            alert('Fehler: ' + data.message);
        }

    } catch (error) {
        console.error('Error deleting quiz:', error);
        alert('Fehler beim Löschen');
    }
}

// Update saveModal function
function saveModal() {
    if (currentModalType === 'uploadPDF') {
        handlePDFUpload();
    } else {
        console.log('Saving...', currentModalType);
        alert('Änderungen gespeichert!');
        closeModal();
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
            const tab = item.getAttribute('data-tab');
            if (!tab) return;

            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
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

    // Render PDF quizzes when tab is shown
    if (tabName === 'pdf-quizzes') {
        console.log('📄 Switching to PDF-Quizzes tab');
        renderPDFQuizzes();
    }

    const titles = {
        'dashboard': '📊 Dashboard',
        'students': '👥 Schülerverwaltung',
        'courses': '📚 Kursverwaltung',
        'tasks': '📝 Aufgabenverwaltung',
        'pdf-quizzes': '📄 PDF-Quizzes',
        'quiz-results': '🎯 Quiz-Ergebnisse',
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
    if (!studentsGrid) return;

    if (students.length === 0) {
        studentsGrid.innerHTML = `
            <div style="grid-column: 1
            /-1; text-align: center; padding: 40px; color: #666;">
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
    if (!coursesList) return;

    if (courses.length === 0) {
        coursesList.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
                <h3 style="margin: 0; font-size: 18px;">Keine Kurse gefunden</h3>
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
                </div>
                <div class="course-actions">
                    <button class="btn-secondary" onclick="editCourse(${course.id})">Bearbeiten</button>
                    <button class="btn-secondary">Vorschau</button>
                    <button class="btn-danger" onclick="deleteCourse(${course.id})">Löschen</button>
                </div>
            </div>
        </div>
    `).join('');
}

function renderTasks() {
    const tasksTableBody = document.getElementById('tasksTableBody');
    if (!tasksTableBody) return;

    if (tasks.length === 0) {
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #666;">
                    <h3>Keine Aufgaben gefunden</h3>
                </td>
            </tr>
        `;
        return;
    }

    tasksTableBody.innerHTML = tasks.map(task => `
        <tr>
            <td class="task-title">${task.title}</td>
            <td><span class="difficulty-badge ${(task.difficulty || 'mittel').toLowerCase()}">${task.difficulty || 'Mittel'}</span></td>
            <td>${task.topic || '-'}</td>
            <td><span class="language-badge">${task.language || 'Python'}</span></td>
            <td>${task.submissions || 0}</td>
            <td><span class="completion-rate">${task.submissions > 0 ? Math.round(((task.completed || 0) / task.submissions) * 100) : 0}%</span></td>
            <td>${task.estimated_time || 30} min</td>
            <td>
                <div class="table-actions">
                    <button class="btn-icon-sm" onclick="editTask(${task.id})">✏️</button>
                    <button class="btn-icon-sm">👁️</button>
                    <button class="btn-icon-sm danger" onclick="deleteTask(${task.id})">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderQuizResults() {
    const quizResultsTable = document.getElementById('quizResultsTable');
    if (!quizResultsTable) {
        console.error('❌ quizResultsTable element not found');
        return;
    }

    console.log('🎨 Rendering quiz results:', quizResults.length);

    if (quizResults.length === 0) {
        quizResultsTable.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #666;">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 16px; opacity: 0.3;">
                        <path d="M9 11H3v2h6m-6 6h6v2H3m10 2l-1.5-1.5L10 21v-6l1.5 1.5L13 15m6.36-4L12 3.64 4.64 11 12 18.36 19.36 11M12 6.73l4.27 4.27-4.27 4.27-4.27-4.27"></path>
                    </svg>
                    <h3 style="margin: 0; font-size: 18px;">Keine Quiz-Ergebnisse gefunden</h3>
                    <p style="margin: 8px 0 0 0; font-size: 14px;">Schüler haben noch keine Quizzes abgeschlossen</p>
                </td>
            </tr>
        `;
        return;
    }

    quizResultsTable.innerHTML = quizResults.map(result => {
        const statusColor = result.passed ? '#10b981' : '#ef4444';
        const statusText = result.passed ? '✅ Bestanden' : '❌ Nicht bestanden';

        return `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <img src="${result.student_avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(result.student_name)}" 
                             alt="${result.student_name}" 
                             style="width: 40px; height: 40px; border-radius: 10px;">
                        <div>
                            <div style="font-weight: 700; color: #1e293b;">${result.student_name}</div>
                            <div style="font-size: 12px; color: #64748b;">${result.student_email}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <div style="font-weight: 600; color: #1e293b;">${result.course_title}</div>
                    <div style="font-size: 12px; color: #64748b;">${result.quiz_title}</div>
                </td>
                <td>
                    <span style="display: inline-block; padding: 4px 12px; background: #ede9fe; color: #7c3aed; border-radius: 20px; font-size: 12px; font-weight: 700;">
                        Versuch #${result.attempt_number}
                    </span>
                </td>
                <td>
                    <div style="font-weight: 800; font-size: 18px; color: ${statusColor};">
                        ${result.score}%
                    </div>
                    <div style="font-size: 11px; color: #64748b;">
                        ${result.correct_answers || 0} / ${result.total_questions || 0} richtig
                    </div>
                </td>
                <td>
                    <span style="color: ${statusColor}; font-weight: 700; font-size: 13px;">
                        ${statusText}
                    </span>
                </td>
                <td>
                    <div style="font-size: 13px; color: #475569;">
                        ${formatDate(result.submitted_at)}
                    </div>
                </td>
                <td>
                    ${result.feedback_parsed ? `
                        <div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: #64748b;">
                            💡 ${result.feedback_parsed.message}
                        </div>
                    ` : '<span style="color: #94a3b8; font-size: 13px;">-</span>'}
                </td>
                <td>
                    <div class="table-actions">
                        <button class="btn-icon-sm" onclick="viewQuizDetails(${result.quiz_id})" title="Details anzeigen">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                        </button>
                        <button class="btn-icon-sm" onclick="viewStudentQuizHistory(${result.user_id})" title="Schüler-Historie">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                            </svg>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function viewQuizDetails(quizId) {
    try {
        const res = await fetch(`/api/teacher/quiz/${quizId}/details`, { credentials: 'include' });
        const data = await res.json();

        if (!data.success) {
            alert('Quiz nicht gefunden');
            return;
        }

        const quiz = data.quiz;
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = `📊 Quiz Details - ${quiz.quiz_title}`;

        let questionsHtml = '';
        if (quiz.questions && quiz.questions.length > 0) {
            questionsHtml = quiz.questions.map((q, idx) => `
                <div style="background: ${q.is_correct ? '#f0fdf4' : '#fef2f2'}; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border-left: 4px solid ${q.is_correct ? '#10b981' : '#ef4444'};">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                        <div style="font-weight: 700; color: #1e293b;">
                            Frage ${idx + 1}: ${q.is_correct ? '✅' : '❌'}
                        </div>
                        <span style="padding: 4px 12px; background: rgba(255,255,255,0.7); border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                            ${q.difficulty || 'Medium'}
                        </span>
                    </div>
                    <div style="margin-bottom: 1rem; color: #374151; font-weight: 500;">
                        ${q.question}
                    </div>
                    ${q.code ? `
                        <div style="background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-family: monospace; font-size: 13px; overflow-x: auto;">
                            <pre style="margin: 0;">${q.code}</pre>
                        </div>
                    ` : ''}
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="font-size: 13px; color: #64748b;">Antwortmöglichkeiten:</strong>
                    </div>
                    ${q.options.map((opt, optIdx) => `
                        <div style="padding: 0.75rem; margin: 0.5rem 0; border-radius: 8px; background: ${
                            optIdx === q.correct_answer ? 'rgba(16, 185, 129, 0.1)' : 
                            optIdx === q.user_answer && optIdx !== q.correct_answer ? 'rgba(239, 68, 68, 0.1)' : 
                            'rgba(255, 255, 255, 0.7)'
                        }; border: 2px solid ${
                            optIdx === q.correct_answer ? '#10b981' : 
                            optIdx === q.user_answer && optIdx !== q.correct_answer ? '#ef4444' : 
                            'transparent'
                        };">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                ${optIdx === q.correct_answer ? '✅' : 
                                  optIdx === q.user_answer && optIdx !== q.correct_answer ? '❌' : 
                                  '⚪'}
                                <span style="font-weight: ${optIdx === q.user_answer || optIdx === q.correct_answer ? '700' : '400'};">
                                    ${String.fromCharCode(65 + optIdx)}. ${opt}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                    <div style="margin-top: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.5); border-radius: 8px; font-size: 13px;">
                        <strong>💡 Erklärung:</strong> ${q.explanation}
                    </div>
                </div>
            `).join('');
        }

        modalBody.innerHTML = `
            <div style="margin-bottom: 2rem;">
                <h4 style="margin: 0; color: #1e293b;">Schüler: ${quiz.student_name}</h4>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 14px;">${quiz.student_email}</p>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1.5rem 0;">
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">Punkte</div>
                        <div style="font-size: 24px; font-weight: 800; color: ${quiz.passed ? '#10b981' : '#ef4444'};">
                            ${quiz.score}%
                        </div>
                    </div>
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">Status</div>
                        <div style="font-size: 16px; font-weight: 700; color: ${quiz.passed ? '#10b981' : '#ef4444'};">
                            ${quiz.passed ? '✅ Bestanden' : '❌ Nicht bestanden'}
                        </div>
                    </div>
                </div>
            </div>
            
            <h4 style="margin: 0 0 1rem 0; color: #1e293b;">📝 Fragen & Antworten</h4>
            ${questionsHtml || '<p style="color: #64748b;">Keine Fragen verfügbar</p>'}
        `;

        modal.classList.add('active');

    } catch (error) {
        console.error('Error loading quiz details:', error);
        alert('Fehler beim Laden der Quiz-Details');
    }
}

async function viewStudentQuizHistory(studentId) {
    try {
        const res = await fetch(`/api/teacher/student/${studentId}/quiz-results`, { credentials: 'include' });
        const data = await res.json();

        if (!data.success) {
            alert('Schüler nicht gefunden');
            return;
        }

        const student = data.student;
        const results = data.results;
        const stats = data.statistics;

        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = `📊 Quiz-Historie - ${student.name}`;

        modalBody.innerHTML = `
            <div style="margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
                    <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(student.name)}" 
                         alt="${student.name}" 
                         style="width: 60px; height: 60px; border-radius: 12px;">
                    <div>
                        <h4 style="margin: 0; color: #1e293b;">${student.name}</h4>
                        <p style="margin: 4px 0 0 0; color: #64748b; font-size: 14px;">${student.email}</p>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
                    <div style="background: linear-gradient(135deg, #ede9fe, #ddd6fe); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #6b21a8; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Gesamt</div>
                        <div style="font-size: 24px; font-weight: 800; color: #7c3aed;">${stats.total_quizzes}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #d1fae5, #a7f3d0); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #065f46; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Bestanden</div>
                        <div style="font-size: 24px; font-weight: 800; color: #10b981;">${stats.passed_quizzes}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #fee2e2, #fecaca); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #7f1d1d; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Nicht bestanden</div>
                        <div style="font-size: 24px; font-weight: 800; color: #ef4444;">${stats.failed_quizzes}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); padding: 1rem; border-radius: 10px;">
                        <div style="font-size: 11px; color: #1e3a8a; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Ø Punkte</div>
                        <div style="font-size: 24px; font-weight: 800; color: #2563eb;">${stats.average_score}%</div>
                    </div>
                </div>
            </div>
            
            <h4 style="margin: 0 0 1rem 0; color: #1e293b;">Verlauf</h4>
            ${results.length === 0 ? `
                <p style="text-align: center; padding: 2rem; color: #64748b;">Keine Quiz-Ergebnisse vorhanden</p>
            ` : results.map(result => `
                <div style="background: white; border: 2px solid ${result.passed ? '#10b981' : '#ef4444'}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                        <div>
                            <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">
                                ${result.course_title}
                            </div>
                            <div style="font-size: 13px; color: #64748b;">
                                ${result.quiz_title}
                            </div>
                        </div>
                        <span style="padding: 6px 14px; background: ${result.passed ? '#d1fae5' : '#fee2e2'}; color: ${result.passed ? '#059669' : '#dc2626'}; border-radius: 20px; font-size: 12px; font-weight: 700;">
                            ${result.passed ? '✅ Bestanden' : '❌ Nicht bestanden'}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                        <div>
                            <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Punkte</div>
                            <div style="font-size: 20px; font-weight: 800; color: ${result.passed ? '#10b981' : '#ef4444'};">
                                ${result.score}%
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Richtig</div>
                            <div style="font-size: 16px; font-weight: 700; color: #475569;">
                                ${result.correct_answers} / ${result.total_questions}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Datum</div>
                            <div style="font-size: 13px; font-weight: 600; color: #475569;">
                                ${formatDate(result.submitted_at)}
                            </div>
                        </div>
                    </div>
                    <button class="btn-secondary" onclick="viewQuizDetails(${result.quiz_id})" style="margin-top: 1rem; width: 100%;">
                        Details anzeigen
                    </button>
                </div>
            `).join('')}
        `;

        modal.classList.add('active');

    } catch (error) {
        console.error('Error loading student quiz history:', error);
        alert('Fehler beim Laden der Quiz-Historie');
    }
}

function filterStudents() {
    const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
    const filteredStudents = students.filter(s =>
        s.name.toLowerCase().includes(searchTerm) ||
        s.email.toLowerCase().includes(searchTerm)
    );

    const studentsGrid = document.getElementById('studentsGrid');
    if (!studentsGrid) return;

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

function filterQuizResults() {
    const searchTerm = document.getElementById('quizSearch').value.toLowerCase();
    const filteredResults = quizResults.filter(r =>
        r.student_name.toLowerCase().includes(searchTerm) ||
        r.student_email.toLowerCase().includes(searchTerm) ||
        r.course_title.toLowerCase().includes(searchTerm) ||
        r.quiz_title.toLowerCase().includes(searchTerm)
    );

    const originalResults = quizResults;
    quizResults = filteredResults;
    renderQuizResults();
    quizResults = originalResults;
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

// Modal click outside to close
document.addEventListener('click', (e) => {
    const modal = document.getElementById('modal');
    if (e.target === modal) {
        closeModal();
    }

});