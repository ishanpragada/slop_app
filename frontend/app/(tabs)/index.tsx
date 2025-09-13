import { TikTokApp } from '@/components/TikTokApp';
import React from 'react';

export default function HomeScreen() {
  // Temporarily bypass authentication to show TikTok UI
  return <TikTokApp />;
}
