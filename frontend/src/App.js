import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationId, setGenerationId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('');
  const [error, setError] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [frameworks, setFrameworks] = useState([]);
  const [selectedFramework, setSelectedFramework] = useState('');
  const [history, setHistory] = useState([]);
  
  const wsRef = useRef(null);

  useEffect(() => {
    // Load frameworks and history on component mount
    loadFrameworks();
    loadHistory();
  }, []);

  useEffect(() => {
    // Setup WebSocket connection when generation starts
    if (generationId && isGenerating) {
      setupWebSocket(generationId);
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [generationId, isGenerating]);

  const loadFrameworks = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/frameworks`);
      const data = await response.json();
      setFrameworks(data.frameworks);
    } catch (err) {
      console.error('Failed to load frameworks:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/history?limit=5`);
      const data = await response.json();
      setHistory(data.generations);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const setupWebSocket = (genId) => {
    const wsUrl = `ws://localhost:8000/ws/${genId}`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'status_update') {
        setStatus(data.status);
        setProgress(data.progress);
        setCurrentStage(data.current_stage);
        if (data.error) {
          setError(data.error);
        }
      } else if (data.type === 'completed') {
        setIsGenerating(false);
        setProgress(100);
        setCurrentStage('Completed');
        setDownloadUrl(`${API_BASE_URL}/download/${genId}`);
        loadHistory(); // Refresh history
      } else if (data.type === 'ping') {
        // Keep-alive ping, no action needed
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error occurred');
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a description for your app');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setProgress(0);
    setCurrentStage('Initializing');
    setDownloadUrl(null);

    try {
      const requestBody = {
        prompt: prompt.trim(),
        user_preferences: selectedFramework ? { framework: selectedFramework } : null
      };

      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setGenerationId(data.generation_id);
      setStatus(data.status);
      
    } catch (err) {
      setError(`Failed to start generation: ${err.message}`);
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank');
    }
  };

  const handleTryExample = (examplePrompt) => {
    setPrompt(examplePrompt);
  };

  const examplePrompts = [
    "Create a simple calculator app with basic arithmetic operations",
    "Build a weather app that shows current conditions and 5-day forecast",
    "Make a todo list app where users can add, edit, and delete tasks",
    "Create a QR code scanner app with flashlight toggle",
    "Build a note-taking app with categories and search functionality"
  ];

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🚀 Project Singularity</h1>
          <p>Revolutionary Text-to-APK Engine</p>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          
          {/* Input Section */}
          <section className="input-section">
            <h2>Describe Your App</h2>
            <div className="input-group">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the app you want to create... (e.g., 'Create a simple calculator app with basic arithmetic operations')"
                rows={4}
                disabled={isGenerating}
                className="prompt-input"
              />
              
              <div className="preferences">
                <label htmlFor="framework-select">Preferred Framework (Optional):</label>
                <select
                  id="framework-select"
                  value={selectedFramework}
                  onChange={(e) => setSelectedFramework(e.target.value)}
                  disabled={isGenerating}
                  className="framework-select"
                >
                  <option value="">Auto-select (Recommended)</option>
                  {frameworks.map((framework) => (
                    <option key={framework.id} value={framework.id}>
                      {framework.name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
                className={`generate-btn ${isGenerating ? 'generating' : ''}`}
              >
                {isGenerating ? '🔄 Generating...' : '🚀 Generate APK'}
              </button>
            </div>
          </section>

          {/* Example Prompts */}
          <section className="examples-section">
            <h3>Try These Examples</h3>
            <div className="examples-grid">
              {examplePrompts.map((example, index) => (
                <button
                  key={index}
                  onClick={() => handleTryExample(example)}
                  disabled={isGenerating}
                  className="example-btn"
                >
                  {example}
                </button>
              ))}
            </div>
          </section>

          {/* Progress Section */}
          {isGenerating && (
            <section className="progress-section">
              <h3>Generation Progress</h3>
              <div className="progress-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <div className="progress-info">
                  <span className="progress-percentage">{progress}%</span>
                  <span className="progress-stage">{currentStage}</span>
                </div>
              </div>
              
              {generationId && (
                <div className="generation-details">
                  <p><strong>Generation ID:</strong> {generationId}</p>
                  <p><strong>Status:</strong> {status}</p>
                </div>
              )}
            </section>
          )}

          {/* Error Section */}
          {error && (
            <section className="error-section">
              <div className="error-message">
                <h3>❌ Error</h3>
                <p>{error}</p>
              </div>
            </section>
          )}

          {/* Download Section */}
          {downloadUrl && (
            <section className="download-section">
              <div className="success-message">
                <h3>✅ APK Generated Successfully!</h3>
                <p>Your Android application has been generated and is ready for download.</p>
                <button onClick={handleDownload} className="download-btn">
                  📱 Download APK
                </button>
              </div>
            </section>
          )}

          {/* History Section */}
          {history.length > 0 && (
            <section className="history-section">
              <h3>Recent Generations</h3>
              <div className="history-list">
                {history.map((gen) => (
                  <div key={gen.id} className="history-item">
                    <div className="history-info">
                      <h4>{gen.app_name || 'Generated App'}</h4>
                      <p>{gen.prompt.substring(0, 100)}...</p>
                      <span className="history-meta">
                        {gen.framework} • {new Date(gen.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="history-actions">
                      <span className={`status-badge ${gen.status}`}>
                        {gen.status}
                      </span>
                      {gen.status === 'completed' && (
                        <a 
                          href={`${API_BASE_URL}/download/${gen.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="download-link"
                        >
                          Download
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

        </div>
      </main>

      <footer className="App-footer">
        <div className="footer-content">
          <p>Project Singularity - Democratizing Mobile App Development</p>
          <p>Transform your ideas into reality with AI-powered development</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
