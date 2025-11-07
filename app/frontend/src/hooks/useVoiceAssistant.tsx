import useWebSocket from "react-use-websocket";
import { useCallback, useRef } from "react";
import useAudioPlayer from "./useAudioPlayer";

// Types for our WebSocket messages
interface VoiceEvent {
  type: string;
  event_type?: string;
  data?: any;
  error?: string;
  message?: string;
  timestamp?: number;
}

interface SessionConfig {
  model?: string;
  voice?: string;
}

interface ToolCallEvent {
  type: 'tool_call_started' | 'tool_call_arguments' | 'tool_call_executing' | 'tool_call_completed' | 'tool_call_error';
  function_name: string;
  call_id: string;
  arguments?: any;
  result?: any;
  error?: string;
  execution_time?: number;
  timestamp: number;
}

interface SessionEvent {
  type: 'session_started' | 'session_stopped' | 'session_error';
  status?: string;
  message?: string;
  error?: string;
  config?: {
    model: string;
    voice: string;
    tools_count: number;
    audio_streaming?: boolean;
    sample_rate?: number;
    format?: string;
    channels?: number;
  };
}

// Audio streaming interface
interface AudioDataEvent {
  type: 'audio_data';
  data: string; // base64 encoded PCM audio
  format: string;
  sample_rate: number;
  channels: number;
  timestamp: number;
}

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

type Parameters = {
  serverUrl?: string;
  clientId?: string;
  autoConnect?: boolean;
  
  // WebSocket event handlers
  onWebSocketOpen?: () => void;
  onWebSocketClose?: () => void;
  onWebSocketError?: (event: Event) => void;
  onWebSocketMessage?: (event: MessageEvent<any>) => void;

  // Voice assistant event handlers
  onSessionStarted?: (event: SessionEvent) => void;
  onSessionStopped?: (event: SessionEvent) => void;
  onSessionError?: (event: SessionEvent) => void;
  
  // Audio event handlers
  onSpeechStarted?: (event: VoiceEvent) => void;
  onSpeechStopped?: (event: VoiceEvent) => void;
  onResponseCreated?: (event: VoiceEvent) => void;
  onResponseDone?: (event: VoiceEvent) => void;
  onResponseTextDelta?: (event: VoiceEvent & { text: string }) => void;
  onResponseAudioDelta?: (event: VoiceEvent) => void;
  onResponseAudioDone?: (event: VoiceEvent) => void;
  
  // Audio streaming handlers
  onAudioData?: (event: AudioDataEvent) => void;
  onAudioPlaybackStart?: () => void;
  onAudioPlaybackStop?: () => void;
  
  // Tool call event handlers
  onToolCallStarted?: (event: ToolCallEvent) => void;
  onToolCallArguments?: (event: ToolCallEvent) => void;
  onToolCallExecuting?: (event: ToolCallEvent) => void;
  onToolCallCompleted?: (event: ToolCallEvent) => void;
  onToolCallError?: (event: ToolCallEvent) => void;
  
  // Conversation events
  onConversationItemCreated?: (event: VoiceEvent) => void;
  onTranscriptionCompleted?: (event: VoiceEvent) => void;
  onAssistantInterrupted?: (event: VoiceEvent) => void;
  
  // Error handler
  onError?: (event: VoiceEvent) => void;
};

export default function useVoiceAssistant({
  serverUrl,
  clientId,
  autoConnect = true,
  onWebSocketOpen,
  onWebSocketClose,
  onWebSocketError,
  onWebSocketMessage,
  onSessionStarted,
  onSessionStopped,
  onSessionError,
  onSpeechStarted,
  onSpeechStopped,
  onResponseCreated,
  onResponseDone,
  onResponseTextDelta,
  onResponseAudioDelta,
  onResponseAudioDone,
  onAudioData,
  onAudioPlaybackStart,
  onAudioPlaybackStop,
  onToolCallStarted,
  onToolCallArguments,
  onToolCallExecuting,
  onToolCallCompleted,
  onToolCallError,
  onConversationItemCreated,
  onTranscriptionCompleted,
  onAssistantInterrupted,
  onError
}: Parameters) {
  
  const clientIdRef = useRef(clientId || `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  
    const getWebSocketUrl = () => {
    if (serverUrl) return serverUrl;
    
    // Auto-detect based on current page URL
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}`;
    }
    
    return 'ws://localhost:8000'; // fallback for development
  };

  const wsEndpoint = `${getWebSocketUrl()}/ws/${clientIdRef.current}`;

  // Initialize audio player for streaming
  const audioPlayer = useAudioPlayer();

  const { sendJsonMessage, readyState } = useWebSocket(
    wsEndpoint,
    {
      onOpen: () => {
        console.log('WebSocket connected to voice assistant');
        // Initialize audio player when connection opens
        audioPlayer.reset();
        onWebSocketOpen?.();
      },
      onClose: () => {
        console.log('WebSocket disconnected from voice assistant');
        // Stop audio playback when connection closes
        audioPlayer.stop();
        onWebSocketClose?.();
      },
      onError: (event) => {
        console.error('WebSocket error:', event);
        onWebSocketError?.(event);
      },
      onMessage: (event) => {
        onWebSocketMessage?.(event);
        onMessageReceived(event);
      },
      shouldReconnect: () => true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    },
    autoConnect
  );

  const startSession = useCallback((config: SessionConfig = {}) => {
    console.log('Starting voice session with config:', config);
    // Reset audio player for new session
    audioPlayer.reset();
    
    sendJsonMessage({
      type: 'start_session',
      config: {
        model: 'gpt-4o-realtime',
        voice: 'pt-BR-FranciscaNeural',
        ...config
      }
    });
  }, [sendJsonMessage, audioPlayer]);

  const stopSession = useCallback(() => {
    console.log('Stopping voice session');
    // Stop audio playback
    audioPlayer.stop();
    
    sendJsonMessage({
      type: 'stop_session'
    });
  }, [sendJsonMessage, audioPlayer]);

  const sendAudio = useCallback((audioData: string) => {
    sendJsonMessage({
      type: 'send_audio',
      audio: audioData
    });
  }, [sendJsonMessage]);

  const sendAudioChunk = useCallback((audioData: string) => {
    sendJsonMessage({
      type: 'audio_chunk',
      data: audioData
    });
  }, [sendJsonMessage]);

  const interruptAssistant = useCallback(() => {
    console.log('Interrupting assistant');
    // Stop current audio playback
    audioPlayer.stop();
    
    sendJsonMessage({
      type: 'interrupt'
    });
  }, [sendJsonMessage, audioPlayer]);

  const onMessageReceived = useCallback((event: MessageEvent<any>) => {
    let message: WebSocketMessage;
    try {
      message = JSON.parse(event.data);
    } catch (e) {
      console.error("Failed to parse JSON message:", e);
      return;
    }

    console.log('Received message:', message.type, message);

    // Handle our custom message types
    switch (message.type) {
      case 'session_started':
        onSessionStarted?.(message as SessionEvent);
        break;
        
      case 'session_stopped':
        onSessionStopped?.(message as SessionEvent);
        break;
        
      case 'session_error':
        onSessionError?.(message as SessionEvent);
        break;

      // Audio streaming
      case 'audio_data':
        handleAudioData(message as AudioDataEvent);
        break;

      // Tool call events
      case 'tool_call_started':
        onToolCallStarted?.(message as ToolCallEvent);
        break;
        
      case 'tool_call_arguments':
        onToolCallArguments?.(message as ToolCallEvent);
        break;
        
      case 'tool_call_executing':
        onToolCallExecuting?.(message as ToolCallEvent);
        break;
        
      case 'tool_call_completed':
        onToolCallCompleted?.(message as ToolCallEvent);
        break;
        
      case 'tool_call_error':
        onToolCallError?.(message as ToolCallEvent);
        break;

      case 'assistant_interrupted':
        onAssistantInterrupted?.(message as VoiceEvent);
        break;

      // Voice Live API events (forwarded from backend)
      case 'voice_event':
        handleVoiceEvent(message.data, message.event_type);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [
    onSessionStarted,
    onSessionStopped, 
    onSessionError,
    onAudioData,
    onToolCallStarted,
    onToolCallArguments,
    onToolCallExecuting,
    onToolCallCompleted,
    onToolCallError,
    onAssistantInterrupted,
    onSpeechStarted,
    onSpeechStopped,
    onResponseCreated,
    onResponseDone,
    onResponseTextDelta,
    onResponseAudioDelta,
    onResponseAudioDone,
    onConversationItemCreated,
    onTranscriptionCompleted,
    onError,
    audioPlayer
  ]);

  // Handle audio data streaming
  const handleAudioData = useCallback((audioEvent: AudioDataEvent) => {
    try {
      console.log('Received audio data:', {
        format: audioEvent.format,
        sampleRate: audioEvent.sample_rate,
        channels: audioEvent.channels,
        dataLength: audioEvent.data.length
      });

      // Play the audio using the audio player
      audioPlayer.play(audioEvent.data);
      
      // Call the custom handler if provided
      onAudioData?.(audioEvent);
      
      // Trigger playback start event on first audio chunk
      onAudioPlaybackStart?.();
      
    } catch (error) {
      console.error('Error handling audio data:', error);
    }
  }, [audioPlayer, onAudioData, onAudioPlaybackStart]);

  const handleVoiceEvent = useCallback((eventData: any, eventType: string) => {
    const voiceEvent: VoiceEvent = {
      type: 'voice_event',
      event_type: eventType,
      data: eventData,
      timestamp: eventData.timestamp
    };

    // Route Azure VoiceLive events to appropriate handlers
    switch (eventType) {
      case 'input_audio_buffer.speech_started':
        onSpeechStarted?.(voiceEvent);
        break;
        
      case 'input_audio_buffer.speech_stopped':
        onSpeechStopped?.(voiceEvent);
        break;
        
      case 'response.created':
        onResponseCreated?.(voiceEvent);
        break;
        
      case 'response.done':
        onResponseDone?.(voiceEvent);
        onAudioPlaybackStop?.(); // Trigger playback stop when response is done
        break;
        
      case 'response.text.delta':
        onResponseTextDelta?.({
          ...voiceEvent,
          text: eventData.text
        });
        break;
        
      case 'response.audio.delta':
        // Audio deltas are now handled via audio_data messages
        onResponseAudioDelta?.(voiceEvent);
        break;
        
      case 'response.audio.done':
        onResponseAudioDone?.(voiceEvent);
        onAudioPlaybackStop?.(); // Trigger playback stop
        break;
        
      case 'conversation.item.created':
        onConversationItemCreated?.(voiceEvent);
        break;
        
      case 'conversation.item.input_audio_transcription.completed':
        onTranscriptionCompleted?.(voiceEvent);
        break;
        
      case 'error':
        onError?.(voiceEvent);
        break;
        
      default:
        console.log('Unhandled voice event:', eventType, eventData);
    }
  }, [
    onSpeechStarted,
    onSpeechStopped,
    onResponseCreated,
    onResponseDone,
    onResponseTextDelta,
    onResponseAudioDelta,
    onResponseAudioDone,
    onConversationItemCreated,
    onTranscriptionCompleted,
    onError,
    onAudioPlaybackStop
  ]);

  // Connection state helpers
  const isConnected = readyState === 1; // WebSocket.OPEN
  const isConnecting = readyState === 0; // WebSocket.CONNECTING
  const isDisconnected = readyState === 3; // WebSocket.CLOSED

  return {
    // Connection state
    isConnected,
    isConnecting,
    isDisconnected,
    clientId: clientIdRef.current,
    
    // Actions
    startSession,
    stopSession,
    sendAudio,
    sendAudioChunk, // For real-time audio streaming
    interruptAssistant,
    
    // Audio player controls
    audioPlayer, // Expose audio player for direct control
    
    // Raw WebSocket (if needed)
    sendJsonMessage
  };
}

// Export types for use in components
export type {
  VoiceEvent,
  SessionConfig,
  ToolCallEvent,
  SessionEvent,
  AudioDataEvent,
  Parameters as VoiceAssistantParameters
};