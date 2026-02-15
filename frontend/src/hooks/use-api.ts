"use client";

import { useState, useEffect, useCallback, useRef } from "react";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Hook for fetching data from the Control Tower API.
 * Handles loading, error, and refetch states.
 *
 * @param fetcher  Async function that returns data
 * @param fallback Optional fallback data when API is unreachable
 * @param deps     Dependency array for re-fetching
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  fallback?: T,
  deps: any[] = []
): UseApiState<T> {
  const [data, setData] = useState<T | null>(fallback ?? null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (mountedRef.current) {
        setData(result);
      }
    } catch (err: any) {
      if (mountedRef.current) {
        setError(err.message || "An error occurred");
        // Keep fallback data if API fails
        if (fallback && !data) {
          setData(fallback);
        }
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook for API mutations (POST, PATCH, DELETE).
 */
export function useMutation<TInput, TOutput>(
  mutator: (input: TInput) => Promise<TOutput>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (input: TInput): Promise<TOutput | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await mutator(input);
        return result;
      } catch (err: any) {
        setError(err.message || "Mutation failed");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [mutator]
  );

  return { execute, loading, error };
}
