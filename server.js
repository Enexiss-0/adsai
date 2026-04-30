const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 3000;
const USERS_FILE = path.join(__dirname, 'users.json');
const JWT_SECRET = process.env.JWT_SECRET || 'adsai-secret-token';
const TOKEN_LIFETIME = '5h';

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

function readUsers() {
  try {
    const raw = fs.readFileSync(USERS_FILE, 'utf-8');
    return JSON.parse(raw || '[]');
  } catch (error) {
    return [];
  }
}

function writeUsers(users) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2), 'utf-8');
}

function generateToken(user) {
  return jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: TOKEN_LIFETIME });
}

function authenticateToken(req, res, next) {
  const authHeader = req.headers.authorization || '';
  const token = authHeader.replace('Bearer ', '');
  if (!token) {
    return res.status(401).json({ message: 'Token ausente' });
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.user = payload;
    next();
  } catch (error) {
    return res.status(401).json({ message: 'Token inválido' });
  }
}

app.post('/api/register', (req, res) => {
  const { name, email, password } = req.body;
  if (!name || !email || !password) {
    return res.status(400).json({ message: 'Nome, email e senha são obrigatórios.' });
  }

  const users = readUsers();
  const existing = users.find(user => user.email === email.toLowerCase());
  if (existing) {
    return res.status(409).json({ message: 'Já existe uma conta com esse email.' });
  }

  const hashedPassword = bcrypt.hashSync(password, 10);
  const user = {
    id: Date.now().toString(),
    name,
    email: email.toLowerCase(),
    password: hashedPassword,
    createdAt: new Date().toISOString()
  };

  users.push(user);
  writeUsers(users);

  const token = generateToken(user);
  res.status(201).json({ user: { id: user.id, name: user.name, email: user.email }, token });
});

app.post('/api/login', (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ message: 'Email e senha são obrigatórios.' });
  }

  const users = readUsers();
  const user = users.find(item => item.email === email.toLowerCase());
  if (!user || !bcrypt.compareSync(password, user.password)) {
    return res.status(401).json({ message: 'Email ou senha inválidos.' });
  }

  const token = generateToken(user);
  res.json({ user: { id: user.id, name: user.name, email: user.email }, token });
});

app.post('/api/generate', authenticateToken, (req, res) => {
  const { prompt, style } = req.body;
  if (!prompt || !style) {
    return res.status(400).json({ message: 'Prompt e estilo são obrigatórios.' });
  }

  const title = `${style} para ${prompt}`;
  const description = `Anúncio com foco em conversão: destaque a vantagem principal, use linguagem simples e convide o usuário a agir agora.`;
  const result = {
    title,
    description,
    prompt,
    style
  };

  res.json({ result });
});

app.get('/api/profile', authenticateToken, (req, res) => {
  const users = readUsers();
  const user = users.find(item => item.id === req.user.id);
  if (!user) {
    return res.status(404).json({ message: 'Usuário não encontrado.' });
  }
  res.json({ user: { id: user.id, name: user.name, email: user.email } });
});

app.use((req, res) => {
  res.status(404).send('Página não encontrada.');
});

app.listen(PORT, () => {
  console.log(`Servidor AdsAI rodando em http://localhost:${PORT}`);
});
