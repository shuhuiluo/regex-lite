export type Span = [number, number];

export interface Match {
  span: Span;
  groups: (Span | null)[];
}

export interface MatchResponse {
  matches: Match[];
}

export interface MatchRequest {
  pattern: string;
  flags: string;
  text: string;
}

const DEFAULT_API_BASE = "http://localhost:8000";

function resolveApiBase(): string {
  const configuredBase = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configuredBase && configuredBase.length > 0) {
    return configuredBase.replace(/\/$/, "");
  }

  return DEFAULT_API_BASE;
}

async function parseJsonSafely<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function match(request: MatchRequest): Promise<MatchResponse> {
  try {
    const response = await fetch(`${resolveApiBase()}/regex/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const payload = await parseJsonSafely<{ detail?: string }>(response);
      const message = payload?.detail ?? `Request failed with status ${response.status}`;
      throw new Error(message);
    }

    const payload = await parseJsonSafely<MatchResponse>(response);
    if (!payload) {
      throw new Error("The server response could not be parsed as JSON.");
    }

    return {
      matches: payload.matches ?? [],
    };
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }

    throw new Error("Unexpected error while communicating with the API.");
  }
}
