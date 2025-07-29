'use client';

import React from 'react';
import { WaveRiderStoreProvider } from '@/store/waverider-store';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return <WaveRiderStoreProvider>{children}</WaveRiderStoreProvider>;
}
