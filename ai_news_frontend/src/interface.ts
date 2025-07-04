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