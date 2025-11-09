import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { X, Clock, TrendingUp, AlertTriangle, Calendar, CheckCircle2, Circle, MapPin, Users, Video } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import { useTasks } from '@/contexts/TaskContext';

interface DailyOverviewModalProps {
  visible: boolean;
  onClose: () => void;
}

// Hardcoded events data (same as EventsCard)
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

const DailyOverviewModal: React.FC<DailyOverviewModalProps> = ({ visible, onClose }) => {
  const { currentTheme } = useTheme();
  const { tasks, toggleTask } = useTasks();

  // Filter today's tasks and events
  const today = new Date().toDateString();
  const todayTasks = tasks.filter(task => {
    const taskDate = new Date(task.due_date).toDateString();
    return taskDate === today;
  }).sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime());

  const todayEvents = hardcodedEvents.filter(event => {
    const eventDate = new Date(event.start_date).toDateString();
    return eventDate === today && event.status === 'scheduled';
  }).sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());

  // Calculate insights
  const totalTasks = todayTasks.length;
  const totalEvents = todayEvents.length;
  const totalItems = totalTasks + totalEvents;
  const completedTasks = todayTasks.filter(task => task.status === 'completed').length;
  const highPriorityTasks = todayTasks.filter(task => task.priority === 'high').length;
  const highPriorityEvents = todayEvents.filter(event => event.priority === 'high').length;
  const totalEstimatedTime = todayTasks.reduce((sum, task) => sum + (task.estimated_minutes || 0), 0);
  const totalEventTime = todayEvents.reduce((sum, event) => {
    if (event.end_date) {
      const duration = (new Date(event.end_date).getTime() - new Date(event.start_date).getTime()) / (1000 * 60);
      return sum + duration;
    }
    return sum;
  }, 0);
  
  // Get dominant subject
  const subjectCounts = todayTasks.reduce((acc, task) => {
    acc[task.subject] = (acc[task.subject] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const dominantSubject = Object.entries(subjectCounts).sort(([,a], [,b]) => b - a)[0]?.[0] || 'General';

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

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0 && mins > 0) return `${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h`;
    return `${mins}m`;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF3B30';
      case 'medium': return '#FF9500';
      case 'low': return '#34C759';
      default: return '#666666';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#30D158';
      case 'in_progress': return '#FFD60A';
      case 'pending': return currentTheme.colors.textSecondary;
      default: return currentTheme.colors.textSecondary;
    }
  };

  const getCompletionPercentage = () => {
    if (totalTasks === 0) return 0;
    return Math.round((completedTasks / totalTasks) * 100);
  };

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
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={onClose}
          >
            <X color={currentTheme.colors.textPrimary} size={24} />
          </TouchableOpacity>
          
          <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
            Daily Overview
          </Text>
          
          <View style={styles.placeholder} />
        </View>

        {/* Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* AI Insights Section */}
          <View style={[styles.insightsCard, { backgroundColor: currentTheme.colors.surface }]}>
            <View style={styles.insightsHeader}>
              <Text style={[styles.insightsTitle, { color: currentTheme.colors.textSecondary }]}>
                TODAY'S ANALYTICS
              </Text>
            </View>
            
            <View style={styles.insightsGrid}>
              <View style={styles.insightItem}>
                <Text style={[styles.insightValue, { color: currentTheme.colors.textPrimary }]}>
                  {totalItems}
                </Text>
                <Text style={[styles.insightLabel, { color: currentTheme.colors.textSecondary }]}>
                  Total Items
                </Text>
              </View>
              
              <View style={styles.insightItem}>
                <Text style={[styles.insightValue, { color: currentTheme.colors.textPrimary }]}>
                  {formatDuration(totalEstimatedTime + totalEventTime)}
                </Text>
                <Text style={[styles.insightLabel, { color: currentTheme.colors.textSecondary }]}>
                  Total Time
                </Text>
              </View>
              
              <View style={styles.insightItem}>
                <Text style={[styles.insightValue, { color: currentTheme.colors.textPrimary }]}>
                  {totalTasks > 0 ? getCompletionPercentage() : 0}%
                </Text>
                <Text style={[styles.insightLabel, { color: currentTheme.colors.textSecondary }]}>
                  Tasks Done
                </Text>
              </View>
            </View>

            {/* Key Insights */}
            {(highPriorityTasks > 0 || highPriorityEvents > 0 || dominantSubject !== 'General' || (totalEstimatedTime + totalEventTime) > 480) && (
              <View style={styles.keyInsights}>
                {(highPriorityTasks + highPriorityEvents) > 0 && (
                  <View style={styles.insightRow}>
                    <AlertTriangle size={14} color="#FF9500" />
                    <Text style={[styles.insightText, { color: currentTheme.colors.textSecondary }]}>
                      {highPriorityTasks + highPriorityEvents} high-priority item{(highPriorityTasks + highPriorityEvents) > 1 ? 's' : ''} require focus
                    </Text>
                  </View>
                )}
                
                {dominantSubject !== 'General' && (
                  <View style={styles.insightRow}>
                    <TrendingUp size={14} color={currentTheme.colors.primary} />
                    <Text style={[styles.insightText, { color: currentTheme.colors.textSecondary }]}>
                      Heaviest focus on {dominantSubject} today
                    </Text>
                  </View>
                )}
                
                {totalEvents > 0 && (
                  <View style={styles.insightRow}>
                    <Calendar size={14} color={currentTheme.colors.primary} />
                    <Text style={[styles.insightText, { color: currentTheme.colors.textSecondary }]}>
                      {totalEvents} event{totalEvents > 1 ? 's' : ''} scheduled today
                    </Text>
                  </View>
                )}
                
                {(totalEstimatedTime + totalEventTime) > 480 && (
                  <View style={styles.insightRow}>
                    <Clock size={14} color="#FF9500" />
                    <Text style={[styles.insightText, { color: currentTheme.colors.textSecondary }]}>
                      Heavy schedule - consider prioritizing key items
                    </Text>
                  </View>
                )}
              </View>
            )}
          </View>

          {/* Today's Tasks Section */}
          <View style={styles.taskListSection}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
              TODAY'S TASKS
            </Text>
            
            {todayTasks.length > 0 ? (
              <View style={styles.taskList}>
                {todayTasks.map((task, index) => (
                  <TouchableOpacity
                    key={task.id}
                    style={[styles.modalTaskItem, { backgroundColor: currentTheme.colors.surface }]}
                    onPress={() => toggleTask(task.id)}
                  >
                    <TouchableOpacity
                      style={[
                        styles.modalCheckbox,
                        { borderColor: currentTheme.colors.border },
                        task.status === 'completed' && { 
                          backgroundColor: getPriorityColor(task.priority), 
                          borderColor: getPriorityColor(task.priority) 
                        }
                      ]}
                      onPress={() => toggleTask(task.id)}
                    >
                      {task.status === 'completed' && (
                        <Text style={styles.modalCheckmark}>✓</Text>
                      )}
                    </TouchableOpacity>
                    <View style={styles.modalTaskContent}>
                      <Text style={[
                        styles.modalTaskText,
                        { color: currentTheme.colors.textPrimary },
                        task.status === 'completed' && { 
                          textDecorationLine: 'line-through',
                          color: currentTheme.colors.textSecondary 
                        }
                      ]}>
                        {task.title}
                      </Text>
                      <View style={styles.modalTaskMeta}>
                        <View style={styles.taskMetaItem}>
                          <Calendar size={12} color={currentTheme.colors.textSecondary} />
                          <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {formatDate(task.due_date)}
                          </Text>
                        </View>
                        <View style={styles.taskMetaItem}>
                          <Clock size={12} color={currentTheme.colors.textSecondary} />
                          <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {formatTime(task.due_date)}
                          </Text>
                        </View>
                        <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(task.priority) + '20' }]}>
                          <Text style={[styles.priorityText, { color: getPriorityColor(task.priority) }]}>
                            {task.priority.toUpperCase()}
                          </Text>
                        </View>
                      </View>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            ) : (
              <View style={styles.emptyState}>
                <Calendar size={48} color={currentTheme.colors.textSecondary} style={{ opacity: 0.5 }} />
                <Text style={[styles.emptyTitle, { color: currentTheme.colors.textPrimary }]}>
                  No tasks for today
                </Text>
                <Text style={[styles.emptyText, { color: currentTheme.colors.textSecondary }]}>
                  Enjoy your free day or add some tasks to get started
                </Text>
              </View>
            )}
          </View>

          {/* Today's Events Section */}
          <View style={styles.taskListSection}>
            <Text style={[styles.sectionTitle, { color: currentTheme.colors.textSecondary }]}>
              TODAY'S EVENTS
            </Text>
            
            {todayEvents.length > 0 ? (
              <View style={styles.taskList}>
                {todayEvents.map((event, index) => (
                  <TouchableOpacity
                    key={event.id}
                    style={[styles.modalTaskItem, { backgroundColor: currentTheme.colors.surface }]}
                  >
                    <View style={[styles.eventTypeIndicator, { backgroundColor: getTypeColor(event.type) }]} />
                    <View style={styles.modalTaskContent}>
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
                      <Text style={[styles.modalTaskText, { color: currentTheme.colors.textPrimary }]}>
                        {event.title}
                      </Text>
                      {event.subject && (
                        <Text style={[styles.modalEventSubject, { color: currentTheme.colors.textSecondary }]}>
                          {event.subject}
                        </Text>
                      )}
                      <View style={styles.modalTaskMeta}>
                        <View style={styles.taskMetaItem}>
                          <Calendar size={12} color={currentTheme.colors.textSecondary} />
                          <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {formatDate(event.start_date)}
                          </Text>
                        </View>
                        <View style={styles.taskMetaItem}>
                          <Clock size={12} color={currentTheme.colors.textSecondary} />
                          <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                            {formatTime(event.start_date)}
                            {event.end_date && ` - ${formatTime(event.end_date)}`}
                          </Text>
                        </View>
                        {(event.location || event.location_type === 'virtual' || event.attendees) && (
                          <View style={styles.taskMetaItem}>
                            {getEventIcon(event)}
                            <Text style={[styles.taskMetaText, { color: currentTheme.colors.textSecondary }]}>
                              {event.location || 
                               (event.location_type === 'virtual' ? 'Virtual' : 
                                event.attendees ? `${event.attendees.length} attendees` : 'Event')}
                            </Text>
                          </View>
                        )}
                      </View>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            ) : (
              <View style={styles.emptyState}>
                <Calendar size={48} color={currentTheme.colors.textSecondary} style={{ opacity: 0.5 }} />
                <Text style={[styles.emptyTitle, { color: currentTheme.colors.textPrimary }]}>
                  No events for today
                </Text>
                <Text style={[styles.emptyText, { color: currentTheme.colors.textSecondary }]}>
                  Your schedule is clear today
                </Text>
              </View>
            )}
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

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
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  placeholder: {
    width: 40,
    height: 40,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  insightsCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  insightsHeader: {
    marginBottom: 16,
  },
  insightsTitle: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  insightsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  insightItem: {
    alignItems: 'center',
    flex: 1,
  },
  insightValue: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 4,
  },
  insightLabel: {
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
  },
  keyInsights: {
    gap: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  insightRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  insightText: {
    fontSize: 13,
    fontWeight: '500',
    flex: 1,
  },
  taskListSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  taskList: {
    paddingHorizontal: 0,
  },
  modalTaskItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderRadius: 12,
    gap: 12,
    marginBottom: 8,
  },
  modalCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  modalCheckmark: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  modalTaskContent: {
    flex: 1,
  },
  modalTaskText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  modalTaskMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
  },
  taskMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  taskMetaText: {
    fontSize: 12,
    fontWeight: '500',
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '600',
  },
  eventTypeIndicator: {
    width: 4,
    height: 24,
    borderRadius: 2,
    marginRight: 8,
    marginTop: 2,
  },
  modalEventHeader: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 4,
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
  modalEventSubject: {
    fontSize: 13,
    fontWeight: '500',
    opacity: 0.8,
    marginBottom: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default DailyOverviewModal; 