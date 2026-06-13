import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// API base URLs
const AUTH_URL = '/api/auth';
const NOTES_URL = '/api/notes';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState('');

  // Fetch notes whenever the token changes (i.e., user logs in)
  useEffect(() => {
    if (token) {
      fetchNotes();
    }
  }, [token]);

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      alert('Username and password are required.');
      return;
    }
    try {
      await axios.post(`${AUTH_URL}/register`, { username, password });
      alert('Registered successfully! You can now log in.');
    } catch (err) {
      alert('Registration failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      alert('Username and password are required.');
      return;
    }
    try {
      const res = await axios.post(`${AUTH_URL}/login`, { username, password });
      const jwt = res.data.access_token;
      setToken(jwt);
      localStorage.setItem('token', jwt);
    } catch (err) {
      alert('Login failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleLogout = () => {
    setToken('');
    setNotes([]);
    localStorage.removeItem('token');
  };

  const fetchNotes = async () => {
    try {
      const res = await axios.get(`${NOTES_URL}/notes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotes(res.data);
    } catch (err) {
      if (err.response?.status === 401) handleLogout(); // Token expired
    }
  };

  const handleCreateNote = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${NOTES_URL}/notes`, { content: newNote }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewNote('');
      fetchNotes(); // Refresh the list
    } catch (err) {
      alert('Failed to create note.');
    }
  };

  // --- UI: Not Logged In ---
  if (!token) {
    return (
      <main className="page page-auth">
        <section className="auth-hero">
          <p className="eyebrow">Micro Notes</p>
          <h1 className="auth-title">Capture ideas before they disappear.</h1>
          <p className="auth-subtitle">
            A fast, focused workspace for your notes, protected by simple JWT auth.
          </p>
        </section>

        <section className="auth-panel" aria-label="Authentication form">
          <h2 className="panel-title">Sign in or create account</h2>
          <form className="auth-form">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="auth-input"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="auth-input"
            />
            <div className="auth-actions">
              <button type="button" onClick={handleLogin} className="auth-button auth-button-primary">
                Login
              </button>
              <button type="button" onClick={handleRegister} className="auth-button auth-button-secondary">
                Register
              </button>
            </div>
          </form>
        </section>
      </main>
    );
  }

  // --- UI: Logged In ---
  return (
    <main className="page page-notes">
      <section className="notes-shell">
        <header className="header">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h2>Your Notes</h2>
          </div>
          <button onClick={handleLogout} className="auth-button auth-button-secondary">Logout</button>
        </header>

        <form onSubmit={handleCreateNote} className="note-form">
          <input
            type="text"
            placeholder="Write a new note..."
            value={newNote}
            onChange={e => setNewNote(e.target.value)}
            className="note-input"
          />
          <button type="submit" className="auth-button auth-button-primary">Add Note</button>
        </form>

        <ul className="notes-list" aria-live="polite">
          {notes.length === 0 && <p className="empty">No notes yet. Add one above.</p>}
          {notes.map(note => (
            <li key={note.id} className="note-item">
              <span className="note-owner">{note.owner}</span>
              <p className="note-content">{note.content}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

export default App;