import { useEffect, useState } from 'react';

const REFRESH_EVENT = 'nexusiq:workspace-refresh';

export const emitWorkspaceRefresh = (caseId?: string) => {
  if (!caseId) return;

  const timestamp = Date.now();
  const detail = { caseId, timestamp };

  window.localStorage.setItem(`nexusiq:workspace-refresh:${caseId}`, String(timestamp));
  window.dispatchEvent(new CustomEvent(REFRESH_EVENT, { detail }));
};

export const useWorkspaceRefresh = (caseId?: string) => {
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!caseId) return;

    const bump = () => setRefreshKey((current) => current + 1);

    const handleRefresh = (event: Event) => {
      const detail = (event as CustomEvent).detail;
      if (detail?.caseId === caseId) bump();
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === `nexusiq:workspace-refresh:${caseId}`) bump();
    };

    window.addEventListener(REFRESH_EVENT, handleRefresh);
    window.addEventListener('storage', handleStorage);

    return () => {
      window.removeEventListener(REFRESH_EVENT, handleRefresh);
      window.removeEventListener('storage', handleStorage);
    };
  }, [caseId]);

  return refreshKey;
};
