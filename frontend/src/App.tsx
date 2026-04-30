import { useState, useRef, useEffect } from 'react';
import './App.css';

const API_BASE = `http://${window.location.hostname}:8000`;

const formatTime = (seconds: number) => {
  const pad = (num: number) => num.toString().padStart(2, '0');
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${pad(m)}:${pad(s)}`;
  return `${m}:${pad(s)}`;
};


const animalEmojis = ['🦊', '🐰', '🐻', '🐼', '🐯', '🦁', '🐨', '🐮', '🐷', '🐸', '🐹', '🐭', '🐱', '🐶', '🐒', '🐧', '🦉', '🐢'];
const animalNames = ['キツネ', 'ウサギ', 'クマ', 'パンダ', 'トラ', 'ライオン', 'コアラ', 'ウシ', 'ブタ', 'カエル', 'ハムスター', 'ネズミ', 'ネコ', 'イヌ', 'サル', 'ペンギン', 'フクロウ', 'カメ'];
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
    color: speakerColors[hash % speakerColors.length],
    animalName: animalNames[hash % animalNames.length]
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

type Segment = { start: number; end: number; speaker: string; text: string };
type Highlight = { start: number; speaker: string; text: string; reason: string };
type Topic = {
  title: string;
  summary: string;
  highlights: Highlight[];
};
type SummaryData = {
  topics: Topic[];
};

type ResultItem = {
  id: string;
  title: string;
  timestamp: string;
  transcription_status: string;
  summary_status: string;
  notion_status: string;
  audio_filename: string | null;
};

function App() {
  const [results, setResults] = useState<ResultItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [data, setData] = useState<{ created_at: string; segments: Segment[] } | null>(null);
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [elapsedTime, setElapsedTime] = useState(0);
  
  const [activeTab, setActiveTab] = useState<'summary' | 'transcript'>('summary');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const fetchResults = async () => {
    try {
      const res = await fetch(`${API_BASE}/results`);
      const json = await res.json();
      setResults(json.results || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchResults();
  }, []);

  const processingIds = results.filter(r => 
    r.transcription_status === 'processing' || 
    r.summary_status === 'processing' || 
    r.notion_status === 'processing' ||
    r.transcription_status === 'none'
  ).map(r => r.id);

  useEffect(() => {
    if (processingIds.length === 0) return;

    const interval = setInterval(() => {
      // Reactの仕様上、ここは「タイマーがセットされた時点の古いresults」を参照してしまうこと（Stale Closure）が原因で
      // 文字起こしが終わっても一生「要約」の有無を確認しにいかないというバグがありました。
      // 確実に対応するため、10秒ごとにリスト全体を再取得して最新化するようにします。
      fetchResults();
    }, 10000);

    return () => clearInterval(interval);
  }, [processingIds.join(',')]);

  const selectedResult = results.find(r => r.id === selectedId);
  const isLoadingTranscription = selectedResult?.transcription_status === 'processing' || selectedResult?.transcription_status === 'none';
  const isLoadingSummary = selectedResult?.summary_status === 'processing' || (selectedResult?.transcription_status === 'success' && selectedResult?.summary_status === 'none');
  const isLoadingNotion = selectedResult?.notion_status === 'processing';

  useEffect(() => {
    if (selectedResult) {
      if (selectedResult.transcription_status === 'success') {
        fetch(`${API_BASE}/outputs/${selectedResult.id}/transcription.json`)
          .then(r => r.json())
          .then(setData)
          .catch(console.error);
      } else {
        setData(null);
      }

      if (selectedResult.summary_status === 'success') {
        fetch(`${API_BASE}/outputs/${selectedResult.id}/summary.json`)
          .then(r => r.json())
          .then(setSummaryData)
          .catch(console.error);
      } else {
        setSummaryData(null);
      }
    } else {
      setData(null);
      setSummaryData(null);
    }
  }, [selectedResult?.id, selectedResult?.transcription_status, selectedResult?.summary_status]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isLoadingTranscription || isLoadingSummary || isLoadingNotion) {
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    } else {
      setElapsedTime(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isLoadingTranscription, isLoadingSummary, isLoadingNotion, selectedId]);

  const audioUrl = selectedResult?.audio_filename 
      ? `${API_BASE}/outputs/${selectedResult.id}/${selectedResult.audio_filename}` 
      : null;

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
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const onClickSubmit = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadMessage("処理を要求中...");
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      const resData = await res.json();
      
      setUploadMessage(resData.message || "POSTしました");
      fetchResults(); // Immediate refresh
      
      // select it
      if (resData.folder) {
        setSelectedId(resData.folder);
      }
      
      setTimeout(() => {
        setIsUploading(false);
        setFile(null);
        setUploadMessage("");
      }, 2000);

    } catch (error) {
      console.error(error);
      setUploadMessage("エラーが発生しました");
      setTimeout(() => setIsUploading(false), 2000);
    }
  };

  const onClickRetry = async (step: string) => {
    if (!selectedId) return;
    setIsUploading(true);
    let stepName = step === "transcription" ? "文字起こし" : step === "summary" ? "要約" : "Notion出力";
    setUploadMessage(`${stepName}の再処理を要求中...`);
    try {
      const res = await fetch(`${API_BASE}/retry/${selectedId}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ step }),
      });
      const resData = await res.json();
      setUploadMessage(resData.message || "再処理を開始しました");
      fetchResults(); // Immediate refresh
      
      setTimeout(() => {
        setIsUploading(false);
        setUploadMessage("");
      }, 2000);

    } catch (error) {
      console.error(error);
      setUploadMessage("再処理要求に失敗しました");
      setTimeout(() => setIsUploading(false), 2000);
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="header-icon-small">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
              <line x1="8" x2="16" y1="22" y2="22" />
            </svg>
          </div>
          <h2>こえログ</h2>
        </div>

        <div className="upload-container">
          {!file && !isUploading ? (
            <div 
              className={`upload-area-small ${isDragging ? "active" : ""}`}
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
              <svg className="upload-icon-small" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
                <path d="M12 12v9" />
                <path d="m16 16-4-4-4 4" />
              </svg>
              <div className="upload-text-small">クリックまたはドラッグでアップロード</div>
            </div>
          ) : (
            <div className="upload-active-container">
              {isUploading ? (
                 <div className="uploading-state">
                   <svg className="spinner-small" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                     <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                   </svg>
                   <span>{uploadMessage}</span>
                 </div>
              ) : (
                 <div className="file-info-small">
                  <div className="file-name-small" title={file?.name}>{file?.name}</div>
                  <div className="file-actions">
                    <button className="remove-btn-small" onClick={removeFile} aria-label="ファイルを削除">✕</button>
                    <button className="submit-btn-small" onClick={onClickSubmit}>解析</button>
                  </div>
                 </div>
              )}
            </div>
          )}
        </div>

        <div className="results-list-container">
          <div className="list-title">履歴</div>
          <div className="results-list">
            {results.length === 0 ? (
               <div className="empty-state">履歴はありません</div>
            ) : (
              results.map(r => (
                <div 
                  key={r.id} 
                  className={`result-item ${selectedId === r.id ? 'active' : ''}`} 
                  onClick={() => setSelectedId(r.id)}
                >
                  <div className="result-item-header">
                     <div className="result-item-title" title={r.title}>{r.title}</div>
                  </div>
                  <div className="result-item-footer">
                     <div className="result-item-time">{r.timestamp || r.id}</div>
                     {(r.transcription_status === 'failed' || r.summary_status === 'failed' || r.notion_status === 'failed') ? (
                        <span className="badge badge-error" style={{backgroundColor: '#fee2e2', color: '#991b1b'}}>エラー ❌</span>
                     ) : (r.transcription_status === 'processing' || r.transcription_status === 'none') ? (
                        <span className="badge badge-processing">文字起こし中</span>
                     ) : (r.summary_status === 'processing' || (r.transcription_status === 'success' && r.summary_status === 'none')) ? (
                        <span className="badge badge-warning">要約中</span>
                     ) : r.notion_status === 'processing' ? (
                        <span className="badge badge-processing" style={{backgroundColor: '#dbeafe', color: '#1e40af'}}>Notion出力中</span>
                     ) : (
                        <span className="badge badge-success">完了</span>
                     )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {!selectedResult ? (
          <div className="empty-main-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.2, marginBottom: '1rem' }}>
              <polyline points="9 14 4 9 9 4"/>
              <path d="M20 20v-7a4 4 0 0 0-4-4H4"/>
            </svg>
            <h2>サイドバーから履歴を選択するか<br/>新しい音声をアップロードしてください</h2>
          </div>
        ) : (
          <div className="result-section">
            <div className="result-header">
              <div style={{display: "flex", justifyContent: "space-between", alignItems: "flex-start", width: "100%"}}>
                <h2>{selectedResult.title}</h2>
                <div className="status-badges" style={{display: "flex", gap: "8px", flexDirection: "column", alignItems: "flex-end"}}>
                  {selectedResult.transcription_status === 'failed' && (
                    <div style={{display: "flex", gap: "8px", alignItems: "center"}}>
                      <span className="badge" style={{backgroundColor: '#fee2e2', color: '#991b1b'}}>文字起こし ❌</span>
                      <button className="submit-btn-small" style={{padding: "2px 8px", fontSize: "0.8em"}} onClick={() => onClickRetry('transcription')}>再実行</button>
                    </div>
                  )}
                  {selectedResult.summary_status === 'failed' && (
                    <div style={{display: "flex", gap: "8px", alignItems: "center"}}>
                      <span className="badge" style={{backgroundColor: '#fee2e2', color: '#991b1b'}}>要約 ❌</span>
                      <button className="submit-btn-small" style={{padding: "2px 8px", fontSize: "0.8em"}} onClick={() => onClickRetry('summary')}>再実行</button>
                    </div>
                  )}
                  {selectedResult.notion_status === 'failed' && (
                    <div style={{display: "flex", gap: "8px", alignItems: "center"}}>
                      <span className="badge" style={{backgroundColor: '#fee2e2', color: '#991b1b'}}>Notion 📝❌</span>
                      <button className="submit-btn-small" style={{padding: "2px 8px", fontSize: "0.8em"}} onClick={() => onClickRetry('notion')}>再実行</button>
                    </div>
                  )}
                  {selectedResult.notion_status === 'success' && (
                    <span className="badge badge-success">Notion 📝✅</span>
                  )}
                </div>
              </div>
              <span className="result-date">{selectedResult.timestamp}</span>
            </div>
            
            <div className="result-content-wrapper">
              <div className="tabs-container">
                <div className="tab-indicator" style={{ transform: activeTab === 'summary' ? 'translateX(0)' : 'translateX(100%)' }}></div>
                <button 
                  className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`} 
                  onClick={() => setActiveTab('summary')}
                >
                  要約・ハイライト
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'transcript' ? 'active' : ''}`} 
                  onClick={() => setActiveTab('transcript')}
                >
                  文字起こし全文
                </button>
              </div>

              {audioUrl && (
                <div className="audio-player-container">
                  <CustomAudioPlayer src={audioUrl} audioRef={audioRef} />
                </div>
              )}

              <div className="scrollable-content">
                {/* Summary Tab */}
                <div className={`tab-content ${activeTab === 'summary' ? 'active' : ''}`}>
                  {(isLoadingTranscription || isLoadingSummary || isLoadingNotion) && (!summaryData || isLoadingNotion) ? (
                    <div className="loading-animation-wrapper" style={{ marginBottom: '1.75rem' }}>
                      <div className="walking-container">
                        <div className="walking-character-wrapper">
                          <div className="walking-character follower">🏃</div>
                          <div className="walking-character">🐕</div>
                        </div>
                      </div>
                      <div className="loading-text">
                        {isLoadingTranscription ? '文字起こし中です...' : isLoadingSummary ? '要約生成中です...' : 'Notionへ出力中です...'}
                        <span style={{ marginLeft: "12px", fontSize: "0.9em", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                          {elapsedTime > 0 ? `${elapsedTime}秒経過` : ''}
                        </span>
                      </div>
                    </div>
                  ) : null}

                  {isLoadingSummary && data && (
                    <div className="summary-card skeleton-summary-card" style={{ marginBottom: '0' }}>
                      <div className="skeleton-line" style={{ width: '30%', height: '16px', marginBottom: '14px' }}></div>
                      <div className="skeleton-line"></div>
                      <div className="skeleton-line" style={{ width: '80%' }}></div>
                      <div className="skeleton-line" style={{ width: '60%', marginBottom: '0' }}></div>
                    </div>
                  )}

                  {summaryData && (
                    <div className="topics-container" style={{ animation: 'fadeInTab 0.5s ease-out' }}>
                      {summaryData.topics.map((topic, topicIndex) => (
                        <div key={topicIndex} className="topic-card">
                          <div className="topic-header">
                            <span className="topic-number">{topicIndex + 1}</span>
                            <h3 className="topic-title">{topic.title}</h3>
                          </div>
                          <p className="topic-summary">{topic.summary}</p>
                          {topic.highlights.length > 0 && (
                            <div className="summary-highlights">
                              <div className="summary-highlights-title">⭐ 重要箇所</div>
                              {topic.highlights.map((h, i) => (
                                <button
                                  key={i}
                                  className="highlight-item"
                                  onClick={() => {
                                    playAudioAt(h.start);
                                  }}
                                  title={`${formatTime(h.start)} から再生`}
                                  aria-label={`重要箇所: ${h.text}`}
                                >
                                  <span className="highlight-time">{formatTime(h.start)}</span>
                                  <span className="highlight-text">{h.text}</span>
                                  <span className="highlight-reason">{h.reason}</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Transcript Tab */}
                <div className={`tab-content ${activeTab === 'transcript' ? 'active' : ''}`}>
                  {isLoadingTranscription && !data ? (
                    <div className="chat-container">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className={`chat-message ${i % 2 === 0 ? 'chat-right' : 'chat-left'} speaker-changed skeleton-message`}>
                          <div className="chat-avatar-wrapper">
                            <div className="chat-avatar skeleton-avatar"></div>
                          </div>
                          <div className="chat-content">
                            <div className="chat-header">
                              <div className="skeleton-name"></div>
                            </div>
                            <div className="chat-bubble-row">
                              <div className="chat-bubble skeleton-bubble" style={{ 
                                borderLeft: i % 2 !== 0 ? '3px solid #e2e8f0' : 'none', 
                                borderRight: i % 2 === 0 ? '3px solid #e2e8f0' : 'none' 
                              }}>
                                <div className="skeleton-line"></div>
                                <div className="skeleton-line" style={{ width: i % 2 === 0 ? '70%' : '90%' }}></div>
                                {i === 1 && <div className="skeleton-line" style={{ width: '50%' }}></div>}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {data && (
                    <div className="chat-container">
                      {data.segments.map((segment: Segment, index: number) => {
                        const speakerName = segment.speaker || "話者";
                        const { emoji, color, animalName } = getSpeakerStyle(speakerName);
                        
                        const firstSpeaker = data.segments[0]?.speaker || "話者";
                        const isRight = speakerName === firstSpeaker;
                        
                        const prevSpeaker = index > 0 ? (data.segments[index - 1].speaker || "話者") : null;
                        const isSpeakerChanged = index === 0 || prevSpeaker !== speakerName;

                        const isHighlighted = summaryData?.topics.some(
                          topic => topic.highlights.some(
                            h => Math.abs(h.start - segment.start) < 0.5
                          )
                        ) ?? false;
                        
                        return (
                          <div 
                            key={`${segment.start}-${index}`} 
                            className={`chat-message ${isRight ? 'chat-right' : 'chat-left'} ${isSpeakerChanged ? 'speaker-changed' : 'same-speaker'}`}
                          >
                            <div className="chat-avatar-wrapper">
                              {isSpeakerChanged && (
                                <div 
                                  className="chat-avatar" 
                                  style={{ backgroundColor: `${color}33`, border: `2px solid ${color}` }} 
                                  title={speakerName}
                                >
                                  {emoji}
                                </div>
                              )}
                            </div>
                            <div className="chat-content">
                              {isSpeakerChanged && (
                                <div className="chat-header">
                                  <span className="chat-speaker" style={{ color: color }}>
                                    {animalName}さん
                                  </span>
                                  {isHighlighted && <span className="highlight-star" title="重要箇所">⭐</span>}
                                </div>
                              )}
                              <div className="chat-bubble-row">
                                <div 
                                  className={`chat-bubble${isHighlighted ? ' chat-bubble-highlighted' : ''}`}
                                  style={{ 
                                    borderLeft: !isRight ? `3px solid ${color}` : 'none', 
                                    borderRight: isRight ? `3px solid ${color}` : 'none',
                                    cursor: 'pointer'
                                  }}
                                  onClick={() => playAudioAt(segment.start)}
                                  title="クリックしてこの時間から再生"
                                  aria-label={`${formatTime(segment.start)}から再生`}
                                >
                                  <div className="chat-text">{segment.text}</div>
                                  {isHighlighted && !isSpeakerChanged && (
                                    <span className="highlight-star-inline" title="重要箇所">⭐</span>
                                  )}
                                </div>
                                <button 
                                  className="chat-time chat-time-link"
                                  onClick={() => playAudioAt(segment.start)}
                                  title="クリックしてこの時間から再生"
                                  aria-label={`${formatTime(segment.start)}から再生`}
                                >
                                  {formatTime(segment.start)}
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
