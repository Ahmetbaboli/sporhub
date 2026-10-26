import { notFound } from "next/navigation";
import { ApiError } from "@/lib/api";

/** Awaits an API call, turning a 404 envelope into Next's notFound(); other errors bubble up. */
export async function orNotFound<T>(request: Promise<T>): Promise<T> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
}

/** Parses a positive integer route/query value; non-numeric input is a 404. */
export function parseId(value: string): number {
  if (!/^\d+$/.test(value)) notFound();
  return Number(value);
}

export function parsePage(value: string | string[] | undefined): number {
  const n = Number(Array.isArray(value) ? value[0] : value);
  return Number.isInteger(n) && n >= 1 ? n : 1;
}
