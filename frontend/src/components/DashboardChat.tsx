import { useState, useRef, useEffect } from 'react';
import { X, Send, Sparkles, Search, BarChart2, Trophy } from 'lucide-react';
import { chatAPI } from '../services/api';
import { useChatStore } from '../stores/chatStore';
import type { ChatMessage as Message } from '../stores/chatStore';

const TOOL_LABELS: Record<string, string> = {
  get_analysis_details: 'Reading analysis details…',
  compare_analyses: 'Comparing destinations…',
  rank_analyses: 'Ranking your analyses…',
};

const TOOL_ICONS: Record<string, typeof Search> = {
  get_analysis_details: Search,
  compare_analyses: BarChart2,
  rank_analyses: Trophy,
};

const STARTERS = [
  'Which move saves me the most money?',
  'Which destination is safest?',
  'Compare all my analyses',
  'What is the best overall move?',
];

export default function DashboardChat() {
  const { messages, isOpen: open, setOpen, setMessages } = useChatStore();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: 'user', content: trimmed };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);

    try {
      const history = nextMessages.map((m) => ({ role: m.role, content: m.content }));
      const { reply, tool_calls } = await chatAPI.send(trimmed, history.slice(0, -1));
      setMessages([...nextMessages, { role: 'assistant', content: reply, toolCalls: tool_calls }]);
    } catch {
      setMessages([
        ...nextMessages,
        { role: 'assistant', content: 'Something went wrong. Please try again.' },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 flex items-center justify-center"
        aria-label="Open AI advisor"
      >
        {open ? <X className="w-6 h-6" /> : <Sparkles className="w-6 h-6" />}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-[380px] max-h-[560px] flex flex-col rounded-2xl shadow-2xl border border-white/20 overflow-hidden bg-gray-900">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-white font-semibold text-sm leading-none">MoveWise AI</p>
              <p className="text-indigo-200 text-xs mt-0.5">Ask about your analyses</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            {messages.length === 0 && (
              <div className="space-y-3">
                <p className="text-gray-400 text-xs text-center">Ask anything about your saved analyses</p>
                <div className="grid grid-cols-1 gap-2">
                  {STARTERS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="text-left text-xs px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors border border-gray-700"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] space-y-1.5`}>
                  {/* Tool call badges */}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-1">
                      {msg.toolCalls.map((tc, j) => {
                        const Icon = TOOL_ICONS[tc.tool] || Search;
                        return (
                          <span
                            key={j}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-900/60 text-indigo-300 text-[10px] border border-indigo-700/40"
                          >
                            <Icon className="w-2.5 h-2.5" />
                            {TOOL_LABELS[tc.tool] || tc.tool}
                          </span>
                        );
                      })}
                    </div>
                  )}

                  <div
                    className={`px-3 py-2 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-sm'
                        : 'bg-gray-800 text-gray-100 rounded-bl-sm'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="px-3 py-2 rounded-2xl rounded-bl-sm bg-gray-800">
                  <div className="flex gap-1 items-center h-4">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="flex-shrink-0 border-t border-gray-700 px-3 py-3 flex gap-2 bg-gray-900">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send(input)}
              placeholder="Ask about your analyses…"
              disabled={loading}
              className="flex-1 bg-gray-800 text-gray-100 placeholder-gray-500 text-sm rounded-xl px-3 py-2 outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
            <button
              onClick={() => send(input)}
              disabled={loading || !input.trim()}
              className="w-9 h-9 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-colors flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
