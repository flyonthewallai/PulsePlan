import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  Animated,
} from 'react-native';
import { X, Calendar, Clock, MapPin, Users, Video } from 'lucide-react-native';
import { GestureHandlerRootView, PanGestureHandler as RNGHPanGestureHandler, State as GestureState } from 'react-native-gesture-handler';
import { useTheme } from '@/contexts/ThemeContext';

interface EventsCardProps {
  onPress?: () => void;
}

// Hardcoded events data for now
const hardcodedEvents = [
  {
    id: '1',
    title: 'Calculus Final Exam',
    type: 'exam',
    subject: 'Mathematics',
    start_date: '2024-03-25T09:00:00Z',
    end_date: '2024-03-25T11:00:00Z',
    location: 'Room 101, Science Building',
    priority: 'high',
    status: 'scheduled',
    preparation_time_minutes: 120,
  },
  {
    id: '2',
    title: 'Team Project Meeting',
    type: 'meeting',
    start_date: '2024-03-24T14:00:00Z',
    end_date: '2024-03-24T15:00:00Z',
    location_type: 'virtual',
    meeting_url: 'https://zoom.us/j/123456789',
    priority: 'medium',
    status: 'scheduled',
    attendees: ['teammate1@email.com', 'teammate2@email.com'],
  },
  {
    id: '3',
    title: 'Computer Science Lecture',
    type: 'class',
    subject: 'Computer Science',
    start_date: '2024-03-24T10:00:00Z',
    end_date: '2024-03-24T11:30:00Z',
    location: 'Lecture Hall A',
    priority: 'medium',
    status: 'scheduled',
  },
  {
    id: '4',
    title: 'Study Group Session',
    type: 'social',
    subject: 'Physics',
    start_date: '2024-03-23T16:00:00Z',
    end_date: '2024-03-23T18:00:00Z',
    location: 'Library Study Room 3',
    priority: 'low',
    status: 'scheduled',
  },
  {
    id: '5',
    title: 'Assignment Due',
    type: 'deadline',
    subject: 'English',
    start_date: '2024-03-26T23:59:00Z',
    priority: 'high',
    status: 'scheduled',
  },
];

const EventsCard: React.FC<EventsCardProps> = ({ onPress }) => {
  const { currentTheme } = useTheme();
  const [showModal, setShowModal] = useState(false);
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const cardTranslateX = React.useRef(new Animated.Value(0)).current;

  // Filter to upcoming events
  const upcomingEvents = hardcodedEvents.filter(event => 
    new Date(event.start_date) >= new Date() && event.status === 'scheduled'
  );

  // Card swipe handlers
  const onCardGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: cardTranslateX } }],
    { useNativeDriver: true }
  );

  const onCardHandlerStateChange = (event: any) => {
    const { state, translationX: gestureTranslationX, velocityX } = event.nativeEvent;
    
    if (state === GestureState.END) {
      // If swiped left significantly or with high velocity, go to next event
      if ((gestureTranslationX < -40 || velocityX < -200) && upcomingEvents.length > 1) {
        // Animate slide out to left
        Animated.timing(cardTranslateX, {
          toValue: -400,
          duration: 150,
          useNativeDriver: true,
        }).start(() => {
          // Update to next event
          setCurrentEventIndex((prevIndex) => (prevIndex + 1) % upcomingEvents.length);
          // Reset position and animate in from right
          cardTranslateX.setValue(400);
          Animated.timing(cardTranslateX, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }).start();
        });
      }
      // If swiped right significantly or with high velocity, go to previous event
      else if ((gestureTranslationX > 40 || velocityX > 200) && upcomingEvents.length > 1) {
        // Animate slide out to right
        Animated.timing(cardTranslateX, {
          toValue: 400,
          duration: 150,
          useNativeDriver: true,
        }).start(() => {
          // Update to previous event
          setCurrentEventIndex((prevIndex) => (prevIndex - 1 + upcomingEvents.length) % upcomingEvents.length);
          // Reset position and animate in from left
          cardTranslateX.setValue(-400);
          Animated.timing(cardTranslateX, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }).start();
        });
      } else {
        // Snap back to original position
        Animated.spring(cardTranslateX, {
          toValue: 0,
          tension: 120,
          friction: 10,
          useNativeDriver: true,
        }).start();
      }
    } else if (state === GestureState.CANCELLED || state === GestureState.FAILED) {
      // Reset position if gesture is cancelled
      Animated.spring(cardTranslateX, {
        toValue: 0,
        tension: 120,
        friction: 10,
        useNativeDriver: true,
      }).start();
    }
  };

  const currentEvent = upcomingEvents[currentEventIndex] || upcomingEvents[0];

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'exam': return '#FF3B30';
      case 'meeting': return '#007AFF';
      case 'class': return '#34C759';
      case 'deadline': return '#FF9500';
      case 'social': return '#AF52DE';
      case 'appointment': return '#5AC8FA';
      default: return '#8E8E93';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF3B30';
      case 'medium': return '#FF9500';
      case 'low': return '#34C759';
      case 'critical': return '#FF0000';
      default: return '#8E8E93';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getEventIcon = (event: any) => {
    if (event.location_type === 'virtual' || event.meeting_url) {
      return <Video size={12} color={currentTheme.colors.textSecondary} />;
    }
    if (event.attendees && event.attendees.length > 0) {
      return <Users size={12} color={currentTheme.colors.textSecondary} />;
    }
    if (event.location) {
      return <MapPin size={12} color={currentTheme.colors.textSecondary} />;
    }
    return <Calendar size={12} color={currentTheme.colors.textSecondary} />;
  };

  const getEventTypeLabel = (type: string) => {
    switch (type) {
      case 'exam': return 'EXAM';
      case 'meeting': return 'MEETING';
      case 'class': return 'CLASS';
      case 'deadline': return 'DEADLINE';
      case 'social': return 'SOCIAL';
      case 'appointment': return 'APPOINTMENT';
      default: return type.toUpperCase();
    }
  };

  return (
    <GestureHandlerRootView>
      <RNGHPanGestureHandler
        onGestureEvent={onCardGestureEvent}
        onHandlerStateChange={onCardHandlerStateChange}
        activeOffsetX={[-10, 10]}
        failOffsetY={[-30, 30]}
        shouldCancelWhenOutside={false}
      >
        <Animated.View
          style={{
            transform: [{ translateX: cardTranslateX }],
          }}
        >
          <TouchableOpacity
            style={[
              styles.card,
              {
                backgroundColor: currentTheme.colors.surface
              }
            ]}
            onPress={() => setShowModal(true)}
            activeOpacity={0.8}
          >
            <View style={styles.cardContent}>
              {/* Current event item */}
              <View style={styles.eventItem}>
                <View style={styles.eventHeader}>
                  <View style={[styles.typeBadge, { backgroundColor: getTypeColor(currentEvent?.type || 'other') + '20' }]}>
                    <Text style={[styles.typeText, { color: getTypeColor(currentEvent?.type || 'other') }]}>
                      {getEventTypeLabel(currentEvent?.type || 'other')}
                    </Text>
                  </View>
                  <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(currentEvent?.priority || 'medium') + '20' }]}>
                    <Text style={[styles.priorityText, { color: getPriorityColor(currentEvent?.priority || 'medium') }]}>
                      {currentEvent?.priority?.toUpperCase() || 'MEDIUM'}
                    </Text>
                  </View>
                </View>
                
                <View style={styles.eventContent}>
                  <Text style={[
                    styles.eventTitle,
                    { color: currentTheme.colors.textPrimary }
                  ]}>
                    {currentEvent?.title || 'No upcoming events'}
                  </Text>
                  
                  {currentEvent && (
                    <>
                      {currentEvent.subject && (
                        <Text style={[styles.eventSubject, { color: currentTheme.colors.textSecondary }]}>
                          {currentEvent.subject}
                        </Text>
                      )}
                      
                      <View style={styles.eventMeta}>
                        <View style={styles.eventMetaItem}>
                          <Calendar size={12} color={currentTheme.colors.textSecondary} />
                          <Text style={[styles.eventMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {formatDate(currentEvent.start_date)}
                          </Text>
                        </View>
                        <View style={styles.eventMetaItem}>
                          <Clock size={12} color={currentTheme.colors.textSecondary} />
                          <Text style={[styles.eventMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {formatTime(currentEvent.start_date)}
                          </Text>
                        </View>
                        <View style={styles.eventMetaItem}>
                          {getEventIcon(currentEvent)}
                          <Text style={[styles.eventMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {currentEvent.location || 
                             (currentEvent.location_type === 'virtual' ? 'Virtual' : 
                              currentEvent.attendees ? `${currentEvent.attendees.length} attendees` : 'Event')}
                          </Text>
                        </View>
                      </View>
                    </>
                  )}
                </View>
              </View>

              {/* Status indicator */}
              {upcomingEvents.length > 1 && (
                <Text style={[styles.statusText, { color: currentTheme.colors.textSecondary }]}>
                  {currentEventIndex + 1} of {upcomingEvents.length}
                </Text>
              )}

              {/* Progress indicators */}
              <View style={styles.progressContainer}>
                {upcomingEvents.slice(0, 4).map((event, index) => (
                  <View
                    key={event.id}
                    style={[
                      styles.progressDot,
                      { backgroundColor: getTypeColor(event.type) },
                      index === currentEventIndex && styles.progressDotActive
                    ]}
                  />
                ))}
                {upcomingEvents.length > 4 && (
                  <Text style={styles.moreIndicator}>•••</Text>
                )}
              </View>
            </View>
          </TouchableOpacity>
        </Animated.View>
      </RNGHPanGestureHandler>

      {/* Full Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <GestureHandlerRootView style={{ flex: 1 }}>
          <View style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
            {/* Header */}
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <X size={24} color={currentTheme.colors.textPrimary} />
              </TouchableOpacity>
              <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>
                Events
              </Text>
              <View style={{ width: 24 }} />
            </View>

            {/* Events list */}
            <ScrollView style={styles.eventsList} showsVerticalScrollIndicator={false}>
              {upcomingEvents.map((event) => (
                <TouchableOpacity
                  key={event.id}
                  style={[styles.modalEventItem, { backgroundColor: currentTheme.colors.surface }]}
                >
                  <View style={styles.modalEventContent}>
                    <View style={styles.modalEventHeader}>
                      <View style={[styles.typeBadge, { backgroundColor: getTypeColor(event.type) + '20' }]}>
                        <Text style={[styles.typeText, { color: getTypeColor(event.type) }]}>
                          {getEventTypeLabel(event.type)}
                        </Text>
                      </View>
                      <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(event.priority) + '20' }]}>
                        <Text style={[styles.priorityText, { color: getPriorityColor(event.priority) }]}>
                          {event.priority.toUpperCase()}
                        </Text>
                      </View>
                    </View>
                    
                    <Text style={[styles.modalEventTitle, { color: currentTheme.colors.textPrimary }]}>
                      {event.title}
                    </Text>
                    
                    {event.subject && (
                      <Text style={[styles.modalEventSubject, { color: currentTheme.colors.textSecondary }]}>
                        {event.subject}
                      </Text>
                    )}
                    
                    <View style={styles.modalEventMeta}>
                      <View style={styles.eventMetaItem}>
                        <Calendar size={12} color={currentTheme.colors.textSecondary} />
                        <Text style={[styles.eventMetaText, { color: currentTheme.colors.textSecondary }]}>
                          {formatDate(event.start_date)}
                        </Text>
                      </View>
                      <View style={styles.eventMetaItem}>
                        <Clock size={12} color={currentTheme.colors.textSecondary} />
                        <Text style={[styles.eventMetaText, { color: currentTheme.colors.textSecondary }]}>
                          {formatTime(event.start_date)}
                          {event.end_date && ` - ${formatTime(event.end_date)}`}
                        </Text>
                      </View>
                      {(event.location || event.location_type === 'virtual' || event.attendees) && (
                        <View style={styles.eventMetaItem}>
                          {getEventIcon(event)}
                          <Text style={[styles.eventMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {event.location || 
                             (event.location_type === 'virtual' ? 'Virtual Meeting' : 
                              event.attendees ? `${event.attendees.length} attendees` : 'Event')}
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>
                </TouchableOpacity>
              ))}

              {upcomingEvents.length === 0 && (
                <View style={styles.emptyState}>
                  <Text style={[styles.emptyText, { color: currentTheme.colors.textSecondary }]}>
                    No upcoming events
                  </Text>
                  <Text style={[styles.emptySubtext, { color: currentTheme.colors.textSecondary }]}>
                    Create a new event to get started
                  </Text>
                </View>
              )}
            </ScrollView>
          </View>
        </GestureHandlerRootView>
      </Modal>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 24,
  },
  cardContent: {
    gap: 8,
  },
  eventItem: {
    gap: 12,
  },
  eventHeader: {
    flexDirection: 'row',
    gap: 8,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  typeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  eventContent: {
    gap: 4,
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  eventSubject: {
    fontSize: 13,
    fontWeight: '500',
    opacity: 0.8,
  },
  eventMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
    marginTop: 4,
  },
  eventMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  eventMetaText: {
    fontSize: 12,
    fontWeight: '500',
  },
  statusText: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 4,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 4,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  progressDotActive: {
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.6)',
  },
  moreIndicator: {
    color: '#666666',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  eventsList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  modalEventItem: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  modalEventContent: {
    gap: 8,
  },
  modalEventHeader: {
    flexDirection: 'row',
    gap: 8,
  },
  modalEventTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalEventSubject: {
    fontSize: 13,
    fontWeight: '500',
    opacity: 0.8,
  },
  modalEventMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
    marginTop: 4,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
  },
});

export default EventsCard; 