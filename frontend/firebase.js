import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { initializeAuth, getReactNativePersistence, GoogleAuthProvider } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

const firebaseConfig = {
  apiKey: "AIzaSyA9IBWvLEmeiLwt5ViPIpaJykCIaxKIcm4",
  authDomain: "slop-app.firebaseapp.com",
  projectId: "slop-app",
  storageBucket: "slop-app.firebasestorage.app",
  messagingSenderId: "782070599615",
  appId: "1:782070599615:ios:21b6814c6c85b3d1635b0a"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services with AsyncStorage for persistent auth
export const db = getFirestore(app);
export const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage)
});

// Initialize Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.addScope('email');
googleProvider.addScope('profile');

export default app;