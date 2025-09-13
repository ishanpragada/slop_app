import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { setAudioModeAsync } from 'expo-audio';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { addDoc, collection, serverTimestamp } from 'firebase/firestore';
import { useEffect } from 'react';
import 'react-native-reanimated';
import '../firebase'; // Import Firebase
import { db } from '../firebase';

import { useColorScheme } from '@/hooks/useColorScheme';
import { AuthProvider } from '../contexts/AuthContext';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const [loaded] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
  });

  // Initialize audio session and test Firebase connection
  useEffect(() => {
    const initializeApp = async () => {
      // Configure audio session for video playback
      try {
        await setAudioModeAsync({
          allowsRecording: false,
          playsInSilentMode: true,
        });
        console.log('✅ Audio session configured for video playback');
      } catch (error) {
        console.error('❌ Audio session configuration error:', error);
      }

      // Test Firebase connection
      try {
        await addDoc(collection(db, 'test'), {
          message: 'Firebase is working!',
          timestamp: serverTimestamp(),
          testDate: new Date(),
          appName: 'Slop'
        });
        console.log('✅ Firebase connection successful!');
      } catch (error) {
        console.error('❌ Firebase error:', error);
      }
    };

    initializeApp();
  }, []);

  if (!loaded) {
    // Async font loading only occurs in development.
    return null;
  }

  return (
    <AuthProvider>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="+not-found" />
        </Stack>
        <StatusBar style="auto" />
      </ThemeProvider>
    </AuthProvider>
  );
}
