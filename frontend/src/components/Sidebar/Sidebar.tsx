import React from 'react';
import Link from 'next/link';

export default function Sidebar() {
  return (
    <nav className="bg-gray-100 p-6 h-full">
      <h2 className="text-2xl font-bold mb-6">PollySystem</h2>
      <ul className="space-y-4">
        <li>
          <Link href="/" className="text-gray-700 hover:text-black hover:underline font-medium">
            Status
          </Link>
        </li>
        <li>
          <Link href="/machines" className="text-gray-700 hover:text-black hover:underline font-medium">
            Hosts
          </Link>
        </li>
      </ul>
    </nav>
  );
}

