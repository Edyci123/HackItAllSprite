const BASE_URL = 'http://localhost:8000';

export const api = {
    login: async (username, password) => {
        const response = await fetch(`${BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        if (!response.ok) throw new Error('Login failed');
        return response.json();
    },

    register: async (username, password) => {
        const response = await fetch(`${BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        if (!response.ok) throw new Error('Registration failed');
        return response.json();
    },

    startSearch: async (query) => {
        const response = await fetch(`${BASE_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });
        if (!response.ok) throw new Error('Search failed');
        return response.json();
    },

    pollSearch: async (jobId) => {
        const response = await fetch(`${BASE_URL}/search/poll/${jobId}`);
        if (!response.ok) throw new Error('Polling failed');
        return response.json();
    },
};
