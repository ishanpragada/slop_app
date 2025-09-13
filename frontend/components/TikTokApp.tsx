import React, { useState } from 'react';
import {
    Alert,
    Dimensions,
    Modal,
    StatusBar,
    StyleSheet,
    View,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import { Comments } from './Comments';
import { DiscoverScreen } from './DiscoverScreen';
import { InboxScreen } from './InboxScreen';
import { SoundPage } from './SoundPage';
import { TikTokTabBar } from './TikTokTabBar';
import { UserProfile } from './UserProfile';
import { VideoFeedWithAPI } from './VideoFeedWithAPI';
import { UserPreferenceResponse } from '../services/userPreferenceService';

type ScreenType = 'home' | 'discover' | 'inbox' | 'profile';
type ModalType = 'comments' | 'profile' | 'sound' | null;

export const TikTokApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ScreenType>('home');
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);
  const { user, logout } = useAuth();

  const handleTabPress = (tabKey: string) => {
    setActiveTab(tabKey as ScreenType);
  };

  const handleLike = (videoId: string) => {
    console.log('Like pressed for video:', videoId);
    // TODO: Implement like functionality with backend
  };

  const handleComment = (videoId: string) => {
    setCurrentVideoId(videoId);
    setActiveModal('comments');
  };

  const handleShare = (videoId: string) => {
    console.log('Share pressed for video:', videoId);
    // TODO: Implement share functionality
  };

  const handleFollow = () => {
    console.log('Follow pressed');
    // TODO: Implement follow functionality
  };

  const handleProfilePress = () => {
    setActiveModal('profile');
  };

  const handleInteractionTracked = (response: UserPreferenceResponse) => {
    console.log('User preference interaction tracked:', response);
    // You can add additional logic here, such as:
    // - Updating UI based on preference updates
    // - Showing notifications when preferences are updated
    // - Logging analytics
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    setCurrentVideoId(null);
  };

  const handleAddComment = (comment: string) => {
    console.log('New comment for video', currentVideoId, ':', comment);
    // TODO: Implement comment functionality with backend
  };

  const handleEditProfile = () => {
    console.log('Edit profile pressed');
  };

  const handleBookmark = () => {
    console.log('Bookmark pressed');
  };

  const handleVideoPress = (videoId: string) => {
    console.log('Video pressed:', videoId);
  };

  const handleBack = () => {
    setActiveModal(null);
  };

  const handleShareSound = () => {
    console.log('Share sound pressed');
  };

  const handleAddToFavorites = () => {
    console.log('Add to favorites pressed');
  };

  const handleUseSound = () => {
    console.log('Use sound pressed');
  };

  const handleSignOut = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            try {
              await logout();
              // Navigation will be handled by ProtectedRoute
            } catch (error) {
              Alert.alert('Error', 'Failed to sign out');
            }
          },
        },
      ]
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <VideoFeedWithAPI
            userId={user?.uid || "anonymous"} 
            onLike={handleLike}
            onComment={handleComment}
            onShare={handleShare}
            onFollow={handleFollow}
            onProfilePress={handleProfilePress}
            onInteractionTracked={handleInteractionTracked}
          />
        );
      case 'discover':
        return <DiscoverScreen />;
      case 'inbox':
        return <InboxScreen />;
      case 'profile':
        return (
          <UserProfile
            onBack={handleBack}
            onEditProfile={handleEditProfile}
            onBookmark={handleBookmark}
            onVideoPress={handleVideoPress}
            onSignOut={handleSignOut}
          />
        );
      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#000000" />
      
      {/* Main Content */}
      {renderContent()}


      {/* Comments Modal */}
      <Modal
        visible={activeModal === 'comments'}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <Comments
          onClose={handleCloseModal}
          onAddComment={handleAddComment}
        />
      </Modal>

      {/* Profile Modal */}
      <Modal
        visible={activeModal === 'profile'}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <UserProfile
          onBack={handleCloseModal}
          onEditProfile={handleEditProfile}
          onBookmark={handleBookmark}
          onVideoPress={handleVideoPress}
          onSignOut={handleSignOut}
        />
      </Modal>

      {/* Sound Page Modal */}
      <Modal
        visible={activeModal === 'sound'}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SoundPage
          onBack={handleCloseModal}
          onShare={handleShareSound}
          onAddToFavorites={handleAddToFavorites}
          onUseSound={handleUseSound}
          onVideoPress={handleVideoPress}
        />
      </Modal>
    </View>
  );
};

const { width, height } = Dimensions.get('window');
// Force landscape dimensions
const landscapeWidth = Math.max(width, height);
const landscapeHeight = Math.min(width, height);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    width: landscapeWidth,
    height: landscapeHeight,
  },
}); 