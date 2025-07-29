'use client';

import WaveRiderIDE from '@/components/ide/waverider-ide';
import { Landing } from '@/components/landing/landing';
import { useWaveRiderStore } from '@/store/waverider-store';
import { useEffect } from 'react';

export default function HomePage() {
  const { user, initialized, initialize } = useWaveRiderStore();

  useEffect(() => {
    if (!initialized) {
      initialize();
    }
  }, [initialized, initialize]);

  if (!initialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Initializing WaveRider...</p>
        </div>
      </div>
    );
  }

  // Show landing page for new users, IDE for authenticated users
  if (!user) {
    return <Landing />;
  }

  return <WaveRiderIDE />;
}
