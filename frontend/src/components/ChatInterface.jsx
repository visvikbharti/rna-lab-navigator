import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  PaperAirplaneIcon, 
  DocumentTextIcon, 
  BeakerIcon,
  AcademicCapIcon,
  SparklesIcon,
  ChevronDownIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { PaperAirplaneIcon as PaperAirplaneSolidIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { nightOwl } from 'react-syntax-highlighter/dist/esm/styles/prism';

const ChatInterface = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSessions, setShowSessions] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadSessions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/chat/sessions/');
      const data = await response.json();
      setSessions(data.sessions || []);
      
      // Load the most recent session if available
      if (data.sessions?.length > 0 && !currentSessionId) {
        loadSession(data.sessions[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/chat/sessions/${sessionId}/`);
      const data = await response.json();
      setMessages(data.messages || []);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/chat/sessions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' })
      });
      
      const data = await response.json();
      await loadSessions();
      loadSession(data.session.id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentSessionId || isLoading) return;

    const message = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Add user message immediately
    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(
        `http://localhost:8000/api/chat/sessions/${currentSessionId}/messages/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: message })
        }
      );

      const data = await response.json();
      
      // Update messages with server response
      setMessages(prev => [
        ...prev.filter(m => m.id !== userMessage.id),
        data.user_message,
        data.assistant_message
      ]);

      // Update session in list
      if (data.session) {
        setSessions(prev => prev.map(s => 
          s.id === currentSessionId ? data.session : s
        ));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await fetch(`http://localhost:8000/api/chat/sessions/${sessionId}/`, {
        method: 'DELETE'
      });
      
      await loadSessions();
      
      // If deleting current session, switch to another
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const getMessageIcon = (role) => {
    if (role === 'user') return null;
    return <SparklesIcon className="w-5 h-5 text-blue-500" />;
  };

  const formatSources = (metadata) => {
    if (!metadata?.sources?.length) return null;
    
    return (
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sources:</h4>
        <div className="space-y-1">
          {metadata.sources.map((source, idx) => (
            <div key={idx} className="flex items-start text-xs text-gray-600 dark:text-gray-400">
              <DocumentTextIcon className="w-4 h-4 mr-1 flex-shrink-0 mt-0.5" />
              <span>
                {source.title} by {source.author} ({source.year})
                {source.type === 'thesis' && <AcademicCapIcon className="w-3 h-3 inline ml-1" />}
                {source.type === 'protocol' && <BeakerIcon className="w-3 h-3 inline ml-1" />}
              </span>
            </div>
          ))}
        </div>
        {metadata.confidence_score && (
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Confidence: {(metadata.confidence_score * 100).toFixed(0)}%
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sessions Sidebar */}
      <AnimatePresence>
        {showSessions && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col"
          >
            {/* New Chat Button */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <button
                onClick={createNewSession}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <PlusIcon className="w-5 h-5" />
                New Chat
              </button>
            </div>

            {/* Sessions List */}
            <div className="flex-1 overflow-y-auto">
              {sessions.length === 0 ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  No conversations yet
                </div>
              ) : (
                <div className="space-y-1 p-2">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                        session.id === currentSessionId
                          ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                      onClick={() => loadSession(session.id)}
                    >
                      <h3 className="font-medium text-sm text-gray-900 dark:text-white pr-8">
                        {session.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(session.updated_at).toLocaleDateString()}
                      </p>
                      
                      {/* Delete button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <TrashIcon className="w-4 h-4 text-gray-400 hover:text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ChevronDownIcon 
                className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform ${
                  showSessions ? 'rotate-90' : ''
                }`} 
              />
            </button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              RNA Lab Navigator
            </h1>
          </div>
          
          <div className="text-sm text-gray-500 dark:text-gray-400">
            AI-powered research assistant
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 ? (
            <div className="max-w-3xl mx-auto text-center py-12">
              <SparklesIcon className="w-12 h-12 mx-auto text-blue-500 mb-4" />
              <h2 className="text-2xl font-semibold text-gray-100 mb-2">
                Welcome to RNA Lab Navigator
              </h2>
              <p className="text-gray-300 mb-8">
                Ask me anything about research papers, protocols, and theses from Dr. Chakraborty's lab.
              </p>
              
              {/* Example queries */}
              <div className="grid md:grid-cols-2 gap-4 text-left">
                {[
                  "What DNA repair mechanisms are studied in Rhythm Phutela's thesis?",
                  "How does the RAPID FnCas9 system work for COVID detection?",
                  "What is the protocol for RNA extraction using Trizol?",
                  "Compare NHEJ and HDR repair mechanisms"
                ].map((query, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputMessage(query)}
                    className="p-4 bg-gray-800 border border-gray-600 rounded-lg hover:border-blue-500 transition-colors text-sm text-gray-200 hover:text-white"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-4 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      {getMessageIcon(message.role)}
                    </div>
                  )}
                  
                  <div className={`flex-1 max-w-xl ${
                    message.role === 'user' ? 'text-right' : ''
                  }`}>
                    <div className={`inline-block p-4 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                    }`}>
                      {message.role === 'assistant' ? (
                        <>
                          <ReactMarkdown
                            components={{
                              code({node, inline, className, children, ...props}) {
                                const match = /language-(\w+)/.exec(className || '');
                                return !inline && match ? (
                                  <SyntaxHighlighter
                                    style={nightOwl}
                                    language={match[1]}
                                    PreTag="div"
                                    {...props}
                                  >
                                    {String(children).replace(/\n$/, '')}
                                  </SyntaxHighlighter>
                                ) : (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                );
                              }
                            }}
                            className="prose prose-sm dark:prose-invert max-w-none"
                          >
                            {message.content}
                          </ReactMarkdown>
                          {formatSources(message.metadata)}
                        </>
                      ) : (
                        <p className="whitespace-pre-wrap text-white">{message.content}</p>
                      )}
                    </div>
                    
                    <div className={`text-xs text-gray-500 dark:text-gray-400 mt-1 ${
                      message.role === 'user' ? 'text-right' : ''
                    }`}>
                      {new Date(message.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                  
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                      U
                    </div>
                  )}
                </motion.div>
              ))}
              
              {/* Loading indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-4"
                >
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                    <SparklesIcon className="w-5 h-5 text-blue-500 animate-pulse" />
                  </div>
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-4">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="max-w-3xl mx-auto">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask about research papers, protocols, or theses..."
                className="w-full px-4 py-3 pr-12 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading || !currentSessionId}
              />
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim() || !currentSessionId}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-blue-600 hover:text-blue-700 disabled:text-gray-400 transition-colors"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <PaperAirplaneSolidIcon className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
              Press Enter to send • Shift+Enter for new line
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;