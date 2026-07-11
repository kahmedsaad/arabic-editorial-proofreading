import type { Article } from "./types";
import { ARTICLES } from "@/data/seed";
import { getState } from "./store";

export function findArticle(id: string): Article | undefined {
  const seed = ARTICLES.find((a) => a.article_id === id);
  if (seed) return seed;
  return getState().customArticles?.find((a) => a.article_id === id);
}

export function allArticles(): Article[] {
  return [...ARTICLES, ...(getState().customArticles ?? [])];
}

export function isCustomArticle(id: string): boolean {
  return !ARTICLES.some((a) => a.article_id === id);
}