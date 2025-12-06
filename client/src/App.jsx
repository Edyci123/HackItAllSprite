import { useState, useEffect, useRef } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import { api } from './services/api'
import './App.css'

function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState([])
  const [pollingMessage, setPollingMessage] = useState('Initializing search...')
  const pollingRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    const user = localStorage.getItem('user')
    if (!user) {
      navigate('/login')
    }
  }, [navigate])

  const handleLogout = () => {
    localStorage.removeItem('user')
    navigate('/login')
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setIsLoading(true)
    setResults([])
    setPollingMessage('Starting search...')

    try {
      const { jobId } = await api.startSearch(searchQuery)

      pollingRef.current = setInterval(async () => {
        try {
          const status = await api.pollSearch(jobId)

          if (status.completed) {
            clearInterval(pollingRef.current)
            setResults(status.results || [])
            setIsLoading(false)
          } else {
            setPollingMessage(status.message || 'Processing...')
          }
        } catch (err) {
          console.error('Polling error:', err)
          clearInterval(pollingRef.current)
          setIsLoading(false)
          setPollingMessage('Error occurred during search')
        }
      }, 1000) // Poll every 1 second

    } catch (err) {
      console.error('Search start error:', err)
      setIsLoading(false)
      setPollingMessage('Failed to start search')
    }
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className={`app-container ${isSearching ? 'searching' : ''}`}>
      <button className="logout-button" onClick={handleLogout}>
        Logout
      </button>
      <div className="content-wrapper">
        <header className="app-header">
          <h1 className="app-title">HackItALL</h1>
          <p className="app-description">
            Discover the future of hacking. Search for resources, tools, and documentation.
          </p>
        </header>

        <div className="search-section">
          <div className="search-bar-wrapper">
            <textarea
              className="search-textarea"
              placeholder="What are you looking for?"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button className="search-button" onClick={handleSearch} aria-label="Search">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 19V5M12 5L5 12M12 5L19 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>

        {isSearching && (
          <div className="results-section">
            {isLoading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p className="polling-message">{pollingMessage}</p>
              </div>
            ) : (
              <div className="results-list">
                {results.map((result) => (
                  <a key={result.id} href={result.url} target="_blank" rel="noreferrer" className="result-card">
                    <h3>{result.title}</h3>
                    <p>{result.description}</p>
                    <span className="result-url">{result.url}</span>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
    </Routes>
  )
}

export default App
