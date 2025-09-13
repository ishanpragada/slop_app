import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import React from 'react';
import {
    Dimensions,
    StatusBar,
    StyleSheet,
    Text,
    TouchableOpacity,
    View
} from 'react-native';
import { VideoPlayer } from './VideoPlayer';

const { width, height } = Dimensions.get('window');

interface VideoFeedProps {
  onLike?: () => void;
  onComment?: () => void;
  onShare?: () => void;
  onFollow?: () => void;
  onProfilePress?: () => void;
}

export const VideoFeed: React.FC<VideoFeedProps> = ({
  onLike,
  onComment,
  onShare,
  onFollow,
  onProfilePress,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Top Navigation Tabs */}
      <View style={styles.topTabs}>
        <Text style={[styles.tabText, styles.inactiveTab]}>Following</Text>
        <Text style={[styles.tabText, styles.activeTab]}>For You</Text>
      </View>

      {/* Video Content Area */}
      <View style={styles.videoContainer}>
        <VideoPlayer />

        {/* Right Side Interaction Buttons */}
        <View style={styles.rightSidebar}>
          {/* Profile Picture */}
          <TouchableOpacity style={styles.profileButton} onPress={onProfilePress}>
            <View style={styles.profileImage}>
              <Text style={styles.profileInitial}>D</Text>
            </View>
            <View style={styles.followButton}>
              <Text style={styles.followButtonText}>+</Text>
            </View>
          </TouchableOpacity>

          {/* Like Button */}
          <TouchableOpacity style={styles.actionButton} onPress={onLike}>
            <Text style={styles.actionIcon}>❤️</Text>
            <Text style={styles.actionCount}>6374</Text>
          </TouchableOpacity>

          {/* Comment Button */}
          <TouchableOpacity style={styles.actionButton} onPress={onComment}>
            <Text style={styles.actionIcon}>💬</Text>
            <Text style={styles.actionCount}>64</Text>
          </TouchableOpacity>

          {/* Share Button */}
          <TouchableOpacity style={styles.actionButton} onPress={onShare}>
            <Text style={styles.actionIcon}>📤</Text>
            <Text style={styles.actionText}>Share</Text>
          </TouchableOpacity>
        </View>

        {/* Bottom Left User Info */}
        <View style={styles.bottomInfo}>
          <Text style={styles.username}>@Yourname</Text>
          <Text style={styles.description}>Description Here #hashtag #hashtag</Text>
          <View style={styles.musicInfo}>
            <Text style={styles.musicIcon}>♫</Text>
            <Text style={styles.musicText}>Music name here - Artist Name</Text>
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  topTabs: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 50,
    paddingBottom: 20,
    zIndex: 10,
  },
  tabText: {
    fontSize: 16,
    fontWeight: '600',
    marginHorizontal: 20,
  },
  activeTab: {
    color: '#FFFFFF',
  },
  inactiveTab: {
    color: '#9BA1A6',
  },
  videoContainer: {
    flex: 1,
    position: 'relative',
  },

  rightSidebar: {
    position: 'absolute',
    right: 15,
    bottom: 150,
    alignItems: 'center',
  },
  profileButton: {
    alignItems: 'center',
    marginBottom: 20,
  },
  profileImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 5,
  },
  profileInitial: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: 'bold',
  },
  followButton: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#FF2D55',
    justifyContent: 'center',
    alignItems: 'center',
  },
  followButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  actionButton: {
    alignItems: 'center',
    marginBottom: 20,
  },
  actionIcon: {
    fontSize: 30,
    marginBottom: 5,
  },
  actionCount: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  actionText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  bottomInfo: {
    position: 'absolute',
    bottom: 150,
    left: 15,
    right: 100,
  },
  username: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 5,
  },
  description: {
    color: '#FFFFFF',
    fontSize: 14,
    marginBottom: 10,
  },
  musicInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  musicIcon: {
    color: '#FFFFFF',
    fontSize: 16,
    marginRight: 5,
  },
  musicText: {
    color: '#FFFFFF',
    fontSize: 14,
  },
}); 