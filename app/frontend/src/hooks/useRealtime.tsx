import useWebSocket from "react-use-websocket";
import { useCallback, useRef } from "react";

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
  };
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
  serverUrl = 'ws://localhost:8000',
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
  const wsEndpoint = `${serverUrl}/ws/${clientIdRef.current}`;

  const { sendJsonMessage, readyState } = useWebSocket(
    wsEndpoint,
    {
      onOpen: () => {
        console.log('WebSocket connected to voice assistant');
        onWebSocketOpen?.();
      },
      onClose: () => {
        console.log('WebSocket disconnected from voice assistant');
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
    sendJsonMessage({
      type: 'start_session',
      config: {
        model: 'gpt-4o-realtime',
        voice: 'pt-BR-FranciscaNeural',
        ...config
      }
    });
  }, [sendJsonMessage]);

  const stopSession = useCallback(() => {
    console.log('Stopping voice session');
    sendJsonMessage({
      type: 'stop_session'
    });
  }, [sendJsonMessage]);

  const sendAudio = useCallback((audioData: string) => {
    sendJsonMessage({
      type: 'send_audio',
      audio: audioData
    });
  }, [sendJsonMessage]);

  const interruptAssistant = useCallback(() => {
    console.log('Interrupting assistant');
    sendJsonMessage({
      type: 'interrupt'
    });
  }, [sendJsonMessage]);

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
    onError
  ]);

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
        break;
        
      case 'response.text.delta':
        onResponseTextDelta?.({
          ...voiceEvent,
          text: eventData.text
        });
        break;
        
      case 'response.audio.delta':
        onResponseAudioDelta?.(voiceEvent);
        break;
        
      case 'response.audio.done':
        onResponseAudioDone?.(voiceEvent);
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
    onError
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
    interruptAssistant,
    
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
  Parameters as VoiceAssistantParameters
};