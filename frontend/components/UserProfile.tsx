import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import React, { useState } from 'react';
import {
    Dimensions,
    FlatList,
    Modal,
    StatusBar,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

const { width } = Dimensions.get('window');
const videoWidth = (width - 4) / 3; // 3 columns with 2px gap

interface VideoItem {
  id: string;
  thumbnail: string;
}

interface UserProfileProps {
  onBack?: () => void;
  onEditProfile?: () => void;
  onBookmark?: () => void;
  onVideoPress?: (videoId: string) => void;
  onSignOut?: () => void;
}

const mockVideos: VideoItem[] = Array.from({ length: 15 }, (_, i) => ({
  id: i.toString(),
  thumbnail: `video-${i}`,
}));

export const UserProfile: React.FC<UserProfileProps> = ({
  onBack,
  onEditProfile,
  onBookmark,
  onVideoPress,
  onSignOut,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];
  const { user } = useAuth();

  // Get user's display name or email
  const displayName = user?.displayName || user?.email?.split('@')[0] || 'User';
  const userEmail = user?.email || 'user@example.com';
  const [showMenu, setShowMenu] = useState(false);

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
        <View style={styles.headerTitle}>
          <Text style={styles.username}>{displayName}</Text>
          <Text style={styles.dropdownIcon}>▼</Text>
        </View>
        <TouchableOpacity style={styles.menuButton} onPress={() => setShowMenu(true)}>
          <Text style={styles.menuIcon}>☰</Text>
        </TouchableOpacity>
      </View>

      {/* Profile Info */}
      <View style={styles.profileSection}>
        <View style={styles.profileImage}>
          <Text style={styles.profileInitial}>{displayName.charAt(0).toUpperCase()}</Text>
        </View>
        <Text style={styles.handle}>@{displayName.toLowerCase().replace(/\s+/g, '_')}</Text>
        
        {/* Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>14</Text>
            <Text style={styles.statLabel}>Following</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>38</Text>
            <Text style={styles.statLabel}>Followers</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>172</Text>
            <Text style={styles.statLabel}>Likes</Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity style={styles.editButton} onPress={onEditProfile}>
            <Text style={styles.editButtonText}>Edit profile</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.bookmarkButton} onPress={onBookmark}>
            <Text style={styles.bookmarkIcon}>🔖</Text>
          </TouchableOpacity>
        </View>

        {/* Bio */}
        <Text style={styles.bio}>Tap to add bio</Text>
      </View>

      {/* Content Tabs */}
      <View style={styles.tabsContainer}>
        <TouchableOpacity style={[styles.tab, styles.activeTab]}>
          <Text style={[styles.tabIcon, styles.activeTabIcon]}>⊞</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tab}>
          <Text style={styles.tabIcon}>❤️</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tab}>
          <Text style={styles.tabIcon}>🔖</Text>
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

      {/* Menu Modal */}
      <Modal
        visible={showMenu}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowMenu(false)}
      >
        <TouchableOpacity 
          style={styles.modalOverlay} 
          activeOpacity={1} 
          onPress={() => setShowMenu(false)}
        >
          <View style={styles.menuContainer}>
            <TouchableOpacity style={styles.menuItem} onPress={() => {
              setShowMenu(false);
              // TODO: Implement settings
              console.log('Settings and Privacy pressed');
            }}>
              <Text style={styles.menuItemText}>Settings and Privacy</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.menuItem} onPress={() => {
              setShowMenu(false);
              onSignOut?.();
            }}>
              <Text style={[styles.menuItemText, styles.signOutText]}>Sign Out</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
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
  headerTitle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginRight: 5,
  },
  dropdownIcon: {
    fontSize: 12,
    color: '#000000',
  },
  menuButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuIcon: {
    fontSize: 20,
    color: '#000000',
  },
  profileSection: {
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 20,
  },
  profileImage: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#E5E5E5',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  profileInitial: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#666666',
  },
  handle: {
    fontSize: 14,
    color: '#9BA1A6',
    marginBottom: 15,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000000',
  },
  statLabel: {
    fontSize: 12,
    color: '#9BA1A6',
    marginTop: 2,
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  editButton: {
    borderWidth: 1,
    borderColor: '#E5E5E5',
    borderRadius: 4,
    paddingHorizontal: 20,
    paddingVertical: 8,
    marginRight: 10,
  },
  editButtonText: {
    fontSize: 14,
    color: '#000000',
    fontWeight: '500',
  },
  bookmarkButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bookmarkIcon: {
    fontSize: 20,
  },
  bio: {
    fontSize: 14,
    color: '#9BA1A6',
    textAlign: 'center',
  },
  tabsContainer: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#E5E5E5',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 15,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#000000',
  },
  tabIcon: {
    fontSize: 20,
    color: '#9BA1A6',
  },
  activeTabIcon: {
    color: '#000000',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
    paddingTop: 100,
    paddingRight: 20,
  },
  menuContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingVertical: 8,
    minWidth: 200,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  menuItem: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  menuItemText: {
    fontSize: 16,
    color: '#000000',
    fontWeight: '500',
  },
  signOutText: {
    color: '#FF3B30',
  },
}); 