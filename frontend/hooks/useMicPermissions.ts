'use client';

import { useState, useEffect, useCallback } from 'react';

export function useMicPermissions() {
  const [permissionState, setPermissionState] = useState<'prompt' | 'granted' | 'denied' | 'unknown'>('unknown');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const checkPermission = useCallback(async () => {
    try {
      if (typeof navigator !== 'undefined' && navigator.permissions) {
        const result = await navigator.permissions.query({ name: 'microphone' as PermissionName });
        setPermissionState(result.state as 'prompt' | 'granted' | 'denied');
        
        result.onchange = () => {
          setPermissionState(result.state as 'prompt' | 'granted' | 'denied');
        };
      }
    } catch {
      // Browser doesn't support microphone permission query
      setPermissionState('unknown');
    }
  }, []);

  const requestMic = useCallback(async () => {
    try {
      setErrorMessage(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop stream immediately after permission granted
      stream.getTracks().forEach((track) => track.stop());
      setPermissionState('granted');
      return true;
    } catch (err: unknown) {
      const error = err as Error;
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        setPermissionState('denied');
        setErrorMessage('Microphone access was denied by browser settings.');
      } else if (error.name === 'NotFoundError') {
        setErrorMessage('No microphone input device found on your device.');
      } else {
        setErrorMessage(error.message || 'Failed to access microphone.');
      }
      return false;
    }
  }, []);

  useEffect(() => {
    checkPermission();
  }, [checkPermission]);

  return {
    permissionState,
    errorMessage,
    requestMic,
    checkPermission,
    setPermissionState,
  };
}
