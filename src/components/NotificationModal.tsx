import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ScrollView,
} from 'react-native';
import { X, MessageSquare, Calendar, CheckCircle, AlertCircle } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';

interface NotificationModalProps {
  visible: boolean;
  onClose: () => void;
}

interface NotificationItem {
  id: string;
  title: string;
  subtitle: string;
  timestamp: string;
  icon: React.ReactNode;
  unread?: boolean;
}

export default function NotificationModal({ visible, onClose }: NotificationModalProps) {
  const { currentTheme } = useTheme();

  const iconGray = '#9CA3AF';

  const notifications: NotificationItem[] = [
    {
      id: '1',
      title: "Task reminder: Complete project proposal",
      subtitle: "Due in 2 hours. Don't forget to submit your proposal.",
      timestamp: "11:30 AM",
      icon: <CheckCircle color={iconGray} size={20} />,
      unread: true,
    },
    {
      id: '2',
      title: "Calendar event starting soon",
      subtitle: "Team meeting in conference room A starts in 15 minutes.",
      timestamp: "10:45 AM",
      icon: <Calendar color={iconGray} size={20} />,
      unread: false,
    },
    {
      id: '3',
      title: "New message from Sarah",
      subtitle: "Hey, can we reschedule our meeting for tomorrow?",
      timestamp: "9:22 AM",
      icon: <MessageSquare color={iconGray} size={20} />,
      unread: false,
    },
    {
      id: '4',
      title: "Study session reminder",
      subtitle: "Chemistry exam prep session starts in 30 minutes.",
      timestamp: "8:30 AM",
      icon: <AlertCircle color={iconGray} size={20} />,
      unread: false,
    },
  ];

  const renderNotification = (notification: NotificationItem) => (
    <TouchableOpacity 
      key={notification.id}
      style={[styles.notificationItem, { backgroundColor: currentTheme.colors.surface }]}
      activeOpacity={0.7}
    >
      <View style={styles.notificationContent}>
        <View style={styles.notificationHeader}>
          <View style={styles.iconContainer}>
            {notification.icon}
          </View>
          <View style={styles.notificationTextContainer}>
            <Text style={[styles.notificationTitle, { color: currentTheme.colors.textPrimary }]}>
              {notification.title}
            </Text>
            <Text style={[styles.notificationSubtitle, { color: currentTheme.colors.textSecondary }]}>
              {notification.subtitle}
            </Text>
          </View>
          <View style={styles.timestampContainer}>
            <Text style={[styles.timestamp, { color: currentTheme.colors.textSecondary }]}>
              {notification.timestamp}
            </Text>
            {notification.unread && (
              <View style={styles.unreadDot} />
            )}
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={currentTheme.colors.background} />
        
        {/* Header */}
        <View style={[styles.header, { backgroundColor: currentTheme.colors.background }]}>
          <View style={styles.headerLeft} />
          
          <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
            Notifications
          </Text>
          
          <TouchableOpacity 
            style={styles.closeButton}
            onPress={onClose}
          >
            <X color={currentTheme.colors.textPrimary} size={24} />
          </TouchableOpacity>
        </View>

        {/* Content */}
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
        >
          {notifications.map(renderNotification)}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 0.5,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  headerLeft: {
    width: 40,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  closeButton: {
    padding: 8,
    marginRight: -8,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },
  notificationItem: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  notificationContent: {
    flex: 1,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconContainer: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  notificationTextContainer: {
    flex: 1,
    marginRight: 12,
  },
  notificationTitle: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
    marginBottom: 4,
  },
  notificationSubtitle: {
    fontSize: 14,
    lineHeight: 18,
    opacity: 0.8,
  },
  timestampContainer: {
    alignItems: 'flex-end',
  },
  timestamp: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 4,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#4F8CFF',
  },
}); 