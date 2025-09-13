import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import React, { useState } from 'react';
import {
    FlatList,
    StatusBar,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';

interface Comment {
  id: string;
  username: string;
  text: string;
  timestamp: string;
  likes: number;
  hasReplies?: boolean;
  replyCount?: number;
}

interface CommentsProps {
  onClose?: () => void;
  comments?: Comment[];
  onAddComment?: (comment: string) => void;
}

const mockComments: Comment[] = [
  {
    id: '1',
    username: 'martini_rond',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 7324,
  },
  {
    id: '2',
    username: 'maxjacobson',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 6172,
    hasReplies: true,
    replyCount: 12,
  },
  {
    id: '3',
    username: 'zackjohn',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 1256,
  },
  {
    id: '4',
    username: 'kiero_d',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 983,
    hasReplies: true,
    replyCount: 5,
  },
  {
    id: '5',
    username: 'mis_potter',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 456,
  },
  {
    id: '6',
    username: 'karennne',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 234,
  },
  {
    id: '7',
    username: 'joshua_l',
    text: 'How neatly I write the date in my book',
    timestamp: '22h',
    likes: 123,
  },
];

export const Comments: React.FC<CommentsProps> = ({
  onClose,
  comments = mockComments,
  onAddComment,
}) => {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];
  const [commentText, setCommentText] = useState('');

  const renderComment = ({ item }: { item: Comment }) => (
    <View style={styles.commentItem}>
      <View style={styles.commentAvatar}>
        <Text style={styles.avatarText}>{item.username.charAt(0).toUpperCase()}</Text>
      </View>
      <View style={styles.commentContent}>
        <View style={styles.commentHeader}>
          <Text style={styles.commentUsername}>{item.username}</Text>
          <Text style={styles.commentTimestamp}>{item.timestamp}</Text>
        </View>
        <Text style={styles.commentText}>{item.text}</Text>
        <View style={styles.commentActions}>
          <TouchableOpacity style={styles.likeButton}>
            <Text style={styles.likeIcon}>❤️</Text>
            <Text style={styles.likeCount}>{item.likes}</Text>
          </TouchableOpacity>
          {item.hasReplies && (
            <TouchableOpacity style={styles.repliesButton}>
              <Text style={styles.repliesText}>View replies ({item.replyCount})</Text>
              <Text style={styles.repliesArrow}>▼</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );

  const handleAddComment = () => {
    if (commentText.trim() && onAddComment) {
      onAddComment(commentText.trim());
      setCommentText('');
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>579 comments</Text>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Text style={styles.closeIcon}>✕</Text>
        </TouchableOpacity>
      </View>

      {/* Comments List */}
      <FlatList
        data={comments}
        renderItem={renderComment}
        keyExtractor={(item) => item.id}
        style={styles.commentsList}
        showsVerticalScrollIndicator={false}
      />

      {/* Comment Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Add comment..."
          placeholderTextColor="#9BA1A6"
          value={commentText}
          onChangeText={setCommentText}
          multiline
        />
        <View style={styles.inputActions}>
          <TouchableOpacity style={styles.emojiButton}>
            <Text style={styles.emojiIcon}>😊</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.sendButton, commentText.trim() ? styles.sendButtonActive : null]}
            onPress={handleAddComment}
            disabled={!commentText.trim()}
          >
            <Text style={styles.sendIcon}>📤</Text>
          </TouchableOpacity>
        </View>
      </View>
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
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
    paddingTop: 50,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
  },
  closeButton: {
    position: 'absolute',
    right: 20,
  },
  closeIcon: {
    fontSize: 20,
    color: '#000000',
  },
  commentsList: {
    flex: 1,
  },
  commentItem: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  commentAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E5E5E5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666666',
  },
  commentContent: {
    flex: 1,
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 5,
  },
  commentUsername: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
  },
  commentTimestamp: {
    fontSize: 12,
    color: '#9BA1A6',
  },
  commentText: {
    fontSize: 14,
    color: '#000000',
    lineHeight: 20,
    marginBottom: 8,
  },
  commentActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  likeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 20,
  },
  likeIcon: {
    fontSize: 16,
    marginRight: 5,
  },
  likeCount: {
    fontSize: 12,
    color: '#9BA1A6',
  },
  repliesButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  repliesText: {
    fontSize: 12,
    color: '#9BA1A6',
    marginRight: 5,
  },
  repliesArrow: {
    fontSize: 10,
    color: '#9BA1A6',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderTopWidth: 1,
    borderTopColor: '#E5E5E5',
    backgroundColor: '#FFFFFF',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    maxHeight: 100,
    marginRight: 10,
    fontSize: 14,
    color: '#000000',
  },
  inputActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  emojiButton: {
    marginRight: 10,
  },
  emojiIcon: {
    fontSize: 20,
  },
  sendButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#E5E5E5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonActive: {
    backgroundColor: '#FF2D55',
  },
  sendIcon: {
    fontSize: 16,
    color: '#FFFFFF',
  },
}); 