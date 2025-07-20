import type { ApiUser } from "./api";


export interface News {
  title: string;
  link: string;
  description: string | null;
  pub_date: string;
}

export interface NewsTaskCreate {
  title: string;
  description: string;
  end_date: string;
}

export interface NewsTask extends NewsTaskCreate{
  id: number;
  is_active: boolean;
  created_at: string;
  positives: News[];
  false_positives: News[];
  user: ApiUser;
}

interface NewsTaskRedis extends NewsTaskCreate {
  id: number;
  is_active: boolean;
  created_at: string;
  positives: News[];
  false_positives: News[];
  user_id: string;
  result: boolean;
}


export interface RedisMessage {
  news: News;
  task: NewsTaskRedis
}

// Crypto Task Types
export const CryptoTaskType = {
  UP: "up",
  DOWN: "down",
  PRICE: "price"
} as const;

export type CryptoTaskType = typeof CryptoTaskType[keyof typeof CryptoTaskType];

export const CryptoTickersType = {
  SOL: "solana",
  BTC: "bitcoin",
  TON: "toncoin"
}

export type CryptoTickersType = typeof CryptoTickersType[keyof typeof CryptoTickersType];


export interface CryptoTaskCreate {
  title: string;
  description?: string;
  end_date: string;
  start_date?: string;
  start_point?: number;
  end_point: number;
  measurement_time: string;
  ticker: string;
  type: CryptoTaskType;
}

export interface CryptoTask extends CryptoTaskCreate {
  id: number;
  is_active: boolean;
  created_at: string;
  user_id: string;
}