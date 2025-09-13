import { addDoc, collection, doc, onSnapshot, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';

interface ConnectionStatus {
  isConnected: boolean;
  lastChecked: Date;
  error?: string;
}

let connectionStatus: ConnectionStatus = {
  isConnected: false,
  lastChecked: new Date(),
};

/**
 * Test Firebase connection with proper error handling and retry logic
 * This replaces the aggressive connection test in _layout.tsx
 */
export const testFirebaseConnection = async (retries: number = 3): Promise<boolean> => {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      // Use a lightweight operation instead of writing documents
      const testDocRef = doc(db, 'connection-test', 'status');
      
      // Set up a listener that will immediately indicate connection status
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 5000); // 5 second timeout

        const unsubscribe = onSnapshot(
          testDocRef,
          (snapshot) => {
            clearTimeout(timeout);
            unsubscribe();
            connectionStatus = {
              isConnected: true,
              lastChecked: new Date(),
            };
            console.log('✅ Firebase connection successful!');
            resolve(true);
          },
          (error) => {
            clearTimeout(timeout);
            unsubscribe();
            connectionStatus = {
              isConnected: false,
              lastChecked: new Date(),
              error: error.message,
            };
            
            if (attempt === retries) {
              console.error(`❌ Firebase connection failed after ${retries} attempts:`, error);
              reject(error);
            } else {
              console.warn(`⚠️ Firebase connection attempt ${attempt} failed, retrying...`);
              // Continue to next retry
            }
          }
        );
      });
    } catch (error) {
      connectionStatus = {
        isConnected: false,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error',
      };

      if (attempt === retries) {
        console.error(`❌ Firebase connection failed after ${retries} attempts:`, error);
        return false;
      }
      
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
  
  return false;
};

/**
 * Safe wrapper for Firestore write operations with built-in error handling
 */
export const safeFirestoreWrite = async <T>(
  collectionName: string,
  data: T,
  retries: number = 2
): Promise<{ success: boolean; docId?: string; error?: string }> => {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const docRef = await addDoc(collection(db, collectionName), {
        ...data,
        timestamp: serverTimestamp(),
        createdAt: new Date(),
      });

      return {
        success: true,
        docId: docRef.id,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      if (attempt === retries) {
        console.error(`❌ Firestore write failed after ${retries} attempts:`, error);
        return {
          success: false,
          error: errorMessage,
        };
      }
      
      console.warn(`⚠️ Firestore write attempt ${attempt} failed, retrying...`, errorMessage);
      
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }

  return {
    success: false,
    error: 'Max retries exceeded',
  };
};

/**
 * Get current connection status without making new requests
 */
export const getConnectionStatus = (): ConnectionStatus => {
  return { ...connectionStatus };
};

/**
 * Monitor Firebase connection status
 */
export const startConnectionMonitoring = (callback?: (status: ConnectionStatus) => void) => {
  // Check connection every 30 seconds if needed
  const interval = setInterval(async () => {
    const timeSinceLastCheck = Date.now() - connectionStatus.lastChecked.getTime();
    
    // Only check if we haven't checked recently or if we're disconnected
    if (timeSinceLastCheck > 30000 || !connectionStatus.isConnected) {
      try {
        await testFirebaseConnection(1); // Single attempt for monitoring
        callback?.(connectionStatus);
      } catch (error) {
        // Connection check failed, status already updated in testFirebaseConnection
        callback?.(connectionStatus);
      }
    }
  }, 30000);

  // Return cleanup function
  return () => clearInterval(interval);
};

