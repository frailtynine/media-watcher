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
  link?: string;
  relevant_news?: string[];
  non_relevant_news?: string[];
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
  BTC: "bitcoin",
  TON: "toncoin",
  ETH: "ethereum",
  DOGE: "dogecoin",
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

export interface Event {
  id: string;
  title: string;
  description: string;
  created_at: string;
  results_at: string;
  ends_at: string;
  false_positives: Array<Record<string, any>>;
  positives: Array<Record<string, any>>;
  rules: string;
  is_active: boolean;
}

export interface PromptExample {
  example: string;
}

export interface Prompt {
  id: number;
  role: string;
  crypto_role: string;
  suggest_post: string;
  post_examples: string[];
}

export interface Settings {
  deepseek: string | null;
  deepl: string | null;
  rss_urls: Record<string, string>;
  tg_urls: Record<string, string>;
}

 export interface ApiSettings {
  deepseek: string | null;
  deepl: string | null;
 }