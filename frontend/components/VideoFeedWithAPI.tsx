import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { VideoView, useVideoPlayer } from 'expo-video';
import { Heart, MessageCircle, Share, Volume2, VolumeX, User, Pause } from 'lucide-react-native';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    Dimensions,
    FlatList,
    Platform,
    StatusBar,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { API_CONFIG, getCurrentIP, testApiConnection } from '../config/api';
import { useVideoInteraction } from '../hooks/useVideoInteraction';
import { UserPreferenceResponse } from '../services/userPreferenceService';

const { width, height } = Dimensions.get('window');
const statusBarHeight = Platform.OS === 'ios' ? 44 : StatusBar.currentHeight || 0;
// Force landscape dimensions - always use the larger dimension as width
const landscapeWidth = Math.max(width, height);
const landscapeHeight = Math.min(width, height);
const videoHeight = landscapeHeight;

// Use the centralized API configuration
const API_BASE_URL = API_CONFIG.BASE_URL;

interface VideoFeedItem {
  video_id: string;
  video_url: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  aspect_ratio?: string;
  title?: string;
  description?: string;
  score?: number;
  size?: number;
  last_modified?: string;
}

interface FeedResponse {
  success: boolean;
  videos: VideoFeedItem[];
  total_videos: number;
  cursor: number;
  next_cursor?: number;
  has_more: boolean;
  feed_size: number;
  message: string;
}

interface VideoFeedProps {
  userId?: string;
  onLike?: (videoId: string) => void;
  onComment?: (videoId: string) => void;
  onShare?: (videoId: string) => void;
  onFollow?: () => void;
  onProfilePress?: () => void;
  onInteractionTracked?: (response: UserPreferenceResponse) => void;
}

interface VideoItemProps {
  item: VideoFeedItem;
  isActive: boolean;
  userId: string;
  onLike: (videoId: string) => void;
  onComment: (videoId: string) => void;
  onShare: (videoId: string) => void;
  onFollow: () => void;
  onProfilePress: () => void;
  onInteractionTracked?: (response: UserPreferenceResponse) => void;
}

const VideoItem: React.FC<VideoItemProps> = ({
  item,
  isActive,
  userId,
  onLike,
  onComment,
  onShare,
  onFollow,
  onProfilePress,
  onInteractionTracked,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [isManuallyPaused, setIsManuallyPaused] = useState(false);
  const videoRef = useRef<VideoView>(null);
  
  const player = useVideoPlayer(item.video_url, (player) => {
    player.loop = true;
    player.muted = isMuted;
    player.timeUpdateEventInterval = 0.1; // Update every 100ms for smoother tracking
  });

  // Handle loading state for expo-video
  useEffect(() => {
    if (player.status === 'readyToPlay') {
      setIsLoading(false);
      if (__DEV__) {
        console.log('Video ready to play, isActive:', isActive);
      }
    } else if (player.status === 'loading') {
      setIsLoading(true);
    } else if (player.status === 'error') {
      setIsLoading(false);
      console.error('Video load error');
    }
  }, [player.status, isActive]);

  // Use the video interaction hook
  const {
    isLiked,
    isLikeLoading,
    likeError,
    watchTime,
    hasTrackedView,
    hasTrackedSkip,
    handleLike,
    resetInteraction,
  } = useVideoInteraction({
    userId,
    videoId: item.video_id,
    isActive,
    onInteractionTracked,
  });

  useEffect(() => {
    if (isActive && player.status === 'readyToPlay' && !isManuallyPaused) {
      try {
        if (__DEV__) {
          console.log('Starting video playback for active video');
        }
        player.play();
      } catch (error) {
        console.error('Error playing video:', error);
      }
    } else if (!isActive) {
      try {
        player.pause();
        setIsManuallyPaused(false); // Reset manual pause state when video becomes inactive
        // Reset interaction tracking when video becomes inactive
        resetInteraction();
      } catch (error) {
        console.error('Error pausing video:', error);
      }
    }
  }, [isActive, player.status, isManuallyPaused, resetInteraction, player]);

  useEffect(() => {
    player.muted = isMuted;
  }, [isMuted, player]);

  const togglePlayPause = () => {
    try {
      if (player.playing) {
        player.pause();
        setIsManuallyPaused(true); // Mark as manually paused
      } else {
        player.play();
        setIsManuallyPaused(false); // Clear manual pause state
      }
    } catch (error) {
      console.error('Error toggling play/pause:', error);
    }
  };

  const toggleMute = () => {
    const newMutedState = !isMuted;
    setIsMuted(newMutedState);
    if (__DEV__) {
      console.log('Audio toggled. Muted:', newMutedState, 'Volume:', newMutedState ? 0.0 : 1.0);
    }
  };

  const handleLikePress = async () => {
    await handleLike();
    onLike(item.video_id);
  };

  return (
    <View style={styles.videoContainer}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Video Player */}
      <TouchableOpacity 
        style={styles.videoPlayer} 
        onPress={togglePlayPause}
        activeOpacity={1}
      >
        <VideoView
          ref={videoRef}
          style={styles.video}
          player={player}
          contentFit="contain"
          nativeControls={false}
        />
        
        {/* Loading indicator */}
        {isLoading && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color="#FFFFFF" />
          </View>
        )}
        
        {/* Pause overlay - only show when manually paused */}
        {!player.playing && !isLoading && isManuallyPaused && (
          <View style={styles.playOverlay}>
            <View style={styles.playButton}>
              <Pause size={32} color="#FFFFFF" strokeWidth={2} />
            </View>
          </View>
        )}
      </TouchableOpacity>

      {/* Right Side Interaction Buttons */}
      <View style={styles.rightSidebar}>
        {/* Like Button */}
        <TouchableOpacity 
          style={[
            styles.actionButton, 
            isLikeLoading && styles.actionButtonLoading
          ]} 
          onPress={handleLikePress}
          disabled={isLikeLoading}
        >
          {isLikeLoading ? (
            <ActivityIndicator size="small" color="#FF2D55" />
          ) : (
            <Heart 
              size={28} 
              color={isLiked ? "#FF2D55" : "#FFFFFF"} 
              strokeWidth={2} 
              fill={isLiked ? "#FF2D55" : "none"}
            />
          )}
        </TouchableOpacity>

        {/* Comment Button */}
        <TouchableOpacity style={styles.actionButton} onPress={() => onComment(item.video_id)}>
          <MessageCircle size={28} color="#FFFFFF" strokeWidth={2} />
        </TouchableOpacity>

        {/* Share Button */}
        <TouchableOpacity style={styles.actionButton} onPress={() => onShare(item.video_id)}>
          <Share size={28} color="#FFFFFF" strokeWidth={2} />
        </TouchableOpacity>

        {/* Mute/Unmute Button */}
        <TouchableOpacity style={styles.actionButton} onPress={toggleMute}>
          {isMuted ? (
            <VolumeX size={28} color="#FFFFFF" strokeWidth={2} />
          ) : (
            <Volume2 size={28} color="#FFFFFF" strokeWidth={2} />
          )}
        </TouchableOpacity>

        {/* Profile Button */}
        <TouchableOpacity style={styles.actionButton} onPress={onProfilePress}>
          <User size={28} color="#FFFFFF" strokeWidth={2} />
        </TouchableOpacity>
      </View>

      {/* Like Error Message */}
      {likeError && (
        <View style={styles.errorOverlay}>
          <Text style={styles.errorText}>{likeError}</Text>
        </View>
      )}

      {/* Debug Info Overlay - only show in development */}
      {__DEV__ && (
        <View style={styles.debugOverlay}>
          <Text style={styles.debugText}>Watch: {watchTime.toFixed(1)}s</Text>
          <Text style={styles.debugText}>
            {hasTrackedView ? '✅ View' : hasTrackedSkip ? '⏭️ Skip' : '⏳ Watching...'}
          </Text>
          <Text style={styles.debugText}>
            {isLiked ? '❤️ Liked' : '🤍 Not liked'} {isLikeLoading && '🔄'}
          </Text>
        </View>
      )}

    </View>
  );
};

export const VideoFeedWithAPI: React.FC<VideoFeedProps> = ({
  userId = 'anonymous',
  onLike,
  onComment,
  onShare,
  onFollow,
  onProfilePress,
  onInteractionTracked,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];
  
  const [videos, setVideos] = useState<VideoFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [cursor, setCursor] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const flatListRef = useRef<FlatList>(null);

  // Fetch videos from backend
  const fetchVideos = useCallback(async (
    isRefresh = false,
    customCursor?: number
  ) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
        setCursor(0);
      } else if (customCursor === undefined) {
        setLoadingMore(true);
      }

      const fetchCursor = customCursor !== undefined ? customCursor : (isRefresh ? 0 : cursor);
      const url = `${API_BASE_URL}${API_CONFIG.ENDPOINTS.INFINITE_FEED}?user_id=${userId}&cursor=${fetchCursor}&limit=10&refresh=${isRefresh}`;
      
      console.log('Fetching from URL (INFINITE):', url); // Debug log
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: FeedResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch videos');
      }

      if (isRefresh) {
        setVideos(data.videos);
        setCursor(data.next_cursor || data.videos.length);
      } else {
        setVideos(prev => customCursor === 0 ? data.videos : [...prev, ...data.videos]);
        setCursor(data.next_cursor || cursor + data.videos.length);
      }
      
      setHasMore(data.has_more);
      setError(null);
      
    } catch (err) {
      console.error('Error fetching videos:', err);
      console.log('Using API URL:', API_BASE_URL); // Debug log
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      
      if (videos.length === 0) {
        Alert.alert(
          'Connection Error',
          `Failed to connect to backend at ${API_BASE_URL}.\n\nPlease ensure:\n1. Backend is running\n2. You're on the same WiFi network\n3. Backend started with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`,
          [
            { text: 'Retry', onPress: () => fetchVideos(true) },
            { text: 'Cancel', style: 'cancel' }
          ]
        );
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [cursor, userId, videos.length]);

  // Initial load
  useEffect(() => {
    // Test API connection first
    testApiConnection().then(isConnected => {
      if (isConnected) {
        fetchVideos(true);
      } else {
        setError('API connection failed. Please check your backend server.');
      }
    });
  }, []);

  // Handle scroll to load more videos (prefetching)
  const handleLoadMore = useCallback(() => {
    if (!loadingMore && hasMore && videos.length > 0) {
      fetchVideos();
    }
  }, [loadingMore, hasMore, videos.length, fetchVideos]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    fetchVideos(true);
  }, [fetchVideos]);

  // Handle like action
  const handleLike = useCallback((videoId: string) => {
    console.log('Liked video:', videoId);
    if (onLike) {
      onLike(videoId);
    }
  }, [onLike]);

  // Handle comment action
  const handleComment = useCallback((videoId: string) => {
    console.log('Comment on video:', videoId);
    if (onComment) {
      onComment(videoId);
    }
  }, [onComment]);

  // Handle share action
  const handleShare = useCallback((videoId: string) => {
    console.log('Share video:', videoId);
    if (onShare) {
      onShare(videoId);
    }
  }, [onShare]);

  // Handle scroll and track current video
  const onViewableItemsChanged = useCallback(({ viewableItems }: any) => {
    if (viewableItems.length > 0) {
      const visibleIndex = viewableItems[0].index;
      setCurrentIndex(visibleIndex);
      
      // Prefetch more videos when approaching end (10 videos ahead)
      if (visibleIndex >= videos.length - 5 && hasMore && !loadingMore) {
        handleLoadMore();
      }
    }
  }, [videos.length, hasMore, loadingMore, handleLoadMore]);

  const viewabilityConfig = {
    itemVisiblePercentThreshold: 80,
    minimumViewTime: 200,
  };

  // Handle interaction tracking
  const handleInteractionTracked = useCallback((response: UserPreferenceResponse) => {
    console.log('User preference interaction tracked:', response);
    onInteractionTracked?.(response);
  }, [onInteractionTracked]);

  // Render individual video item
  const renderVideoItem = ({ item, index }: { item: VideoFeedItem; index: number }) => (
    <VideoItem
      item={item}
      isActive={index === currentIndex}
      userId={userId}
      onLike={handleLike}
      onComment={handleComment}
      onShare={handleShare}
      onFollow={onFollow || (() => {})}
      onProfilePress={onProfilePress || (() => {})}
      onInteractionTracked={handleInteractionTracked}
    />
  );

  // Loading state
  if (loading && videos.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FFFFFF" />
        <Text style={styles.loadingText}>Loading your feed...</Text>
      </View>
    );
  }

  // Error state
  if (error && videos.length === 0) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Failed to load videos</Text>
        <Text style={styles.errorSubtext}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => fetchVideos(true)}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={videos}
        renderItem={renderVideoItem}
        keyExtractor={(item) => item.video_id}
        pagingEnabled
        showsVerticalScrollIndicator={false}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        removeClippedSubviews={false}
        maxToRenderPerBatch={2}
        initialNumToRender={1}
        windowSize={3}
        snapToInterval={landscapeHeight}
        snapToAlignment="start"
        decelerationRate="fast"
        bounces={false}
        scrollEventThrottle={16}
        disableIntervalMomentum={true}
        contentContainerStyle={{ width: landscapeWidth }}
        getItemLayout={(_, index) => ({
          length: landscapeHeight,
          offset: landscapeHeight * index,
          index,
        })}
      />
      
      {/* Loading more indicator */}
      {loadingMore && (
        <View style={styles.loadingMoreContainer}>
          <ActivityIndicator size="small" color="#FFFFFF" />
        </View>
      )}
      
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  videoContainer: {
    width: landscapeWidth,
    height: videoHeight,
    position: 'relative',
  },
  videoPlayer: {
    flex: 1,
  },
  video: {
    width: '100%',
    height: '100%',
    backgroundColor: '#000000',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  playOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rightSidebar: {
    position: 'absolute',
    right: 15,
    top: '50%',
    transform: [{ translateY: -150 }], // Offset to center the icon group (5 icons * 48px + 4 margins * 16px = 304px, half is 152px)
    alignItems: 'center',
    zIndex: 10,
  },
  actionButton: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    marginBottom: 16,
    backdropFilter: 'blur(10px)',
  },
  actionButtonLoading: {
    backgroundColor: 'rgba(255, 45, 85, 0.2)', // Slightly red background when loading
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
    marginTop: 10,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
    paddingHorizontal: 40,
  },
  errorText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  errorSubtext: {
    color: '#9BA1A6',
    fontSize: 14,
    marginBottom: 20,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#FF2D55',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 25,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingMoreContainer: {
    position: 'absolute',
    bottom: 100,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  errorOverlay: {
    position: 'absolute',
    top: 50,
    left: 15,
    right: 15,
    backgroundColor: 'rgba(255, 45, 85, 0.9)',
    padding: 12,
    borderRadius: 8,
    zIndex: 20,
  },
  errorText: {
    color: '#FFFFFF',
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '500',
  },
  debugOverlay: {
    position: 'absolute',
    top: 100,
    left: 15,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 10,
    borderRadius: 8,
    minWidth: 120,
  },
  debugText: {
    color: '#FFFFFF',
    fontSize: 12,
    marginBottom: 2,
    fontFamily: 'monospace',
  },
}); 