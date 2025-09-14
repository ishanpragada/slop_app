import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
  SafeAreaView,
  Image,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

interface UserProfileProps {
  onBack: () => void;
  onEditProfile: () => void;
  onBookmark: () => void;
  onVideoPress: (videoId: string) => void;
  onSignOut: () => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({
  onBack,
  onEditProfile,
  onBookmark,
  onVideoPress,
  onSignOut,
}) => {
  const { user } = useAuth();

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile</Text>
        <TouchableOpacity onPress={onSignOut} style={styles.signOutButton}>
          <Text style={styles.signOutButtonText}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content} 
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Profile Info Section */}
        <View style={styles.profileSection}>
          {/* Profile Picture */}
          <View style={styles.profilePictureContainer}>
            <Image
              source={{ 
                uri: user?.photoURL || 'https://via.placeholder.com/120x120/333/fff?text=User'
              }}
              style={styles.profilePicture}
            />
          </View>
          
          {/* User Info */}
          <View style={styles.userInfo}>
            <Text style={styles.username}>
              {user?.displayName || user?.email?.split('@')[0] || 'User'}
            </Text>
            <Text style={styles.userHandle}>
              @{user?.email?.split('@')[0] || 'user'}
            </Text>
          </View>
          
          {/* Bio */}
          <View style={styles.bioContainer}>
            <Text style={styles.bioText}>
              🎬 Content Creator {'\n'}
              🌟 Spreading positivity {'\n'}
              📧 {user?.email || 'contact@email.com'}
            </Text>
          </View>
          
          {/* Edit Profile Button */}
          <TouchableOpacity style={styles.editButton} onPress={onEditProfile}>
            <Text style={styles.editButtonText}>Edit Profile</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  backButton: {
    padding: 10,
  },
  backButtonText: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  signOutButton: {
    backgroundColor: '#FF3040',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  signOutButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: Math.max(20, landscapeWidth * 0.1),
    paddingVertical: 20,
  },
  profileSection: {
    alignItems: 'center',
    maxWidth: 600,
    alignSelf: 'center',
    width: '100%',
  },
  profilePictureContainer: {
    marginBottom: Math.max(15, landscapeHeight * 0.03),
  },
  profilePicture: {
    width: Math.min(120, landscapeHeight * 0.18),
    height: Math.min(120, landscapeHeight * 0.18),
    borderRadius: Math.min(60, landscapeHeight * 0.09),
    backgroundColor: '#333333',
  },
  userInfo: {
    alignItems: 'center',
    marginBottom: Math.max(20, landscapeHeight * 0.04),
  },
  username: {
    color: '#FFFFFF',
    fontSize: Math.min(24, landscapeHeight * 0.045),
    fontWeight: 'bold',
    marginBottom: 5,
    textAlign: 'center',
  },
  userHandle: {
    color: '#AAAAAA',
    fontSize: Math.min(18, landscapeHeight * 0.035),
    textAlign: 'center',
  },
  bioContainer: {
    alignItems: 'center',
    marginBottom: Math.max(25, landscapeHeight * 0.05),
    paddingHorizontal: 20,
    maxWidth: '100%',
  },
  bioText: {
    color: '#FFFFFF',
    fontSize: Math.min(16, landscapeHeight * 0.03),
    lineHeight: Math.min(24, landscapeHeight * 0.045),
    textAlign: 'center',
    maxWidth: 400,
  },
  editButton: {
    backgroundColor: '#333333',
    paddingHorizontal: Math.max(25, landscapeWidth * 0.04),
    paddingVertical: Math.max(10, landscapeHeight * 0.02),
    borderRadius: 25,
    borderWidth: 1,
    borderColor: '#555555',
    minWidth: 150,
  },
  editButtonText: {
    color: '#FFFFFF',
    fontSize: Math.min(16, landscapeHeight * 0.03),
    fontWeight: '600',
    textAlign: 'center',
  },
});
