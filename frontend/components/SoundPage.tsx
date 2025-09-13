import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import React from 'react';
import {
    Dimensions,
    FlatList,
    StatusBar,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';

const { width } = Dimensions.get('window');
const videoWidth = (width - 4) / 3; // 3 columns with 2px gap

interface VideoItem {
  id: string;
  thumbnail: string;
}

interface SoundPageProps {
  onBack?: () => void;
  onShare?: () => void;
  onAddToFavorites?: () => void;
  onUseSound?: () => void;
  onVideoPress?: (videoId: string) => void;
}

const mockVideos: VideoItem[] = Array.from({ length: 12 }, (_, i) => ({
  id: i.toString(),
  thumbnail: `video-${i}`,
}));

export const SoundPage: React.FC<SoundPageProps> = ({
  onBack,
  onShare,
  onAddToFavorites,
  onUseSound,
  onVideoPress,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];

  const renderVideo = ({ item }: { item: VideoItem }) => (
    <TouchableOpacity
      style={styles.videoThumbnail}
      onPress={() => onVideoPress?.(item.id)}
    >
      <View style={styles.videoPlaceholder}>
        <Text style={styles.videoPlaceholderText}>📹</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onShare} style={styles.shareButton}>
          <Text style={styles.shareIcon}>📤</Text>
        </TouchableOpacity>
      </View>

      {/* Sound Info */}
      <View style={styles.soundInfo}>
        <View style={styles.albumArt}>
          <Text style={styles.albumArtText}>🎵</Text>
        </View>
        <Text style={styles.soundTitle}>The Round</Text>
        <Text style={styles.artistName}>Roddy Roundicch</Text>
        <Text style={styles.videoCount}>1.7M videos</Text>
        
        <TouchableOpacity style={styles.favoritesButton} onPress={onAddToFavorites}>
          <Text style={styles.favoritesIcon}>🔖</Text>
          <Text style={styles.favoritesText}>Add to Favorites</Text>
        </TouchableOpacity>
      </View>

      {/* Video Grid */}
      <FlatList
        data={mockVideos}
        renderItem={renderVideo}
        keyExtractor={(item) => item.id}
        numColumns={3}
        style={styles.videoGrid}
        showsVerticalScrollIndicator={false}
      />

      {/* Use Sound Button */}
      <TouchableOpacity style={styles.useSoundButton} onPress={onUseSound}>
        <Text style={styles.cameraIcon}>📷</Text>
        <Text style={styles.useSoundText}>Use this sound</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    paddingTop: 50,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backIcon: {
    fontSize: 24,
    color: '#000000',
  },
  shareButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  shareIcon: {
    fontSize: 20,
    color: '#000000',
  },
  soundInfo: {
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 20,
  },
  albumArt: {
    width: 120,
    height: 120,
    borderRadius: 8,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  albumArtText: {
    fontSize: 48,
  },
  soundTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000000',
    marginBottom: 5,
  },
  artistName: {
    fontSize: 16,
    color: '#9BA1A6',
    marginBottom: 5,
  },
  videoCount: {
    fontSize: 14,
    color: '#9BA1A6',
    marginBottom: 20,
  },
  favoritesButton: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E5E5',
    borderRadius: 4,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  favoritesIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  favoritesText: {
    fontSize: 14,
    color: '#000000',
    fontWeight: '500',
  },
  videoGrid: {
    flex: 1,
  },
  videoThumbnail: {
    width: videoWidth,
    height: videoWidth * 1.3,
    margin: 1,
  },
  videoPlaceholder: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoPlaceholderText: {
    fontSize: 24,
  },
  useSoundButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF2D55',
    paddingVertical: 15,
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 8,
  },
  cameraIcon: {
    fontSize: 20,
    color: '#FFFFFF',
    marginRight: 8,
  },
  useSoundText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
}); 