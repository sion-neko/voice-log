import { useState, useRef, useEffect } from 'react';
import './App.css';

const formatTime = (seconds: number) => {
  const pad = (num: number) => num.toString().padStart(2, '0');
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${pad(m)}:${pad(s)}`;
  return `${m}:${pad(s)}`;
};

const formatDate = (dateString: string) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    }).format(date);
  } catch {
    return dateString;
  }
};

const animalEmojis = ['🦊', '🐰', '🐻', '🐼', '🐯', '🦁', '🐨', '🐮', '🐷', '🐸', '🐹', '🐭', '🐱', '🐶', '🐒', '🐧', '🦉', '🐢'];
const speakerColors = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#10b981', // green
  '#06b6d4', // cyan
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#d946ef', // fuchsia
  '#f43f5e', // rose
];

const getSpeakerStyle = (speakerStr: string) => {
  const safeStr = speakerStr || "Unknown";
  let hash = 0;
  for (let i = 0; i < safeStr.length; i++) {
    hash = safeStr.charCodeAt(i) + ((hash << 5) - hash);
  }
  hash = Math.abs(hash);
  return {
    emoji: animalEmojis[hash % animalEmojis.length],
    color: speakerColors[hash % speakerColors.length]
  };
};

const CustomAudioPlayer = ({ src, audioRef }: { src: string, audioRef: React.RefObject<HTMLAudioElement | null> }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const onTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const onLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const onSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = Number(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  useEffect(() => {
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    
    const audioEl = audioRef.current;
    if (audioEl) {
      audioEl.addEventListener('play', handlePlay);
      audioEl.addEventListener('pause', handlePause);
      return () => {
        audioEl.removeEventListener('play', handlePlay);
        audioEl.removeEventListener('pause', handlePause);
      };
    }
  }, [audioRef]);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="custom-player-wrapper">
      <audio 
        ref={audioRef} 
        src={src} 
        onTimeUpdate={onTimeUpdate} 
        onLoadedMetadata={onLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
      <button className="player-play-btn" onClick={togglePlayPause} aria-label={isPlaying ? "一時停止" : "再生"}>
        {isPlaying ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 4h4v16H6zm8 0h4v16h-4z"/>
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: '4px' }}>
            <path d="M8 5v14l11-7z"/>
          </svg>
        )}
      </button>
      <div className="player-time-display">{formatTime(currentTime)}</div>
      <input 
        type="range" 
        className="player-seek-bar" 
        min={0} 
        max={duration || 0} 
        step={0.1}
        value={currentTime} 
        onChange={onSeek} 
        aria-label="シークバー"
        style={{ background: `linear-gradient(to right, var(--accent-color) ${progress}%, #e2e8f0 ${progress}%)` }}
      />
      <div className="player-time-display">{formatTime(duration)}</div>
    </div>
  );
};

function App() {
  const [data, setData] = useState<{ created_at: string; segments: { start: number; end: number; speaker: string; text: string }[] } | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setAudioUrl(null);
    }
  }, [file]);

  const playAudioAt = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      audioRef.current.play().catch(e => console.error("Audio play failed", e));
    }
  };

  const onChangeFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setFile(files[0]);
      setData(null);
    }
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      setFile(files[0]);
      setData(null);
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setData(null);
  };

  const onClickSubmit = async () => {
    if (!file) return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("http://localhost:8000/summarize", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      setData(json);
    } catch (error) {
      console.error(error);
      setData({ created_at: "", segments: [] });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <div className="header-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" x2="12" y1="19" y2="22" />
            <line x1="8" x2="16" y1="22" y2="22" />
          </svg>
        </div>
        <h1>AI Speech Summarizer</h1>
        <p>音声をアップロードして、AIで瞬時に要約を作成します</p>
      </div>

      <div className="main-card">
        {!file ? (
          <div 
            className={`upload-area ${isDragging ? "active" : ""}`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
          >
            <input 
              ref={fileInputRef}
              name="file" 
              type="file" 
              accept="audio/*" 
              onChange={onChangeFile} 
            />
            <svg className="upload-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
              <path d="M12 12v9" />
              <path d="m16 16-4-4-4 4" />
            </svg>
            <div className="upload-text">クリックまたはドラッグ＆ドロップでアップロード</div>
            <div className="upload-subtext">WAV, MP3, M4A などのフォーマットに対応</div>
          </div>
        ) : (
          <div className="file-info">
            <div className="file-name">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
              {file.name}
            </div>
            <button className="remove-btn" onClick={removeFile} aria-label="ファイルを削除" title="削除">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>
        )}

        <button 
          className="submit-btn" 
          disabled={!file || isLoading} 
          onClick={onClickSubmit}
        >
          {isLoading ? (
            <>
              <svg className="spinner" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              要約中...
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v20" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
              音声を要約する
            </>
          )}
        </button>
      </div>

      {data && (
        <div className="result-section">
          <div className="result-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" x2="8" y1="13" y2="13" />
              <line x1="16" x2="8" y1="17" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            <h2>要約結果</h2>
          </div>
          <div className="result-content">
            {data.created_at && (
              <div className="result-meta">
                <span className="result-date">作成日時: {formatDate(data.created_at)}</span>
              </div>
            )}
            
            {audioUrl && (
              <div className="audio-player-container">
                <CustomAudioPlayer src={audioUrl} audioRef={audioRef} />
              </div>
            )}

            <div className="chat-container">
              {data.segments.map((segment: any, index: number) => {
                const speakerName = segment.speaker || "話者";
                const { emoji, color } = getSpeakerStyle(speakerName);
                return (
                  <div key={`${segment.start}-${index}`} className="chat-message">
                    <div className="chat-avatar" style={{ backgroundColor: `${color}33`, border: `2px solid ${color}` }}>
                      {emoji}
                    </div>
                    <div className="chat-content">
                      <div className="chat-header">
                        <span className="chat-speaker" style={{ color: color }}>
                          {speakerName}
                        </span>
                        <button 
                          className="chat-time chat-time-link"
                          onClick={() => playAudioAt(segment.start)}
                          title="クリックしてこの時間から再生"
                          aria-label={`${formatTime(segment.start)}から再生`}
                        >
                          ▶ {formatTime(segment.start)}
                        </button>
                      </div>
                      <div className="chat-bubble">
                        <div className="chat-text">{segment.text}</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
