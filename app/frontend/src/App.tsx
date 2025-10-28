import { useState } from "react";
import { Mic, MicOff, Settings, Phone, PhoneOff } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { GroundingFiles } from "@/components/ui/grounding-files";
import GroundingFileView from "@/components/ui/grounding-file-view";
import StatusMessage from "@/components/ui/status-message";

import useVoiceAssistant from "@/hooks/useVoiceAssistant";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";

import { GroundingFile, ToolResult } from "./types";

import logo from "./assets/logo.svg";

function App() {
    const [isRecording, setIsRecording] = useState(false);
    const [isSessionActive, setIsSessionActive] = useState(false);
    const [groundingFiles, setGroundingFiles] = useState<GroundingFile[]>([]);
    const [selectedFile, setSelectedFile] = useState<GroundingFile | null>(null);
    const [toolCalls, setToolCalls] = useState<Array<{
        id: string;
        function_name: string;
        status: 'started' | 'executing' | 'completed' | 'error';
        arguments?: any;
        result?: any;
        error?: string;
        execution_time?: number;
        timestamp: number;
    }>>([]);
    const [assistantResponse, setAssistantResponse] = useState<string>("");

    const {
        isConnected,
        startSession,
        stopSession,
        sendAudio,
        interruptAssistant
    } = useVoiceAssistant({
        serverUrl: 'ws://localhost:8000', // Your backend WebSocket server
        onWebSocketOpen: () => {
            console.log("WebSocket connection opened to voice assistant");
        },
        onWebSocketClose: () => {
            console.log("WebSocket connection closed");
            setIsSessionActive(false);
        },
        onWebSocketError: (event) => {
            console.error("WebSocket error:", event);
        },
        onSessionStarted: (event) => {
            console.log("Voice session started:", event);
            setIsSessionActive(true);
            setAssistantResponse("");
        },
        onSessionStopped: (event) => {
            console.log("Voice session stopped:", event);
            setIsSessionActive(false);
        },
        onSessionError: (event) => {
            console.error("Session error:", event);
            setIsSessionActive(false);
        },
        onSpeechStarted: () => {
            console.log("User started speaking");
            stopAudioPlayer();
        },
        onSpeechStopped: () => {
            console.log("User stopped speaking");
        },
        onResponseTextDelta: (event) => {
            // Accumulate text response from assistant
            setAssistantResponse(prev => prev + (event.text || ""));
        },
        onResponseAudioDelta: (event) => {
            // Play audio if recording is active
            if (isRecording && event.data?.has_audio) {
                // Note: You might need to handle audio playback differently
                // since we're not getting the actual audio data in WebSocket events
                console.log("Received audio delta");
            }
        },
        onResponseDone: () => {
            console.log("Response completed");
        },
        onToolCallStarted: (event) => {
            console.log(`Tool call started: ${event.function_name}`);
            setToolCalls(prev => [...prev, {
                id: event.call_id,
                function_name: event.function_name,
                status: 'started',
                timestamp: event.timestamp
            }]);
        },
        onToolCallArguments: (event) => {
            console.log(`Tool arguments received:`, event.arguments);
            setToolCalls(prev => prev.map(call => 
                call.id === event.call_id 
                    ? { ...call, arguments: event.arguments }
                    : call
            ));
        },
        onToolCallExecuting: (event) => {
            console.log(`Executing tool: ${event.function_name}`);
            setToolCalls(prev => prev.map(call => 
                call.id === event.call_id 
                    ? { ...call, status: 'executing' }
                    : call
            ));
        },
        onToolCallCompleted: (event) => {
            console.log(`Tool completed: ${event.function_name}`, event.result);
            setToolCalls(prev => prev.map(call => 
                call.id === event.call_id 
                    ? { 
                        ...call, 
                        status: 'completed', 
                        result: event.result,
                        execution_time: event.execution_time
                    }
                    : call
            ));

            // Handle grounding files if the result contains sources
            if (event.result && typeof event.result === 'object' && event.result.sources) {
                const files: GroundingFile[] = event.result.sources.map((x: any) => ({
                    id: x.chunk_id || x.id,
                    name: x.title || x.name,
                    content: x.chunk || x.content
                }));
                setGroundingFiles(prev => [...prev, ...files]);
            }
        },
        onToolCallError: (event) => {
            console.error(`Tool error: ${event.function_name}`, event.error);
            setToolCalls(prev => prev.map(call => 
                call.id === event.call_id 
                    ? { ...call, status: 'error', error: event.error }
                    : call
            ));
        },
        onAssistantInterrupted: () => {
            console.log("Assistant interrupted");
            stopAudioPlayer();
        },
        onError: (event) => {
            console.error("Voice assistant error:", event);
        }
    });

    const { reset: resetAudioPlayer, play: playAudio, stop: stopAudioPlayer } = useAudioPlayer();
    const { start: startAudioRecording, stop: stopAudioRecording } = useAudioRecorder({ 
        onAudioRecorded: sendAudio 
    });

    const onToggleSession = async () => {
        if (!isSessionActive) {
            // Start voice session
            await startSession({
                model: 'gpt-4o-realtime',
                voice: 'pt-BR-FranciscaNeural'
            });
            setGroundingFiles([]);
            setToolCalls([]);
        } else {
            // Stop voice session
            await stopSession();
            if (isRecording) {
                await stopAudioRecording();
                setIsRecording(false);
            }
        }
    };

    const onToggleListening = async () => {
        if (!isRecording && isSessionActive) {
            await startAudioRecording();
            resetAudioPlayer();
            setIsRecording(true);
        } else if (isRecording) {
            await stopAudioRecording();
            stopAudioPlayer();
            setIsRecording(false);
        }
    };

    const onInterrupt = () => {
        interruptAssistant();
        stopAudioPlayer();
    };

    const { t } = useTranslation();

    return (
        <div className="flex min-h-screen flex-col bg-gray-100 text-gray-900">
            <div className="p-4 sm:absolute sm:left-4 sm:top-4">
                <img src={logo} alt="Azure logo" className="h-16 w-16" />
            </div>
            
            {/* Connection status */}
            <div className="absolute top-4 right-4 flex items-center gap-2">
                <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm">
                    {isConnected ? 'Connected' : 'Disconnected'}
                </span>
            </div>

            <main className="flex flex-grow flex-col items-center justify-center px-4">
                <h1 className="mb-8 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-4xl font-bold text-transparent md:text-7xl text-center">
                    {t("app.title")}
                </h1>

                {/* Session Controls */}
                <div className="mb-6 flex flex-col items-center gap-4">
                    <Button
                        onClick={onToggleSession}
                        disabled={!isConnected}
                        className={`h-12 w-60 ${
                            isSessionActive 
                                ? "bg-red-600 hover:bg-red-700" 
                                : "bg-blue-600 hover:bg-blue-700"
                        }`}
                    >
                        {isSessionActive ? (
                            <>
                                <PhoneOff className="mr-2 h-4 w-4" />
                                End Session
                            </>
                        ) : (
                            <>
                                <Phone className="mr-2 h-4 w-4" />
                                Start Voice Session
                            </>
                        )}
                    </Button>

                    {/* Recording Controls */}
                    {isSessionActive && (
                        <div className="flex gap-2">
                            <Button
                                onClick={onToggleListening}
                                className={`h-12 w-40 ${
                                    isRecording 
                                        ? "bg-red-600 hover:bg-red-700" 
                                        : "bg-purple-500 hover:bg-purple-600"
                                }`}
                                aria-label={isRecording ? t("app.stopRecording") : t("app.startRecording")}
                            >
                                {isRecording ? (
                                    <>
                                        <MicOff className="mr-2 h-4 w-4" />
                                        Stop Listening
                                    </>
                                ) : (
                                    <>
                                        <Mic className="mr-2 h-6 w-6" />
                                        Start Listening
                                    </>
                                )}
                            </Button>

                            <Button
                                onClick={onInterrupt}
                                variant="outline"
                                className="h-12 w-20"
                                disabled={!isRecording}
                            >
                                Interrupt
                            </Button>
                        </div>
                    )}

                    <StatusMessage isRecording={isRecording} />
                </div>

                {/* Assistant Response */}
                {assistantResponse && (
                    <div className="mb-6 max-w-2xl rounded-lg bg-white p-4 shadow-md">
                        <h3 className="mb-2 font-semibold">Assistant Response:</h3>
                        <p className="text-gray-700">{assistantResponse}</p>
                    </div>
                )}

                {/* Tool Calls Display */}
                {toolCalls.length > 0 && (
                    <div className="mb-6 max-w-2xl rounded-lg bg-white p-4 shadow-md">
                        <h3 className="mb-2 font-semibold">Function Calls:</h3>
                        <div className="space-y-2">
                            {toolCalls.map((call) => (
                                <div key={call.id} className="flex items-center gap-2 text-sm">
                                    <div className={`h-2 w-2 rounded-full ${
                                        call.status === 'completed' ? 'bg-green-500' :
                                        call.status === 'error' ? 'bg-red-500' :
                                        call.status === 'executing' ? 'bg-yellow-500' :
                                        'bg-blue-500'
                                    }`} />
                                    <span className="font-medium">{call.function_name}</span>
                                    <span className="text-gray-500">({call.status})</span>
                                    {call.execution_time && (
                                        <span className="text-xs text-gray-400">
                                            {call.execution_time.toFixed(0)}ms
                                        </span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <GroundingFiles files={groundingFiles} onSelected={setSelectedFile} />
            </main>

            <footer className="py-4 text-center">
                <p>{t("app.footer")}</p>
            </footer>

            <GroundingFileView groundingFile={selectedFile} onClosed={() => setSelectedFile(null)} />
        </div>
    );
}

export default App;