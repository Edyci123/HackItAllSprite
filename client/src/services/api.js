const BASE_URL = 'http://localhost:8000';

export const api = {
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
        const response = await fetch(`${BASE_URL}/search/${jobId}`);
        if (!response.ok) throw new Error('Polling failed');
        return response.json();
    },
};
