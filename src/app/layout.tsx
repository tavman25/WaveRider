import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Toaster } from 'react-hot-toast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'WaveRider - Agentic AI IDE',
  description:
    'An AI-native code editor with autonomous agents for planning, coding, debugging, and optimization',
  keywords: ['AI', 'IDE', 'code editor', 'autonomous agents', 'development'],
  authors: [{ name: 'WaveRider Team' }],
  openGraph: {
    title: 'WaveRider - Agentic AI IDE',
    description: 'Revolutionizing development with AI-powered autonomous coding agents',
    url: 'https://waverider.dev',
    siteName: 'WaveRider',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'WaveRider AI IDE',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'WaveRider - Agentic AI IDE',
    description: 'Revolutionizing development with AI-powered autonomous coding agents',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
          <Toaster
            position="bottom-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'hsl(var(--card))',
                color: 'hsl(var(--card-foreground))',
                border: '1px solid hsl(var(--border))',
              },
              success: {
                iconTheme: {
                  primary: 'hsl(var(--primary))',
                  secondary: 'hsl(var(--primary-foreground))',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
