'use client';

import { useEffect, useState } from 'react';

export type MicPermissionState = 'unknown' | 'granted' | 'denied' | 'prompt';

/**
 * Tracks microphone permission state.
 * Returns the current state and a helper to request permission explicitly.
 */
export function useMicPermission() {
  const [permissionState, setPermissionState] = useState<MicPermissionState>('unknown');

  useEffect(() => {
    if (typeof navigator === 'undefined' || !navigator.permissions) {
      // Permissions API not supported — assume prompt
      setPermissionState('prompt');
      return;
    }

    navigator.permissions
      .query({ name: 'microphone' as PermissionName })
      .then((status) => {
        setPermissionState(status.state as MicPermissionState);

        status.onchange = () => {
          setPermissionState(status.state as MicPermissionState);
        };
      })
      .catch(() => {
        setPermissionState('prompt');
      });
  }, []);

  const requestMicPermission = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop all tracks immediately — we just wanted the permission
      stream.getTracks().forEach((track) => track.stop());
      setPermissionState('granted');
      return true;
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setPermissionState('denied');
      }
      return false;
    }
  };

  return { permissionState, requestMicPermission };
}
