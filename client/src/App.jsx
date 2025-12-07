import { useState, useRef, useEffect } from 'react'
import { api } from './services/api'
import './App.css'

function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [refinementQuery, setRefinementQuery] = useState('')
  const [suggestedCompany, setSuggestedCompany] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState([])
  const [pollingMessage, setPollingMessage] = useState('Initializing search...')
  const [currentStep, setCurrentStep] = useState('initializing')
  const [progressPercent, setProgressPercent] = useState(0)
  const [totalProducts, setTotalProducts] = useState(0)
  const [scoredCount, setScoredCount] = useState(0)
  const [partialResults, setPartialResults] = useState([])
  const [searchHistory, setSearchHistory] = useState([]) // Track search history for refinements
  const [displayQuery, setDisplayQuery] = useState('') // The query to show in textarea during loading
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' }) // Toast notification
  const pollingRef = useRef(null)

  // Show toast notification
  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type })
    setTimeout(() => setToast({ show: false, message: '', type: 'success' }), 4000)
  }

  // Product popup handler
  const handleProductClick = (product, event) => {
    event.preventDefault()

    // Calculate popup size and position (centered, modal-like)
    const width = Math.min(1200, window.innerWidth * 0.9)
    const height = Math.min(800, window.innerHeight * 0.9)
    const left = (window.innerWidth - width) / 2 + window.screenX
    const top = (window.innerHeight - height) / 2 + window.screenY

    // Open the product URL in a styled popup window
    window.open(
      product.link,
      'productPreview',
      `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,location=yes,status=no,scrollbars=yes,resizable=yes`
    )
  }

  const handleSearch = async (isRefinement = false) => {
    const queryToUse = isRefinement
      ? `${searchQuery}\n\n--- REFINARE ---\n${refinementQuery}`
      : searchQuery

    if (!queryToUse.trim()) return

    // Track search history
    if (isRefinement) {
      setSearchHistory(prev => [...prev, { type: 'refinement', query: refinementQuery }])
      setSearchQuery(queryToUse) // Update main query with combined query
      setRefinementQuery('') // Clear refinement input
    } else {
      setSearchHistory([{ type: 'initial', query: searchQuery }])
    }

    // Set the display query BEFORE loading starts so it's visible during loading
    setDisplayQuery(queryToUse)
    setIsSearching(true)
    setIsLoading(true)
    setResults([])
    setPartialResults([])
    setPollingMessage('Initializing search...')
    setCurrentStep('initializing')
    setProgressPercent(0)
    setTotalProducts(0)
    setScoredCount(0)

    try {
      const { task_id } = await api.startSearch(queryToUse)
      const jobId = task_id

      pollingRef.current = setInterval(async () => {
        try {
          const status = await api.pollSearch(jobId)

          // Update real status from backend
          setPollingMessage(status.step_message || 'Processing...')
          setCurrentStep(status.current_step || 'running')
          setProgressPercent(status.progress_percent || 0)
          setTotalProducts(status.total_products || 0)
          setScoredCount(status.scored_count || 0)

          // Display partial results as they stream in
          if (status.partial_results && status.partial_results.length > 0) {
            setPartialResults(status.partial_results)
          }

          if (status.status === 'completed') {
            clearInterval(pollingRef.current)
            setResults(status.result || [])
            setPartialResults([])
            setIsLoading(false)
          } else if (status.status === 'failed') {
            clearInterval(pollingRef.current)
            setIsLoading(false)
            setPollingMessage(status.step_message || 'Search failed')
          }
        } catch (err) {
          console.error('Polling error:', err)
          clearInterval(pollingRef.current)
          setIsLoading(false)
          setPollingMessage('Error occurred during search')
        }
      }, 800) // Poll slightly faster for smoother updates

    } catch (err) {
      console.error('Search start error:', err)
      setIsLoading(false)
      setPollingMessage('Failed to start search')
    }
  }

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      // If we have results, this is a refinement; otherwise it's a new search
      const hasResults = results.length > 0 && !isLoading
      handleSearch(hasResults)
    }
  }

  // Reset everything for a new search
  const handleNewSearch = () => {
    setSearchQuery('')
    setRefinementQuery('')
    setSuggestedCompany('')
    setIsSearching(false)
    setIsLoading(false)
    setResults([])
    setPartialResults([])
    setSearchHistory([])
    setPollingMessage('Initializing search...')
    setCurrentStep('initializing')
    setProgressPercent(0)
    setTotalProducts(0)
    setScoredCount(0)
  }

  const handleHintClick = (hint) => {
    setSearchQuery(hint)
  }

  const searchHints = [
    'wireless headphones',
    'running shoes',
    'coffee maker',
    'laptop stand'
  ]

  // Get display products - either partial results during loading, or final results
  const displayProducts = isLoading ? partialResults : results

  // Calculate step indicator based on current_step
  const getStepIndex = () => {
    switch (currentStep) {
      case 'initializing': return 0
      case 'transforming': return 0
      case 'scraping': return 1
      case 'ranking': return 2
      case 'completed': return 3
      default: return 0
    }
  }

  const stepIndex = getStepIndex()

  return (
    <div className={`app-container ${isSearching ? 'searching' : ''}`}>
      {/* Toast Notification */}
      {toast.show && (
        <div className={`toast-notification ${toast.type}`}>
          <span>{toast.message}</span>
          <button className="toast-close" onClick={() => setToast({ ...toast, show: false })}>×</button>
        </div>
      )}

      {/* Floating Orbs Background */}
      <div className="floating-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <div className="content-wrapper">
        <header className="app-header">
          <h1 className="app-title">
            Local<span className="title-accent">Hunt</span>
          </h1>

          {!isSearching && (
            <>
              <p className="tagline">
                Discover products from trusted local businesses
              </p>

              <div className="feature-pills">
                <div className="feature-pill">
                  <svg className="feature-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    <polyline points="9 22 9 12 15 12 15 22"></polyline>
                  </svg>
                  Support Local
                </div>
                <div className="feature-pill">
                  <svg className="feature-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  Verified Sellers
                </div>
              </div>
            </>
          )}

          <span className="mission-pill">
            Agentic Commerce for Local Communities
          </span>
        </header>

        <div className="search-section">
          {/* Show "New Search" button when we have results */}
          {isSearching && !isLoading && results.length > 0 && (
            <button className="new-search-button" onClick={handleNewSearch}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                <path d="M3 3v5h5"></path>
              </svg>
              New Search
            </button>
          )}

          <div className={`search-bar-wrapper ${isLoading ? 'disabled' : ''} ${isSearching && !isLoading && results.length > 0 ? 'refine-mode' : ''}`}>
            <textarea
              className="search-textarea"
              placeholder={isSearching && !isLoading && results.length > 0
                ? "Refine your search... (e.g., 'cheaper options', 'prefer smaller shops')"
                : "What are you looking for today?"}
              value={
                isLoading
                  ? displayQuery // During loading, show the query being searched (including refinements)
                  : (isSearching && results.length > 0 ? refinementQuery : searchQuery)
              }
              onChange={(e) => {
                if (isSearching && !isLoading && results.length > 0) {
                  setRefinementQuery(e.target.value)
                } else {
                  setSearchQuery(e.target.value)
                }
              }}
              onKeyDown={handleKeyDown}
              rows={2}
              disabled={isLoading}
            />
            <button
              className={`search-button ${isSearching && !isLoading && results.length > 0 ? 'refine-button-mode' : ''}`}
              onClick={() => {
                const hasResults = results.length > 0 && !isLoading && isSearching
                handleSearch(hasResults)
              }}
              aria-label={isSearching && !isLoading && results.length > 0 ? "Refine" : "Search"}
              disabled={isLoading || (isSearching && !isLoading && results.length > 0 && !refinementQuery.trim())}
            >
              {isSearching && !isLoading && results.length > 0 ? (
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13"></path>
                  <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                </svg>
              ) : (
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </button>
          </div>

          {/* Refinement mode hint */}
          {isSearching && !isLoading && results.length > 0 && (
            <span className="refine-mode-hint">Type to refine results, or click "New Search" to start fresh</span>
          )}

          {/* Company Suggestion Input - only on initial search */}
          {!isSearching && (
            <div className="company-suggestion-wrapper">
              <div className="company-suggestion-input-row">
                <input
                  type="text"
                  className="company-suggestion-input"
                  placeholder="Suggest a local shop (e.g., shop URL or name)"
                  value={suggestedCompany}
                  onChange={(e) => setSuggestedCompany(e.target.value)}
                />
                <button
                  className="suggest-shop-button"
                  onClick={() => {
                    if (suggestedCompany.trim()) {
                      showToast(`✅ Thank you! "${suggestedCompany}" has been added to our local shops registry.`, 'success')
                      setSuggestedCompany('')
                    } else {
                      showToast('Please enter a shop name or URL first.', 'error')
                    }
                  }}
                >
                  Suggest
                </button>
              </div>
              <span className="company-suggestion-hint">💡 Know a local shop with bad SEO? Add it to help everyone discover it!</span>
            </div>
          )}

          {!isSearching && (
            <div className="search-hints">
              {searchHints.map((hint, i) => (
                <span
                  key={i}
                  className="hint-chip"
                  onClick={() => handleHintClick(hint)}
                >
                  {hint}
                </span>
              ))}
            </div>
          )}
        </div>

        {isSearching && (
          <div className="results-section">
            {/* Show products - either streaming partial results or final results */}
            {displayProducts.length > 0 && (
              <>
                <div className="results-header">
                  <div className="results-count">
                    {isLoading
                      ? <><strong>{displayProducts.length}</strong> products analyzed so far...</>
                      : <>Found <strong>{displayProducts.length}</strong> products from trusted local sellers</>
                    }
                  </div>
                </div>
                <div className="results-list">
                  {displayProducts.map((result, index) => {
                    const scores = result.scores || {}

                    return (
                      <div
                        key={`${result.name}-${index}`}
                        className={`result-card ${isLoading ? 'streaming' : ''}`}
                        style={{ animationDelay: `${index * 0.05}s` }}
                        onClick={(e) => handleProductClick(result, e)}
                      >
                        <div className="result-image-wrapper">
                          {result.image ? (
                            <img src={result.image} alt={result.name} className="result-image" />
                          ) : (
                            <div className="no-image-placeholder">
                              <span>📦</span>
                              <p>No image</p>
                            </div>
                          )}
                        </div>

                        <div className="result-content">
                          <div className="result-header">
                            <h3>{result.name}</h3>
                          </div>

                          <div className="result-meta">
                            <span className="price-tag">{result.price}</span>
                            <span className="firm-badge">{result.firm}</span>
                          </div>

                          {result.description && (
                            <p className="description-text">{result.description}</p>
                          )}
                        </div>

                        {scores.reasoning && (
                          <div className="agent-insight">
                            <div className="insight-header">
                              <div className="pulse-dot"></div>
                              <span className="insight-title">AI Insight</span>
                            </div>
                            <p className="insight-text">{scores.reasoning}</p>
                          </div>
                        )}

                        <div className="card-view-indicator">
                          <span>Click to view</span>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                          </svg>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}

            {/* Loading indicator - shown below products during loading */}
            {isLoading && (
              <div className="loading-below-products">
                <div className="loading-spinner-small"></div>
                <div className="loading-info">
                  <div className="loading-text-small">{pollingMessage}</div>
                  <div className="loading-subtext-small">
                    {currentStep === 'ranking' && totalProducts > 0
                      ? `Analyzing ${scoredCount} of ${totalProducts} products`
                      : 'Finding more products for you...'
                    }
                  </div>
                </div>
                <div className="progress-steps-horizontal">
                  <div className={`step-dot ${stepIndex >= 0 ? 'active' : ''} ${stepIndex > 0 ? 'complete' : ''}`} title="Search"></div>
                  <div className={`step-dot ${stepIndex >= 1 ? 'active' : ''} ${stepIndex > 1 ? 'complete' : ''}`} title="Scrape"></div>
                  <div className={`step-dot ${stepIndex >= 2 ? 'active' : ''} ${stepIndex > 2 ? 'complete' : ''}`} title="Rank"></div>
                  <div className={`step-dot ${stepIndex >= 3 ? 'active' : ''}`} title="Done"></div>
                </div>
              </div>
            )}

          </div>
        )}

        {!isSearching && (
          <footer className="app-footer">
            <div className="footer-content">
              <div className="footer-brand">
                Local<span>Hunt</span>
              </div>
              <p className="footer-mission">
                Empowering local businesses and communities through intelligent product discovery.
              </p>
            </div>
          </footer>
        )}
      </div>
    </div>
  )
}

export default App
