const loginTab = document.getElementById('loginTab');
const registerTab = document.getElementById('registerTab');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const authMessage = document.getElementById('authMessage');
const authSection = document.getElementById('authSection');
const appSection = document.getElementById('appSection');
const logoutBtn = document.getElementById('logoutBtn');
const userNameSpan = document.getElementById('userName');
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');
const switchToRegister = document.getElementById('switchToRegister');
const switchToLogin = document.getElementById('switchToLogin');
const adPrompt = document.getElementById('adPrompt');
const adStyle = document.getElementById('adStyle');
const generateAdBtn = document.getElementById('generateAdBtn');
const adResult = document.getElementById('adResult');

const API_BASE = '/api';
const SESSION_KEY = 'adsai_session';

function showMessage(text, type = 'error') {
  authMessage.textContent = text;
  authMessage.style.color = type === 'success' ? '#059669' : '#ec4899';
}

function switchTab(tab) {
  if (tab === 'login') {
    loginTab.classList.add('active');
    registerTab.classList.remove('active');
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
  } else {
    loginTab.classList.remove('active');
    registerTab.classList.add('active');
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
  }

  showMessage('');
}

function setSession(session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function getSession() {
  return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function getAuthHeaders() {
  const session = getSession();
  if (!session || !session.token) return { 'Content-Type': 'application/json' };
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${session.token}`
  };
}

function showApp(user) {
  authSection.classList.add('hidden');
  appSection.classList.remove('hidden');
  logoutBtn.classList.remove('hidden');
  userNameSpan.textContent = user.name;
}

function showAuth() {
  authSection.classList.remove('hidden');
  appSection.classList.add('hidden');
  logoutBtn.classList.add('hidden');
  switchTab('login');
}

async function postJson(url, body, auth = false) {
  const options = {
    method: 'POST',
    headers: auth ? getAuthHeaders() : { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  };
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Erro na requisição');
  }
  return data;
}

loginTab.addEventListener('click', () => switchTab('login'));
registerTab.addEventListener('click', () => switchTab('register'));
switchToRegister.addEventListener('click', () => switchTab('register'));
switchToLogin.addEventListener('click', () => switchTab('login'));

registerBtn.addEventListener('click', async () => {
  const name = document.getElementById('registerName').value.trim();
  const email = document.getElementById('registerEmail').value.trim().toLowerCase();
  const password = document.getElementById('registerPassword').value.trim();

  if (!name || !email || !password) {
    showMessage('Preencha todos os campos para se registrar.');
    return;
  }

  try {
    const data = await postJson(`${API_BASE}/register`, { name, email, password });
    setSession({ token: data.token, user: data.user });
    showMessage('Registro feito com sucesso!', 'success');
    showApp(data.user);
  } catch (error) {
    showMessage(error.message);
  }
});

loginBtn.addEventListener('click', async () => {
  const email = document.getElementById('loginEmail').value.trim().toLowerCase();
  const password = document.getElementById('loginPassword').value.trim();

  if (!email || !password) {
    showMessage('Preencha email e senha para entrar.');
    return;
  }

  try {
    const data = await postJson(`${API_BASE}/login`, { email, password });
    setSession({ token: data.token, user: data.user });
    showMessage('Login realizado com sucesso!', 'success');
    showApp(data.user);
  } catch (error) {
    showMessage(error.message);
  }
});

logoutBtn.addEventListener('click', () => {
  clearSession();
  showAuth();
  adResult.textContent = 'Seu anúncio aparecerá aqui.';
  adPrompt.value = '';
});

generateAdBtn.addEventListener('click', async () => {
  const prompt = adPrompt.value.trim();
  const style = adStyle.value;

  if (!prompt) {
    adResult.textContent = 'Digite sua ideia de anúncio para gerar o resultado.';
    return;
  }

  try {
    const data = await postJson(`${API_BASE}/generate`, { prompt, style }, true);
    adResult.innerHTML = `
      <div>
        <p class="eyebrow">Anúncio gerado</p>
        <h3>${data.result.title}</h3>
        <p>${data.result.description}</p>
      </div>
    `;
  } catch (error) {
    adResult.textContent = error.message;
  }
});

(async () => {
  const session = getSession();
  if (session && session.token && session.user) {
    try {
      const res = await fetch(`${API_BASE}/profile`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      showApp(data.user);
      return;
    } catch (error) {
      clearSession();
    }
  }
  showAuth();
})();
