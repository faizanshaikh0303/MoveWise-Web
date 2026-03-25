import { create } from 'zustand';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: { tool: string; args: Record<string, unknown> }[];
}

interface ChatState {
  messages: ChatMessage[];
  isOpen: boolean;
  setOpen: (open: boolean) => void;
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isOpen: false,
  setOpen: (open) => set({ isOpen: open }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),
  clearChat: () => set({ messages: [], isOpen: false }),
}));
