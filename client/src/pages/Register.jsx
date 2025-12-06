import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import '../App.css';

function Register() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await api.register(username, password);
            navigate('/login');
        } catch (err) {
            setError('Registration failed');
        }
    };

    return (
        <div className="app-container" style={{ paddingTop: '20vh' }}>
            <div className="content-wrapper">
                <h1 className="app-title" style={{ fontSize: '4rem', marginBottom: '1rem' }}>HackItALL</h1>
                <h2 className="app-description" style={{ fontSize: '2rem', marginBottom: '2rem', color: 'white' }}>Register</h2>
                <form onSubmit={handleSubmit} className="search-bar-wrapper" style={{ flexDirection: 'column', borderRadius: '24px', width: '100%', maxWidth: '400px', padding: '2rem' }}>
                    <input
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="search-textarea"
                        style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '1rem' }}
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="search-textarea"
                        style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '2rem' }}
                    />
                    {error && <p style={{ color: '#ff4444', marginBottom: '1rem' }}>{error}</p>}
                    <button type="submit" className="search-button" style={{ width: '100%', borderRadius: '12px', height: 'auto', padding: '1rem' }}>
                        Register
                    </button>
                    <p style={{ marginTop: '1rem', color: 'rgba(255,255,255,0.6)' }}>
                        Already have an account? <Link to="/login" style={{ color: 'var(--primary-color)' }}>Login</Link>
                    </p>
                </form>
            </div>
        </div>
    );
}

export default Register;
