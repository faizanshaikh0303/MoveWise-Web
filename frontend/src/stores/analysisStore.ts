import { create } from 'zustand';
import type { AnalysisSummary } from '@/types';
import { analysisAPI } from '@/services/api';

interface AnalysisState {
  analyses: AnalysisSummary[];
  fetched: boolean;
  fetchAnalyses: () => Promise<void>;
  prependAnalysis: (analysis: AnalysisSummary) => void;
  markCompleted: (id: number) => void;
  clearAnalyses: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  analyses: [],
  fetched: false,

  fetchAnalyses: async () => {
    const data = await analysisAPI.getAll();
    set({ analyses: data, fetched: true });
  },

  prependAnalysis: (analysis) =>
    set((state) => ({ analyses: [analysis, ...state.analyses] })),

  markCompleted: (id) =>
    set((state) => ({
      analyses: state.analyses.map((a) =>
        a.id === id ? { ...a, status: 'completed' as const } : a
      ),
    })),

  clearAnalyses: () => set({ analyses: [], fetched: false }),
}));
