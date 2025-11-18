const heroTitle = document.querySelector('.hero-title');
if (heroTitle) {
	const text = heroTitle.textContent.trim();
	heroTitle.textContent = '';

	text.split(' ').forEach((word, wi) => {
		const wordSpan = document.createElement('span');
		wordSpan.classList.add('word');

		word.split('').forEach((char, ci) => {
			const charSpan = document.createElement('span');
			charSpan.classList.add('char');
			charSpan.textContent = char;

			if (word === "Coding") charSpan.classList.add('highlight');

			charSpan.style.animationDelay = `${wi * 0.3 + ci * 0.05}s`;
			wordSpan.appendChild(charSpan);
		});

		heroTitle.appendChild(wordSpan);
		heroTitle.appendChild(document.createTextNode(' '));
	});
}

const cats = document.querySelectorAll('.cat');
function revealCats() {
	const triggerBottom = window.innerHeight * 0.85;
	cats.forEach(cat => {
		const catTop = cat.getBoundingClientRect().top;
		if (catTop < triggerBottom) cat.classList.add('show');
	});
}
window.addEventListener('scroll', revealCats);
window.addEventListener('load', revealCats);

document.addEventListener('DOMContentLoaded', () => {
	console.log("Frontend connected!");

	const modal = document.getElementById('auth-modal');
	const btnLogin = document.querySelector('button.btn-ghost');
	const btnRegister = document.querySelector('header .btn');
	const closeBtn = document.querySelector('.modal .close');
	const tabs = document.querySelectorAll('.tab-btn');
	const contents = document.querySelectorAll('.tab-content');

	if (btnLogin && btnRegister && modal) {
		btnLogin.addEventListener('click', () => {
			modal.style.display = 'block';
			showTab('login');
		});
		btnRegister.addEventListener('click', () => {
			modal.style.display = 'block';
			showTab('register');
		});
	}

	if (closeBtn) {
		closeBtn.addEventListener('click', () => modal.style.display = 'none');
		window.addEventListener('click', e => {
			if (e.target === modal) modal.style.display = 'none';
		});
	}

	tabs.forEach(tab => {
		tab.addEventListener('click', () => showTab(tab.dataset.tab));
	});

	function showTab(tabId) {
		tabs.forEach(t => t.classList.remove('active'));
		document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
		contents.forEach(c => c.style.display = 'none');
		document.getElementById(tabId).style.display = 'block';
	}

	const registerBtn = document.querySelector('#register .btn');
	if (registerBtn) {
		registerBtn.addEventListener('click', async () => {
			const name = document.querySelector('#register input[type=text]').value.trim();
			const email = document.querySelector('#register input[type=email]').value.trim();
			const password = document.querySelector('#register input[type=password]').value.trim();

			if (!name || !email || !password) return alert('Please complete all fields!');

			try {
				const res = await fetch('/api/register', {
					method: 'POST',
					headers: {'Content-Type': 'application/json'},
					credentials: 'include',
					body: JSON.stringify({name, email, password})
				});
				const data = await res.json();
				alert(data.message);
				if (data.success) {
					document.querySelector('#register input[type=text]').value = '';
					document.querySelector('#register input[type=email]').value = '';
					document.querySelector('#register input[type=password]').value = '';
					showTab('login');
				}
			} catch (err) {
				alert('Error connecting to the server.');
				console.error(err);
			}
		});
	}

	const loginBtn = document.querySelector('#login-btn');
	if (loginBtn) {
		loginBtn.addEventListener('click', async () => {
			const email = document.querySelector('#login-email').value.trim();
			const password = document.querySelector('#login-password').value.trim();

			if (!email || !password) return alert('Bitte E-Mail und Passwort eingeben.');

			try {
				const res = await fetch('/api/login', {
					method: 'POST',
					headers: {'Content-Type': 'application/json'},
					credentials: 'include',
					body: JSON.stringify({email, password})
				});
				const data = await res.json();

				if (data.success) {
					alert(data.message);
					window.location.href = '/dashboard.html';
				} else {
					alert(data.message);
				}
			} catch (err) {
				alert('Error connecting to the server.');
				console.error(err);
			}
		});
	}

	const teacherLoginBtn = document.querySelector('#teacher-login-btn');
	if (teacherLoginBtn) {
		teacherLoginBtn.addEventListener('click', async () => {
			const email = document.querySelector('#login-email').value.trim();
			const password = document.querySelector('#login-password').value.trim();

			if (!email || !password) return alert('Bitte E-Mail und Passwort eingeben.');

			try {
				const res = await fetch('/api/teacher-login', {
					method: 'POST',
					headers: {'Content-Type': 'application/json'},
					credentials: 'include',
					body: JSON.stringify({email, password})
				});
				const data = await res.json();

				if (data.success) {
					alert(data.message);
					window.location.href = '/teacher-admin.html';
				} else {
					alert(data.message);
				}
			} catch (err) {
				alert('Error connecting to the server.');
				console.error(err);
			}
		});
	}

	checkAuth();
});

document.querySelectorAll('.faq .item').forEach(item => {
	const q = item.querySelector('.q');
	const a = item.querySelector('.a');
	a.style.display = 'none';

	q.addEventListener('click', () => {
		const isOpen = a.style.display === 'block';
		document.querySelectorAll('.faq .a').forEach(x => x.style.display = 'none');
		document.querySelectorAll('.faq .toggle').forEach(t => t.textContent = '+');
		if (!isOpen) {
			a.style.display = 'block';
			const toggle = q.querySelector('.toggle');
			if (toggle) toggle.textContent = '−';
		}
	});
});

async function checkAuth() {
	try {
		const res = await fetch('/api/check-auth', {
			credentials: 'include'
		});
		const data = await res.json();

		if (data.authenticated) {
			console.log('User authorised:', data.user);
			updateHeaderForAuthUser(data.user);
		}
	} catch (err) {
		console.error('Authorisation verification error:', err);
	}
}

document.addEventListener('DOMContentLoaded', () => {
    const forgotLink = document.getElementById('forgot-password-link');
    const resetTabBtn = document.querySelector('.tab-btn[data-tab="reset"]');
    const requestResetBtn = document.getElementById('request-reset-btn');
    const resetPasswordBtn = document.getElementById('reset-password-btn');
    const newPasswordSection = document.getElementById('new-password-section');

    if (forgotLink) {
        forgotLink.addEventListener('click', (e) => {
            e.preventDefault();
            showTab('reset');
        });
    }

    if (requestResetBtn) {
        requestResetBtn.addEventListener('click', async () => {
            const email = document.getElementById('reset-email').value.trim();
            if (!email) return alert('Bitte E-Mail eingeben');

            try {
                const res = await fetch('/api/request-password-reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email})
                });
                const data = await res.json();
                alert(data.message);
                if (data.success) {
                    newPasswordSection.style.display = 'block';
                }
            } catch (err) {
                console.error(err);
                alert('Fehler beim Senden der E-Mail');
            }
        });
    }

    if (resetPasswordBtn) {
        resetPasswordBtn.addEventListener('click', async () => {
            const email = document.getElementById('reset-email').value.trim();
            const password = document.getElementById('new-password').value.trim();
            if (!email || !password) return alert('E-Mail und neues Passwort eingeben');

            try {
                const tokenRes = await fetch('/api/request-password-reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email})
                });
                const tokenData = await tokenRes.json();
                if (!tokenData.success) return alert(tokenData.message);

                const token = prompt('Bitte gib den Token aus der E-Mail ein');

                if (!token) return alert('Token erforderlich');

                const res = await fetch('/api/reset-password', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token, password})
                });
                const data = await res.json();
                alert(data.message);
                if (data.success) {
                    showTab('login');
                }
            } catch (err) {
                console.error(err);
                alert('Fehler beim Zurücksetzen des Passworts');
            }
        });
    }
});

function updateHeaderForAuthUser(user) {
	const nav = document.querySelector('nav .nav-links');
	if (nav) {
		const btnLogin = document.querySelector('button.btn-ghost');
		const btnRegister = document.querySelector('header .btn');

		if (btnLogin) btnLogin.textContent = user.name;
		if (btnRegister) {
			btnRegister.textContent = 'LogOut';
			btnRegister.onclick = async () => {
				try {
					const res = await fetch('/api/logout', {
						method: 'POST',
						credentials: 'include'
					});
					const data = await res.json();
					alert(data.message);
					window.location.reload();
				} catch (err) {
					console.error(err);
				}
			};
		}
	}
}
