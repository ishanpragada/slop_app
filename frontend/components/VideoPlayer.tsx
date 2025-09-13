import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

const { width, height } = Dimensions.get('window');

interface VideoPlayerProps {
  videoUrl?: string;
  onPress?: () => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  onPress,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={1}>
      <View style={styles.videoContainer}>
        {/* Video Placeholder - This would be replaced with actual video */}
        <View style={styles.videoContent}>
          <View style={styles.videoPlaceholder}>
            <Text style={styles.playIcon}>▶️</Text>
            <Text style={styles.videoText}>Video Content</Text>
          </View>
        </View>
        
        {/* Video Controls Overlay */}
        <View style={styles.controlsOverlay}>
          <View style={styles.topControls}>
            <View style={styles.progressBar}>
              <View style={styles.progressFill} />
            </View>
          </View>
          
          <View style={styles.centerControls}>
            <TouchableOpacity style={styles.playButton}>
              <Text style={styles.playButtonIcon}>⏸️</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  videoContainer: {
    flex: 1,
    position: 'relative',
  },
  videoContent: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  videoPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
  },
  playIcon: {
    fontSize: 48,
    marginBottom: 10,
  },
  videoText: {
    color: '#FFFFFF',
    fontSize: 16,
    opacity: 0.7,
  },
  controlsOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'space-between',
  },
  topControls: {
    paddingTop: 100,
    paddingHorizontal: 20,
  },
  progressBar: {
    height: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 1,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#FF2D55',
    borderRadius: 1,
    width: '30%', // This would be dynamic based on video progress
  },
  centerControls: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButtonIcon: {
    fontSize: 24,
  },
}); 