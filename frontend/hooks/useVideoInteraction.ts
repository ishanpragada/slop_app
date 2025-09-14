import { useCallback, useEffect, useRef, useState } from 'react';
import { userPreferenceService, UserPreferenceResponse } from '../services/userPreferenceService';

interface UseVideoInteractionProps {
  userId: string;
  videoId: string;
  isActive: boolean;
  onInteractionTracked?: (response: UserPreferenceResponse) => void;
}

interface UseVideoInteractionReturn {
  isLiked: boolean;
  isLikeLoading: boolean;
  likeError: string | null;
  watchTime: number;
  hasTrackedView: boolean;
  hasTrackedSkip: boolean;
  handleLike: () => Promise<void>;
  trackViewTime: (timeInSeconds: number) => Promise<void>;
  resetInteraction: () => void;
}

export const useVideoInteraction = ({
  userId,
  videoId,
  isActive,
  onInteractionTracked,
}: UseVideoInteractionProps): UseVideoInteractionReturn => {
  const [isLiked, setIsLiked] = useState(false);
  const [isLikeLoading, setIsLikeLoading] = useState(false);
  const [likeError, setLikeError] = useState<string | null>(null);
  const [watchTime, setWatchTime] = useState(0);
  const [hasTrackedView, setHasTrackedView] = useState(false);
  const [hasTrackedSkip, setHasTrackedSkip] = useState(false);
  
  const watchTimeRef = useRef(0);
  const intervalRef = useRef<number | null>(null);
  const hasTrackedInteractionRef = useRef(false);

  // Track watch time when video is active
  useEffect(() => {
    if (isActive && !hasTrackedInteractionRef.current) {
      // Start tracking watch time
      intervalRef.current = setInterval(() => {
        watchTimeRef.current += 0.1; // Update every 100ms
        setWatchTime(watchTimeRef.current);
      }, 100);
    } else {
      // Stop tracking when video becomes inactive
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      
      // Track view/skip interactions only when video becomes inactive (user scrolls away)
      if (watchTimeRef.current > 0 && !hasTrackedInteractionRef.current) {
        if (watchTimeRef.current >= 3) {
          trackView();
        } else {
          trackSkip();
        }
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isActive]);

  const trackView = useCallback(async () => {
    if (hasTrackedView || hasTrackedInteractionRef.current) return;
    
    try {
      const response = await userPreferenceService.trackView(userId, videoId);
      setHasTrackedView(true);
      hasTrackedInteractionRef.current = true;
      onInteractionTracked?.(response);
      
      console.log('View tracked:', {
        videoId,
        watchTime: watchTimeRef.current,
        response
      });
    } catch (error) {
      console.error('Error tracking view:', error);
    }
  }, [userId, videoId, hasTrackedView, onInteractionTracked]);

  const trackSkip = useCallback(async () => {
    if (hasTrackedSkip || hasTrackedInteractionRef.current) return;
    
    try {
      const response = await userPreferenceService.trackSkip(userId, videoId);
      setHasTrackedSkip(true);
      hasTrackedInteractionRef.current = true;
      onInteractionTracked?.(response);
      
      console.log('Skip tracked:', {
        videoId,
        watchTime: watchTimeRef.current,
        response
      });
    } catch (error) {
      console.error('Error tracking skip:', error);
    }
  }, [userId, videoId, hasTrackedSkip, onInteractionTracked]);

  const handleLike = useCallback(async () => {
    // Clear any previous errors
    setLikeError(null);
    
    // Optimistic UI update - show red heart immediately
    const newLikedState = !isLiked;
    setIsLiked(newLikedState);
    setIsLikeLoading(true);
    
    try {
      // Call backend to track the like
      const response = await userPreferenceService.trackLike(userId, videoId);
      onInteractionTracked?.(response);
      
      console.log('Like tracked:', {
        videoId,
        isLiked: newLikedState,
        response
      });
    } catch (error) {
      // Rollback optimistic update if backend call fails
      console.error('Error tracking like:', error);
      setIsLiked(isLiked); // Revert to previous state
      setLikeError('Failed to track like. Please try again.');
      
      // Clear error after 3 seconds
      setTimeout(() => setLikeError(null), 3000);
    } finally {
      setIsLikeLoading(false);
    }
  }, [userId, videoId, isLiked, onInteractionTracked]);

  const trackViewTime = useCallback(async (timeInSeconds: number) => {
    watchTimeRef.current = timeInSeconds;
    setWatchTime(timeInSeconds);
    
    // Note: View/skip tracking is now deferred until video becomes inactive
    // This function only updates the watch time display
  }, []);

  const resetInteraction = useCallback(() => {
    setIsLiked(false);
    setIsLikeLoading(false);
    setLikeError(null);
    setWatchTime(0);
    setHasTrackedView(false);
    setHasTrackedSkip(false);
    watchTimeRef.current = 0;
    hasTrackedInteractionRef.current = false;
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  return {
    isLiked,
    isLikeLoading,
    likeError,
    watchTime,
    hasTrackedView,
    hasTrackedSkip,
    handleLike,
    trackViewTime,
    resetInteraction,
  };
};
