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
import * as Haptics from 'expo-haptics';

const { width, height } = Dimensions.get('window');
// Force landscape dimensions
const landscapeWidth = Math.max(width, height);

interface TabItem {
  key: string;
  title: string;
  icon: string;
  activeIcon?: string;
}

interface TikTokTabBarProps {
  activeTab: string;
  onTabPress: (tabKey: string) => void;
}

const tabs: TabItem[] = [
  {
    key: 'home',
    title: 'Home',
    icon: '△',
    activeIcon: '▲',
  },
  {
    key: 'discover',
    title: 'Discover',
    icon: '◊',
    activeIcon: '◆',
  },
  {
    key: 'inbox',
    title: 'Inbox',
    icon: '□',
    activeIcon: '■',
  },
  {
    key: 'profile',
    title: 'Profile',
    icon: '○',
    activeIcon: '●',
  },
];

export const TikTokTabBar: React.FC<TikTokTabBarProps> = ({
  activeTab,
  onTabPress,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];

  const handleTabPress = (tabKey: string) => {
    // Trigger haptic feedback
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onTabPress(tabKey);
  };

  return (
    <View style={styles.container}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        const iconToShow = isActive ? (tab.activeIcon || tab.icon) : tab.icon;
        
        return (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, isActive && styles.activeTab]}
            onPress={() => handleTabPress(tab.key)}
            activeOpacity={0.7}
          >
            <View style={[styles.iconContainer, isActive && styles.activeIconContainer]}>
              <Text style={[
                styles.tabIcon,
                isActive ? styles.activeTabIcon : styles.inactiveTabIcon
              ]}>
                {iconToShow}
              </Text>
            </View>
            <Text style={[
              styles.tabTitle,
              isActive ? styles.activeTabTitle : styles.inactiveTabTitle
            ]}>
              {tab.title}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#000000',
    borderTopWidth: 0.5,
    borderTopColor: '#1A1A1A',
    paddingBottom: 20,
    paddingTop: 4,
    paddingHorizontal: 10,
    width: landscapeWidth,
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingVertical: 2,
  },
  activeTab: {
    transform: [{ scale: 1.05 }],
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
    backgroundColor: 'transparent',
  },
  activeIconContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  tabIcon: {
    fontSize: 16,
    fontWeight: '300',
  },
  activeTabIcon: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  inactiveTabIcon: {
    color: '#9BA1A6',
  },
  tabTitle: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  activeTabTitle: {
    color: '#FFFFFF',
  },
  inactiveTabTitle: {
    color: '#9BA1A6',
  },
}); 