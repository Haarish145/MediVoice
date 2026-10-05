import { useState, useCallback } from "react";
import { createSession } from "../services/api";

export function useSession() {
  const [session, setSession] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState(null);

  const startSession = useCallback(async (language, patientName = "", facility = "") => {
    setIsCreating(true);
    setError(null);
    try {
      const data = await createSession(language, patientName, facility);
      setSession(data);
      return data;
    } catch (err) {
      setError("Failed to create session. Is the backend running?");
      return null;
    } finally {
      setIsCreating(false);
    }
  }, []);

  const clearSession = useCallback(() => {
    setSession(null);
    setError(null);
  }, []);

  return { session, isCreating, error, startSession, clearSession };
}
