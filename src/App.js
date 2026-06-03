import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

function App() {
  const [musicFiles, setMusicFiles] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [theme, setTheme] = useState('dark');
  const [showQueue, setShowQueue] = useState(false);
  const [repeatMode, setRepeatMode] = useState('none'); // none, one, all
  const [shuffle, setShuffle] = useState(false);
  const [showJellyfinSetup, setShowJellyfinSetup] = useState(false);
  const [jellyfinConnected, setJellyfinConnected] = useState(false);
  const [jellyfinLibraries, setJellyfinLibraries] = useState([]);
  const [selectedLibrary, setSelectedLibrary] = useState(null);
  const [jellyfinItems, setJellyfinItems] = useState([]);
  const [currentMediaType, setCurrentMediaType] = useState('Audio');
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [showAudioSettings, setShowAudioSettings] = useState(false);
  const [showUrlStreaming, setShowUrlStreaming] = useState(false);
  const [audioDevices, setAudioDevices] = useState([]);
  const [audioSettings, setAudioSettings] = useState({ defaultDevice: 'default', volume: 0.7 });
  const [streamingUrls, setStreamingUrls] = useState([]);
  const [mediaServerDetected, setMediaServerDetected] = useState(false);
  const [mediaServerInfo, setMediaServerInfo] = useState(null);
  const [enableMediaServerAutoDetect, setEnableMediaServerAutoDetect] = useState(false);
  
  const audioRef = useRef(null);
  const videoRef = useRef(null);
  const progressBarRef = useRef(null);
  const volumeBarRef = useRef(null);

  // Media server autodetection (hidden by default)
  useEffect(() => {
    const detectMediaServer = async () => {
      const defaultServerUrl = 'https://media.raywonderis.me';
      
      try {
        const response = await fetch(`${defaultServerUrl}/System/Info/Public`);
        const info = await response.json();
        
        console.log("Connected to:", info.ServerName);
        setMediaServerDetected(true);
        setMediaServerInfo({
          serverName: info.ServerName,
          serverUrl: defaultServerUrl,
          version: info.Version
        });
      } catch (err) {
        console.log("Media server not available - using local mode");
        setMediaServerDetected(false);
        setMediaServerInfo(null);
      }
    };

    // Only auto-detect if explicitly enabled
    const autoDetectEnabled = localStorage.getItem('enableMediaServerAutoDetect') === 'true';
    setEnableMediaServerAutoDetect(autoDetectEnabled);
    if (autoDetectEnabled) {
      detectMediaServer();
    }
  }, []);

  // Load saved preferences
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedVolume = localStorage.getItem('volume') || '0.7';
    const savedRepeat = localStorage.getItem('repeatMode') || 'none';
    const savedShuffle = localStorage.getItem('shuffle') === 'true';
    
    setTheme(savedTheme);
    setVolume(parseFloat(savedVolume));
    setRepeatMode(savedRepeat);
    setShuffle(savedShuffle);
    
    document.body.setAttribute('data-theme', savedTheme);
  }, []);

  // Load audio devices and settings
  useEffect(() => {
    const loadAudioData = async () => {
      if (window.electronAPI) {
        try {
          const [devices, settings] = await Promise.all([
            window.electronAPI.getAudioDevices(),
            window.electronAPI.loadAudioSettings()
          ]);
          setAudioDevices(devices);
          setAudioSettings(settings);
          setVolume(settings.volume || 0.7);
        } catch (error) {
          console.error('Failed to load audio data:', error);
        }
      }
    };
    
    loadAudioData();
  }, []);

  // Electron API event listeners
  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onMusicFilesLoaded((files) => {
        setMusicFiles(files);
        if (files.length > 0 && currentIndex === -1) {
          setCurrentIndex(0);
          setCurrentTrack(files[0]);
        }
      });

      window.electronAPI.onPlaybackToggle(() => {
        togglePlayPause();
      });

      window.electronAPI.onPlaybackPrevious(() => {
        previousTrack();
      });

      window.electronAPI.onPlaybackNext(() => {
        nextTrack();
      });

      window.electronAPI.onToggleTheme(() => {
        toggleTheme();
      });

      window.electronAPI.onShowJellyfinSetup(() => {
        setShowJellyfinSetup(true);
      });

      window.electronAPI.onShowAudioSettings(() => {
        setShowAudioSettings(true);
      });

      window.electronAPI.onShowUrlStreaming(() => {
        setShowUrlStreaming(true);
      });
    }

    return () => {
      if (window.electronAPI) {
        window.electronAPI.removeAllListeners('music-files-loaded');
        window.electronAPI.removeAllListeners('playback-toggle');
        window.electronAPI.removeAllListeners('playback-previous');
        window.electronAPI.removeAllListeners('playback-next');
        window.electronAPI.removeAllListeners('toggle-theme');
        window.electronAPI.removeAllListeners('show-jellyfin-setup');
        window.electronAPI.removeAllListeners('show-audio-settings');
        window.electronAPI.removeAllListeners('show-url-streaming');
      }
    };
  }, []);

  // Audio event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration || 0);
    const handleEnded = () => {
      if (repeatMode === 'one') {
        audio.currentTime = 0;
        audio.play();
      } else {
        nextTrack();
      }
    };
    const handleCanPlay = () => {
      if (isPlaying) {
        audio.play();
      }
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [repeatMode, isPlaying]);

  // Update audio volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
    localStorage.setItem('volume', volume.toString());
  }, [volume]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.target.tagName === 'INPUT') return;
      
      switch (e.code) {
        case 'Space':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            previousTrack();
          }
          break;
        case 'ArrowRight':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            nextTrack();
          }
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  const loadTrack = useCallback((track, index) => {
    if (!track) return;
    
    const audio = audioRef.current;
    if (audio) {
      audio.src = `file://${track.path}`;
      setCurrentTrack(track);
      setCurrentIndex(index);
      setCurrentTime(0);
      setDuration(0);
      
      // Save current position
      localStorage.setItem('currentTrack', JSON.stringify({ track, index }));
    }
  }, []);

  const togglePlayPause = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !currentTrack) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying, currentTrack]);

  const nextTrack = useCallback(() => {
    if (musicFiles.length === 0) return;
    
    let nextIndex;
    if (shuffle) {
      nextIndex = Math.floor(Math.random() * musicFiles.length);
    } else {
      nextIndex = (currentIndex + 1) % musicFiles.length;
    }
    
    if (repeatMode === 'none' && nextIndex === 0 && currentIndex === musicFiles.length - 1) {
      setIsPlaying(false);
      return;
    }
    
    loadTrack(musicFiles[nextIndex], nextIndex);
    if (isPlaying) {
      setTimeout(() => audioRef.current?.play(), 100);
    }
  }, [musicFiles, currentIndex, shuffle, repeatMode, isPlaying, loadTrack]);

  const previousTrack = useCallback(() => {
    if (musicFiles.length === 0) return;
    
    let prevIndex;
    if (shuffle) {
      prevIndex = Math.floor(Math.random() * musicFiles.length);
    } else {
      prevIndex = currentIndex === 0 ? musicFiles.length - 1 : currentIndex - 1;
    }
    
    loadTrack(musicFiles[prevIndex], prevIndex);
    if (isPlaying) {
      setTimeout(() => audioRef.current?.play(), 100);
    }
  }, [musicFiles, currentIndex, shuffle, isPlaying, loadTrack]);

  const seekTo = useCallback((percentage) => {
    const audio = audioRef.current;
    if (audio && duration) {
      audio.currentTime = (percentage / 100) * duration;
    }
  }, [duration]);

  const toggleTheme = useCallback(() => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  }, [theme]);

  const toggleRepeat = useCallback(() => {
    const modes = ['none', 'all', 'one'];
    const currentModeIndex = modes.indexOf(repeatMode);
    const nextMode = modes[(currentModeIndex + 1) % modes.length];
    setRepeatMode(nextMode);
    localStorage.setItem('repeatMode', nextMode);
  }, [repeatMode]);

  const toggleShuffle = useCallback(() => {
    const newShuffle = !shuffle;
    setShuffle(newShuffle);
    localStorage.setItem('shuffle', newShuffle.toString());
  }, [shuffle]);

  const selectMusicFolder = useCallback(() => {
    if (window.electronAPI) {
      window.electronAPI.selectMusicFolder();
    }
  }, []);

  const connectToJellyfin = async (serverUrl, username, password) => {
    try {
      const result = await window.electronAPI.jellyfinConnect({
        serverUrl,
        username,
        password
      });

      if (result.success) {
        setJellyfinConnected(true);
        const libraries = await window.electronAPI.jellyfinGetLibraries();
        setJellyfinLibraries(libraries);
        setShowJellyfinSetup(false);
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const loadJellyfinLibrary = async (libraryId, mediaType = 'Audio') => {
    try {
      const items = await window.electronAPI.jellyfinGetItems({
        parentId: libraryId,
        mediaType
      });
      
      const formattedItems = items.map(item => ({
        id: item.Id,
        title: item.Name,
        artist: item.AlbumArtist || item.Artists?.[0] || 'Unknown Artist',
        album: item.Album || 'Unknown Album',
        duration: item.RunTimeTicks ? item.RunTimeTicks / 10000000 : 0,
        track: item.IndexNumber || 0,
        year: item.ProductionYear || null,
        genre: item.Genres?.[0] || null,
        isJellyfin: true,
        streamUrl: null
      }));

      setJellyfinItems(formattedItems);
      setSelectedLibrary(libraryId);
      setCurrentMediaType(mediaType);
    } catch (error) {
      console.error('Failed to load Jellyfin library:', error);
    }
  };

  const loadJellyfinTrack = useCallback(async (track, index) => {
    if (!track || !track.isJellyfin) return;

    try {
      const streamUrl = await window.electronAPI.jellyfinGetStreamUrl(track.id);
      const audio = audioRef.current;
      if (audio) {
        audio.src = streamUrl;
        setCurrentTrack({ ...track, streamUrl });
        setCurrentIndex(index);
        setCurrentTime(0);
        setDuration(0);
      }
    } catch (error) {
      console.error('Failed to load Jellyfin track:', error);
    }
  }, []);

  const playJellyfinVideo = useCallback(async (video) => {
    try {
      const streamUrl = await window.electronAPI.jellyfinGetStreamUrl(video.id);
      setCurrentVideo({ ...video, streamUrl });
      setShowVideoPlayer(true);
    } catch (error) {
      console.error('Failed to load Jellyfin video:', error);
    }
  }, []);

  const addStreamingUrl = useCallback((url, title = '') => {
    const newStream = {
      id: Date.now(),
      url,
      title: title || new URL(url).hostname,
      isStream: true
    };
    setStreamingUrls(prev => [...prev, newStream]);
    return newStream;
  }, []);

  const loadStreamUrl = useCallback((streamUrl, title = '') => {
    const audio = audioRef.current;
    if (audio) {
      audio.src = streamUrl;
      setCurrentTrack({
        title: title || 'Network Stream',
        artist: 'Streaming',
        album: 'Network',
        duration: 0,
        isStream: true,
        path: streamUrl
      });
      setCurrentIndex(-1);
      setCurrentTime(0);
      setDuration(0);
    }
  }, []);

  const saveAudioSettings = async (newSettings) => {
    try {
      const result = await window.electronAPI.saveAudioSettings(newSettings);
      if (result.success) {
        setAudioSettings(newSettings);
        if (newSettings.volume !== undefined) {
          setVolume(newSettings.volume);
        }
      }
      return result;
    } catch (error) {
      console.error('Failed to save audio settings:', error);
      return { success: false, error: error.message };
    }
  };

  const toggleMediaServerAutoDetect = async (enabled) => {
    setEnableMediaServerAutoDetect(enabled);
    localStorage.setItem('enableMediaServerAutoDetect', enabled.toString());
    
    if (enabled) {
      // Trigger detection immediately
      const defaultServerUrl = 'https://media.raywonderis.me';
      try {
        const response = await fetch(`${defaultServerUrl}/System/Info/Public`);
        const info = await response.json();
        
        console.log("Connected to:", info.ServerName);
        setMediaServerDetected(true);
        setMediaServerInfo({
          serverName: info.ServerName,
          serverUrl: defaultServerUrl,
          version: info.Version
        });
      } catch (err) {
        console.log("Media server not available - using local mode");
        setMediaServerDetected(false);
        setMediaServerInfo(null);
      }
    } else {
      // Disable and clear connection
      setMediaServerDetected(false);
      setMediaServerInfo(null);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleProgressClick = (e) => {
    const rect = progressBarRef.current.getBoundingClientRect();
    const percentage = ((e.clientX - rect.left) / rect.width) * 100;
    seekTo(percentage);
  };

  const handleVolumeClick = (e) => {
    const rect = volumeBarRef.current.getBoundingClientRect();
    const percentage = (e.clientX - rect.left) / rect.width;
    setVolume(Math.max(0, Math.min(1, percentage)));
  };

  return (
    <div className="app">
      <audio ref={audioRef} />
      
      <div className="main-content">
        <div className="sidebar">
          <div className="sidebar-header">
            <h1>Media Player</h1>
            <button className="theme-toggle" onClick={toggleTheme}>
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
          
          <div className="sidebar-actions">
            <button className="folder-btn" onClick={selectMusicFolder}>
              📁 Open Music Folder
            </button>
            <button 
              className={`queue-btn ${showQueue ? 'active' : ''}`}
              onClick={() => setShowQueue(!showQueue)}
            >
              📜 Queue ({musicFiles.length})
            </button>
          </div>

          {mediaServerDetected && mediaServerInfo && (
            <div className="media-server-status">
              <div className="server-indicator">
                <span className="status-dot connected">●</span>
                <span className="server-name">{mediaServerInfo.serverName}</span>
              </div>
              <div className="server-details">
                Connected to media server
              </div>
            </div>
          )}

          {showQueue && (
            <div className="queue">
              {musicFiles.map((track, index) => (
                <div 
                  key={index}
                  className={`queue-item ${index === currentIndex ? 'active' : ''}`}
                  onClick={() => {
                    loadTrack(track, index);
                    if (isPlaying) {
                      setTimeout(() => audioRef.current?.play(), 100);
                    }
                  }}
                >
                  <div className="track-info">
                    <div className="track-title">{track.title}</div>
                    <div className="track-artist">{track.artist}</div>
                  </div>
                  <div className="track-duration">{formatTime(track.duration)}</div>
                </div>
              ))}
            </div>
          )}

          {jellyfinConnected && (
            <div className="jellyfin-section">
              <h3>🔗 Jellyfin Libraries</h3>
              <div className="jellyfin-controls">
                <select 
                  onChange={(e) => setCurrentMediaType(e.target.value)}
                  value={currentMediaType}
                >
                  <option value="Audio">Music</option>
                  <option value="Video">Videos</option>
                </select>
              </div>
              <div className="jellyfin-libraries">
                {jellyfinLibraries.map((library, index) => (
                  <button
                    key={library.Id}
                    className={`library-btn ${selectedLibrary === library.Id ? 'active' : ''}`}
                    onClick={() => loadJellyfinLibrary(library.Id, currentMediaType)}
                  >
                    {library.Name}
                  </button>
                ))}
              </div>
              {jellyfinItems.length > 0 && (
                <div className="jellyfin-queue">
                  <h4>Jellyfin {currentMediaType === 'Audio' ? 'Music' : 'Videos'} ({jellyfinItems.length})</h4>
                  {jellyfinItems.map((item, index) => (
                    <div 
                      key={item.id}
                      className={`queue-item ${index === currentIndex && currentTrack?.isJellyfin ? 'active' : ''}`}
                      onClick={() => {
                        if (currentMediaType === 'Audio') {
                          loadJellyfinTrack(item, index);
                          if (isPlaying) {
                            setTimeout(() => audioRef.current?.play(), 100);
                          }
                        } else {
                          // For videos
                          playJellyfinVideo(item);
                        }
                      }}
                    >
                      <div className="track-info">
                        <div className="track-title">{item.title}</div>
                        <div className="track-artist">{item.artist}</div>
                      </div>
                      <div className="track-duration">{formatTime(item.duration)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {streamingUrls.length > 0 && (
            <div className="streaming-section">
              <h3>🌐 Streaming URLs</h3>
              <div className="streaming-queue">
                {streamingUrls.map((stream) => (
                  <div 
                    key={stream.id}
                    className={`queue-item ${currentTrack?.isStream && currentTrack?.path === stream.url ? 'active' : ''}`}
                    onClick={() => {
                      loadStreamUrl(stream.url, stream.title);
                      if (isPlaying) {
                        setTimeout(() => audioRef.current?.play(), 100);
                      }
                    }}
                  >
                    <div className="track-info">
                      <div className="track-title">{stream.title}</div>
                      <div className="track-artist">Network Stream</div>
                    </div>
                    <button
                      className="remove-stream-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        setStreamingUrls(prev => prev.filter(s => s.id !== stream.id));
                      }}
                      title="Remove stream"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="player-area">
          <div className="now-playing">
            {currentTrack ? (
              <>
                <div className="album-art">
                  {currentTrack.coverArt ? (
                    <img 
                      src={`data:${currentTrack.coverArt.format};base64,${currentTrack.coverArt.data.toString('base64')}`} 
                      alt="Album Art" 
                    />
                  ) : (
                    <div className="no-art">🎵</div>
                  )}
                </div>
                <div className="track-details">
                  <h2>{currentTrack.title}</h2>
                  <h3>{currentTrack.artist}</h3>
                  <h4>{currentTrack.album}</h4>
                </div>
              </>
            ) : (
              <div className="no-track">
                <div className="no-art">🎵</div>
                <div className="track-details">
                  <h2>No track selected</h2>
                  <h3>Open a music folder to get started</h3>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="player-controls">
        <div className="progress-container">
          <span className="time">{formatTime(currentTime)}</span>
          <div 
            className="progress-bar" 
            ref={progressBarRef}
            onClick={handleProgressClick}
          >
            <div 
              className="progress-fill" 
              style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
            />
          </div>
          <span className="time">{formatTime(duration)}</span>
        </div>

        <div className="controls">
          <button 
            className={`control-btn ${shuffle ? 'active' : ''}`}
            onClick={toggleShuffle}
            title="Shuffle"
          >
            🔀
          </button>
          
          <button className="control-btn" onClick={previousTrack} title="Previous">
            ⏮️
          </button>
          
          <button 
            className="play-btn" 
            onClick={togglePlayPause}
            disabled={!currentTrack}
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>
          
          <button className="control-btn" onClick={nextTrack} title="Next">
            ⏭️
          </button>
          
          <button 
            className={`control-btn ${repeatMode !== 'none' ? 'active' : ''}`}
            onClick={toggleRepeat}
            title={`Repeat: ${repeatMode}`}
          >
            {repeatMode === 'one' ? '🔂' : '🔁'}
          </button>
        </div>

        <div className="volume-container">
          <span>🔊</span>
          <div 
            className="volume-bar" 
            ref={volumeBarRef}
            onClick={handleVolumeClick}
          >
            <div 
              className="volume-fill" 
              style={{ width: `${volume * 100}%` }}
            />
          </div>
          <span>{Math.round(volume * 100)}%</span>
        </div>
      </div>

      {showJellyfinSetup && <JellyfinSetupModal />}
      {showVideoPlayer && <VideoPlayer />}
      {showAudioSettings && <AudioSettingsModal />}
      {showUrlStreaming && <UrlStreamingModal />}
    </div>
  );

  function VideoPlayer() {
    const [videoVolume, setVideoVolume] = useState(0.7);
    const [isVideoPlaying, setIsVideoPlaying] = useState(false);
    const [videoCurrentTime, setVideoCurrentTime] = useState(0);
    const [videoDuration, setVideoDuration] = useState(0);

    useEffect(() => {
      const video = videoRef.current;
      if (!video || !currentVideo) return;

      const handleTimeUpdate = () => setVideoCurrentTime(video.currentTime);
      const handleDurationChange = () => setVideoDuration(video.duration || 0);
      const handlePlay = () => setIsVideoPlaying(true);
      const handlePause = () => setIsVideoPlaying(false);

      video.addEventListener('timeupdate', handleTimeUpdate);
      video.addEventListener('durationchange', handleDurationChange);
      video.addEventListener('play', handlePlay);
      video.addEventListener('pause', handlePause);

      // Set up video
      video.src = currentVideo.streamUrl;
      video.volume = videoVolume;

      return () => {
        video.removeEventListener('timeupdate', handleTimeUpdate);
        video.removeEventListener('durationchange', handleDurationChange);
        video.removeEventListener('play', handlePlay);
        video.removeEventListener('pause', handlePause);
      };
    }, [currentVideo, videoVolume]);

    const toggleVideoPlayPause = () => {
      const video = videoRef.current;
      if (!video) return;

      if (isVideoPlaying) {
        video.pause();
      } else {
        video.play();
      }
    };

    const seekVideo = (percentage) => {
      const video = videoRef.current;
      if (video && videoDuration) {
        video.currentTime = (percentage / 100) * videoDuration;
      }
    };

    const handleVideoProgressClick = (e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const percentage = ((e.clientX - rect.left) / rect.width) * 100;
      seekVideo(percentage);
    };

    return (
      <div className="video-player-overlay">
        <div className="video-player">
          <div className="video-header">
            <h2>{currentVideo?.title}</h2>
            <button 
              className="close-video-btn"
              onClick={() => {
                setShowVideoPlayer(false);
                setCurrentVideo(null);
                if (videoRef.current) {
                  videoRef.current.pause();
                }
              }}
            >
              ✕
            </button>
          </div>
          
          <div className="video-container">
            <video
              ref={videoRef}
              controls
              className="video-element"
              onDoubleClick={() => {
                if (videoRef.current.requestFullscreen) {
                  videoRef.current.requestFullscreen();
                }
              }}
            />
          </div>

          <div className="video-controls">
            <div className="video-progress-container">
              <span className="video-time">{formatTime(videoCurrentTime)}</span>
              <div 
                className="video-progress-bar"
                onClick={handleVideoProgressClick}
              >
                <div 
                  className="video-progress-fill" 
                  style={{ width: `${videoDuration ? (videoCurrentTime / videoDuration) * 100 : 0}%` }}
                />
              </div>
              <span className="video-time">{formatTime(videoDuration)}</span>
            </div>

            <div className="video-control-buttons">
              <button 
                className="video-control-btn" 
                onClick={toggleVideoPlayPause}
              >
                {isVideoPlaying ? '⏸️' : '▶️'}
              </button>
              
              <div className="video-volume-container">
                <span>🔊</span>
                <div 
                  className="video-volume-bar"
                  onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const percentage = (e.clientX - rect.left) / rect.width;
                    const newVolume = Math.max(0, Math.min(1, percentage));
                    setVideoVolume(newVolume);
                    if (videoRef.current) {
                      videoRef.current.volume = newVolume;
                    }
                  }}
                >
                  <div 
                    className="video-volume-fill" 
                    style={{ width: `${videoVolume * 100}%` }}
                  />
                </div>
                <span>{Math.round(videoVolume * 100)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function JellyfinSetupModal() {
    const [serverUrl, setServerUrl] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [connecting, setConnecting] = useState(false);
    const [error, setError] = useState('');

    const handleConnect = async (e) => {
      e.preventDefault();
      setConnecting(true);
      setError('');

      const result = await connectToJellyfin(serverUrl, username, password);
      
      if (!result.success) {
        setError(result.error || 'Connection failed');
      }
      
      setConnecting(false);
    };

    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h2>Connect to Jellyfin</h2>
            <button 
              className="close-btn"
              onClick={() => setShowJellyfinSetup(false)}
            >
              ✕
            </button>
          </div>
          <form onSubmit={handleConnect} className="jellyfin-form">
            <div className="form-group">
              <label>Server URL:</label>
              <input
                type="url"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="http://localhost:8096"
                required
              />
            </div>
            <div className="form-group">
              <label>Username:</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Password:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            <div className="form-actions">
              <button
                type="button"
                onClick={() => setShowJellyfinSetup(false)}
                className="cancel-btn"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={connecting}
                className="connect-btn"
              >
                {connecting ? 'Connecting...' : 'Connect'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  function AudioSettingsModal() {
    const [selectedDevice, setSelectedDevice] = useState(audioSettings.defaultDevice);
    const [defaultVolume, setDefaultVolume] = useState(audioSettings.volume || 0.7);
    const [mediaServerEnabled, setMediaServerEnabled] = useState(enableMediaServerAutoDetect);
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
      setSaving(true);
      const newSettings = {
        defaultDevice: selectedDevice,
        volume: defaultVolume
      };
      
      const result = await saveAudioSettings(newSettings);
      
      // Save media server setting
      if (mediaServerEnabled !== enableMediaServerAutoDetect) {
        await toggleMediaServerAutoDetect(mediaServerEnabled);
      }
      
      if (result.success) {
        setShowAudioSettings(false);
      }
      
      setSaving(false);
    };

    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h2>Audio Settings</h2>
            <button 
              className="close-btn"
              onClick={() => setShowAudioSettings(false)}
            >
              ✕
            </button>
          </div>
          <div className="audio-settings-form">
            <div className="form-group">
              <label>Default Audio Output Device:</label>
              <select
                value={selectedDevice}
                onChange={(e) => setSelectedDevice(e.target.value)}
              >
                {audioDevices.map(device => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Default Volume: {Math.round(defaultVolume * 100)}%</label>
              <div className="volume-slider-container">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={defaultVolume}
                  onChange={(e) => setDefaultVolume(parseFloat(e.target.value))}
                  className="volume-slider"
                />
              </div>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={mediaServerEnabled}
                  onChange={(e) => setMediaServerEnabled(e.target.checked)}
                />
                Enable Media Server Auto-Detection
              </label>
              <div className="setting-description">
                Automatically detect and connect to media.raywonderis.me on startup
              </div>
            </div>

            <div className="device-info">
              <h4>Current Audio Device:</h4>
              <p>{audioDevices.find(d => d.deviceId === selectedDevice)?.label || 'Unknown'}</p>
            </div>

            <div className="form-actions">
              <button
                type="button"
                onClick={() => setShowAudioSettings(false)}
                className="cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="connect-btn"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function UrlStreamingModal() {
    const [streamUrl, setStreamUrl] = useState('');
    const [streamTitle, setStreamTitle] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleAddStream = async (e) => {
      e.preventDefault();
      setLoading(true);
      setError('');

      try {
        // Basic URL validation
        new URL(streamUrl);
        
        const stream = addStreamingUrl(streamUrl, streamTitle);
        setShowUrlStreaming(false);
        setStreamUrl('');
        setStreamTitle('');
      } catch (err) {
        setError('Please enter a valid URL');
      }
      
      setLoading(false);
    };

    const handlePlayNow = async (e) => {
      e.preventDefault();
      setLoading(true);
      setError('');

      try {
        new URL(streamUrl);
        loadStreamUrl(streamUrl, streamTitle || 'Network Stream');
        setShowUrlStreaming(false);
        setStreamUrl('');
        setStreamTitle('');
      } catch (err) {
        setError('Please enter a valid URL');
      }
      
      setLoading(false);
    };

    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h2>Add Streaming URL</h2>
            <button 
              className="close-btn"
              onClick={() => setShowUrlStreaming(false)}
            >
              ✕
            </button>
          </div>
          <form className="url-streaming-form">
            <div className="form-group">
              <label>Stream URL:</label>
              <input
                type="url"
                value={streamUrl}
                onChange={(e) => setStreamUrl(e.target.value)}
                placeholder="https://example.com/stream.m3u8"
                required
              />
            </div>
            <div className="form-group">
              <label>Title (optional):</label>
              <input
                type="text"
                value={streamTitle}
                onChange={(e) => setStreamTitle(e.target.value)}
                placeholder="My Radio Station"
              />
            </div>
            
            <div className="stream-examples">
              <h4>Supported Formats:</h4>
              <ul>
                <li>HTTP Live Streaming (.m3u8)</li>
                <li>Direct audio streams (.mp3, .aac, .ogg)</li>
                <li>Icecast/Shoutcast streams</li>
                <li>WebM audio streams</li>
              </ul>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            <div className="form-actions">
              <button
                type="button"
                onClick={() => setShowUrlStreaming(false)}
                className="cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAddStream}
                disabled={loading || !streamUrl}
                className="add-stream-btn"
              >
                {loading ? 'Adding...' : 'Add to List'}
              </button>
              <button
                type="button"
                onClick={handlePlayNow}
                disabled={loading || !streamUrl}
                className="connect-btn"
              >
                {loading ? 'Loading...' : 'Play Now'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

export default App;