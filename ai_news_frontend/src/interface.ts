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
  rss_urls: Record<string, string>;
  tg_urls: Record<string, string>;
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
  rss_urls: Record<string, string>;
  tg_urls: Record<string, string>;
}

export interface Sources {
  rss_urls: Record<string, string>;
  tg_urls: Record<string, string>;
}

 export interface ApiSettings {
  deepseek: string | null;
 }