import axios from 'axios';

import { API_BASE_URL } from '@/config/api';

export type RegisterPayload = {
  full_name?: string;
  email: string;
  password: string;
};

export type RegisterResponse = {
  message: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: 'bearer';
};

export type ChatResponse = {
  answer: string;
};

export type KpiSummary = {
  total_sales: number;
  total_profit: number;
  margin_pct: number | null;
  total_orders: number;
};

export type SalesTimeSeriesPoint = {
  period: string;
  total_sales: number;
};

export type SalesTimeseriesResponse = {
  series: SalesTimeSeriesPoint[];
};

export type ReportResponse = {
  title: string;
  summary: string;
  key_points: string[];
};

type ReportAgentApiResponse = Partial<ReportResponse> & {
  error?: string;
};

/**
 * Client HTTP unique de l'application.
 * Les futurs appels protégés (dont /chat) ajouteront leur JWT ici ou par requête.
 */
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  const response = await api.post<RegisterResponse>('/auth/register', payload);
  return response.data;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/login', payload);
  return response.data;
}

/** Récupère les indicateurs globaux du dashboard avec le JWT courant. */
export async function getKpiSummary(token: string): Promise<KpiSummary> {
  const response = await api.get<KpiSummary>('/data/kpis/summary', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

/** Récupère les ventes mensuelles réelles du dashboard avec le JWT courant. */
export async function getSalesTimeseries(token: string): Promise<SalesTimeSeriesPoint[]> {
  const response = await api.get<SalesTimeseriesResponse>('/data/sales/timeseries', {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!Array.isArray(response.data.series)) {
    throw new Error('Série de ventes invalide reçue du serveur.');
  }

  return response.data.series;
}

/** Demande au Report Agent une synthèse de résultats BI réels. */
export async function generateReport(results: string, token: string): Promise<ReportResponse> {
  const response = await api.post<ReportAgentApiResponse>(
    '/agents/report',
    { results },
    {
      // Le Report Agent appelle Ollama, comme le Chat : ce seul appel reçoit un délai étendu.
      timeout: 90_000,
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  if (typeof response.data.error === 'string') {
    throw new Error(response.data.error);
  }

  if (typeof response.data.title !== 'string' || typeof response.data.summary !== 'string') {
    throw new Error('Le Report Agent a renvoyé un rapport incomplet.');
  }

  return {
    title: response.data.title,
    summary: response.data.summary,
    key_points: Array.isArray(response.data.key_points)
      ? response.data.key_points.filter((point): point is string => typeof point === 'string')
      : [],
  };
}

/** Envoie une question à l'orchestrateur via la route FastAPI protégée. */
export async function sendChatMessage(question: string, token: string): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>(
    '/chat',
    { question },
    {
      // L'Orchestrator peut devoir charger Ollama et appeler un agent BI :
      // seul /chat bénéficie donc d'un délai plus long que les routes d'authentification.
      timeout: 130_000,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (typeof response.data.answer !== 'string') {
    throw new Error('Réponse invalide reçue du serveur.');
  }

  return response.data;
}
