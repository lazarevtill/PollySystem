import '../../styles/globals.css';
import type { AppProps } from 'next/app';
import Sidebar from '../components/Sidebar/Sidebar';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <Component {...pageProps} />
      </main>
    </div>
  );
}

