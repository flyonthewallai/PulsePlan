import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Modal, 
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { 
  X, 
  Calendar, 
  Clock, 
  Flag, 
  BookOpen,
  CheckCircle2,
  PlayCircle,
  Edit3,
  Trash2,
  Sparkles,
  BarChart3,
  Target,
} from 'lucide-react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { useTheme } from '../contexts/ThemeContext';
import { useTasks, Task } from '../contexts/TaskContext';
import { chatAPIService } from '../services/chatService';
import { formatAIResponse, cleanMarkdownText } from '../utils/markdownParser';

type TaskDetailsModalProps = {
  visible: boolean;
  task: Task | null;
  onClose: () => void;
  onEdit?: (task: Task) => void;
};

type AIInsight = {
  type: 'difficulty' | 'time' | 'priority' | 'suggestion';
  title: string;
  content: string;
  icon: React.ReactNode;
};

type CachedInsights = {
  insights: Omit<AIInsight, 'icon'>[];
  timestamp: number;
  taskVersion: string; // Hash of task properties to detect changes
};

const INSIGHTS_CACHE_KEY = '@task_insights_cache';
const CACHE_EXPIRY_HOURS = 24; // Cache expires after 24 hours

export default function TaskDetailsModal({ visible, task, onClose, onEdit }: TaskDetailsModalProps) {
  const { currentTheme } = useTheme();
  const { updateTask, deleteTask } = useTasks();
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [aiInsights, setAiInsights] = useState<AIInsight[]>([]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#FF5757';
      case 'medium': return '#FFD60A'; 
      case 'low': return '#30D158';
      default: return currentTheme.colors.textSecondary;
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
    
    const dateStr = date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
    
    if (diffDays === 0) return `Today at ${timeStr}`;
    if (diffDays === 1) return `Tomorrow at ${timeStr}`;
    if (diffDays === -1) return `Yesterday at ${timeStr}`;
    if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`;
    if (diffDays <= 7) return `In ${diffDays} days at ${timeStr}`;
    
    return `${dateStr} at ${timeStr}`;
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'Not set';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours > 0 && mins > 0) {
      return `${hours}h ${mins}m`;
    } else if (hours > 0) {
      return `${hours}h`;
    } else {
      return `${mins} min`;
    }
  };

  // Generate a simple hash of task properties to detect changes
  const getTaskVersion = (task: Task): string => {
    return `${task.title}-${task.subject}-${task.priority}-${task.status}-${task.estimated_minutes}-${task.due_date}`;
  };

  // Load cached insights from AsyncStorage
  const loadCachedInsights = async (taskId: string, taskVersion: string): Promise<AIInsight[] | null> => {
    try {
      const cacheData = await AsyncStorage.getItem(`${INSIGHTS_CACHE_KEY}_${taskId}`);
      if (!cacheData) return null;

      const cached: CachedInsights = JSON.parse(cacheData);
      
      // Check if cache is expired
      const now = Date.now();
      const cacheAge = (now - cached.timestamp) / (1000 * 60 * 60); // hours
      if (cacheAge > CACHE_EXPIRY_HOURS) {
        await AsyncStorage.removeItem(`${INSIGHTS_CACHE_KEY}_${taskId}`);
        return null;
      }

      // Check if task has changed
      if (cached.taskVersion !== taskVersion) {
        await AsyncStorage.removeItem(`${INSIGHTS_CACHE_KEY}_${taskId}`);
        return null;
      }

      // Convert cached insights back to full AIInsight objects with icons
      const insights: AIInsight[] = cached.insights.map((insight, index) => ({
        ...insight,
        icon: getInsightIcon(insight.type)
      }));

      return insights;
    } catch (error) {
      console.error('Error loading cached insights:', error);
      return null;
    }
  };

  // Save insights to AsyncStorage
  const saveCachedInsights = async (taskId: string, taskVersion: string, insights: AIInsight[]) => {
    try {
      const cacheData: CachedInsights = {
        insights: insights.map(({ icon, ...insight }) => insight), // Remove icon for storage
        timestamp: Date.now(),
        taskVersion
      };
      
      await AsyncStorage.setItem(`${INSIGHTS_CACHE_KEY}_${taskId}`, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Error saving cached insights:', error);
    }
  };

  // Get icon for insight type
  const getInsightIcon = (type: string): React.ReactNode => {
    switch (type) {
      case 'difficulty':
        return <BarChart3 size={16} color={currentTheme.colors.primary} />;
      case 'time':
        return <Clock size={16} color={currentTheme.colors.primary} />;
      case 'priority':
        return <Flag size={16} color={currentTheme.colors.primary} />;
      case 'suggestion':
        return <Sparkles size={16} color={currentTheme.colors.primary} />;
      default:
        return <Target size={16} color={currentTheme.colors.primary} />;
    }
  };

  // Parse AI response and extract structured insights
  const parseAIResponse = (response: string): AIInsight[] => {
    const insights: AIInsight[] = [];
    
    // Use the shared markdown parser for initial cleaning
    const cleanedResponse = formatAIResponse(response);
    
    // Split into paragraphs
    const paragraphs = cleanedResponse
      .split('\n\n')
      .map(p => p.trim())
      .filter(p => p.length > 20);
    
    // Create insights from paragraphs
    for (let i = 0; i < Math.min(4, paragraphs.length); i++) {
      const paragraph = paragraphs[i];
      const type = determineInsightType(paragraph, i);
      const title = generateInsightTitle(type, i);
      
      insights.push({
        type,
        title,
        content: cleanMarkdownText(paragraph),
        icon: getInsightIcon(type)
      });
    }
    
    // If we still don't have enough insights, create fallback ones
    if (insights.length === 0) {
      insights.push({
        type: 'suggestion',
        title: 'AI Insight',
        content: cleanMarkdownText(response),
        icon: getInsightIcon('suggestion')
      });
    }
    
    return insights.slice(0, 4);
  };
  
  // Determine insight type based on content keywords
  const determineInsightType = (content: string, index: number): AIInsight['type'] => {
    const lowerContent = content.toLowerCase();
    
    if (lowerContent.includes('difficulty') || lowerContent.includes('complex') || 
        lowerContent.includes('challenge') || lowerContent.includes('easy') || 
        lowerContent.includes('hard')) {
      return 'difficulty';
    }
    
    if (lowerContent.includes('time') || lowerContent.includes('minutes') || 
        lowerContent.includes('hours') || lowerContent.includes('break') || 
        lowerContent.includes('chunk') || lowerContent.includes('schedule')) {
      return 'time';
    }
    
    if (lowerContent.includes('priority') || lowerContent.includes('urgent') || 
        lowerContent.includes('important') || lowerContent.includes('deadline')) {
      return 'priority';
    }
    
    // Default patterns based on index
    const types: AIInsight['type'][] = ['difficulty', 'time', 'suggestion', 'suggestion'];
    return types[index] || 'suggestion';
  };
  
  // Generate appropriate title based on type
  const generateInsightTitle = (type: AIInsight['type'], index: number): string => {
    const titles = {
      difficulty: ['Complexity Analysis', 'Task Difficulty', 'Challenge Level'],
      time: ['Time Management', 'Scheduling Tip', 'Time Strategy'],
      priority: ['Priority Assessment', 'Urgency Level', 'Priority Insight'],
      suggestion: ['Smart Tip', 'Study Strategy', 'Productivity Tip', 'Recommendation']
    };
    
    const typeIndex = Math.min(index, titles[type].length - 1);
    return titles[type][typeIndex];
  };

  const generateAIInsights = async (task: Task) => {
    if (!task) return;
    
    setLoadingInsights(true);
    
    try {
      const taskVersion = getTaskVersion(task);
      
      // Check cache first
      const cachedInsights = await loadCachedInsights(task.id, taskVersion);
      if (cachedInsights) {
        setAiInsights(cachedInsights);
        setLoadingInsights(false);
        return;
      }

      // Generate new insights if not cached
      const prompt = `Analyze this task and provide specific, actionable insights:

Task: ${task.title}
Subject: ${task.subject}
Due: ${formatDate(task.due_date)}
Priority: ${task.priority}
Status: ${task.status}
Estimated time: ${formatDuration(task.estimated_minutes)}

Please provide 3-4 insights covering:
1. **Task Complexity**: Assess the difficulty and what makes it challenging
2. **Time Management**: Specific suggestions for managing time and breaking down work
3. **Study Strategy**: Best approaches for this subject and task type
4. **Priority & Focus**: Tips for maintaining focus and managing priority

Format each insight clearly with practical, actionable advice.`;

      const response = await chatAPIService.sendMessage([
        { role: 'user', content: prompt }
      ]);

      let insights: AIInsight[] = [];
      
      // Parse AI response if available
      if (response.content) {
        insights = parseAIResponse(response.content);
      }
      
      // Fallback to default insights if parsing failed
      if (insights.length === 0) {
        insights = [
          {
            type: 'difficulty',
            title: 'Complexity Analysis',
            content: 'This task appears to be moderately complex based on the subject and estimated time.',
            icon: <BarChart3 size={16} color={currentTheme.colors.primary} />
          },
          {
            type: 'time',
            title: 'Time Management',
            content: 'Consider breaking this into smaller chunks if it takes longer than 2 hours.',
            icon: <Clock size={16} color={currentTheme.colors.primary} />
          },
          {
            type: 'suggestion',
            title: 'Smart Tip',
            content: 'Work on this during your peak productivity hours for best results.',
            icon: <Sparkles size={16} color={currentTheme.colors.primary} />
          }
        ];
      }

      setAiInsights(insights);
      
      // Cache the generated insights
      await saveCachedInsights(task.id, taskVersion, insights);
      
    } catch (error) {
      console.error('Error generating AI insights:', error);
      // Fallback insights
      const fallbackInsights: AIInsight[] = [
        {
          type: 'suggestion',
          title: 'Quick Tip',
          content: 'Break larger tasks into smaller, manageable chunks for better focus.',
          icon: <Target size={16} color={currentTheme.colors.primary} />
        }
      ];
      setAiInsights(fallbackInsights);
    } finally {
      setLoadingInsights(false);
    }
  };

  useEffect(() => {
    if (visible && task) {
      generateAIInsights(task);
    }
  }, [visible, task]);

  const handleStatusChange = async (newStatus: 'pending' | 'in_progress' | 'completed') => {
    if (!task) return;
    
    try {
      await updateTask(task.id, { status: newStatus });
      onClose();
    } catch (error) {
      Alert.alert('Error', 'Failed to update task status');
    }
  };

  const handleDelete = () => {
    if (!task) return;
    
    Alert.alert(
      'Delete Task',
      'Are you sure you want to delete this task? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteTask(task.id);
              // Clean up cached insights when task is deleted
              await AsyncStorage.removeItem(`${INSIGHTS_CACHE_KEY}_${task.id}`);
              onClose();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete task');
            }
          }
        }
      ]
    );
  };

  const handleEdit = () => {
    if (task && onEdit) {
      onEdit(task);
      onClose();
    }
  };

  if (!task) return null;

  const isOverdue = new Date(task.due_date) < new Date() && task.status !== 'completed';

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <BlurView intensity={20} style={styles.overlay}>
        <View style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
          {/* Header */}
          <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <X color={currentTheme.colors.textSecondary} size={24} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>
              Task Details
            </Text>
            <TouchableOpacity style={styles.editButton} onPress={handleEdit}>
              <Edit3 color={currentTheme.colors.primary} size={20} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Task Header */}
            <View style={styles.taskHeader}>
              <Text style={[styles.taskTitle, { color: currentTheme.colors.textPrimary }]}>
                {task.title}
              </Text>
              
              <View style={styles.statusContainer}>
                <View style={[styles.statusBadge, { 
                  backgroundColor: currentTheme.colors.surface,
                  borderColor: currentTheme.colors.border 
                }]}>
                  <View 
                    style={[
                      styles.statusDot,
                      { backgroundColor: getStatusColor(task.status) },
                    ]} 
                  />
                  <Text style={[styles.statusText, { color: currentTheme.colors.textPrimary }]}>
                    {task.status.replace('_', ' ').charAt(0).toUpperCase() + task.status.replace('_', ' ').slice(1)}
                  </Text>
                </View>
                
                <View style={[styles.priorityBadge, { 
                  backgroundColor: currentTheme.colors.surface,
                  borderColor: currentTheme.colors.border 
                }]}>
                  <View 
                    style={[
                      styles.priorityDot,
                      { backgroundColor: getPriorityColor(task.priority) },
                    ]} 
                  />
                  <Text style={[styles.priorityText, { color: currentTheme.colors.textPrimary }]}>
                    {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                  </Text>
                </View>
              </View>
            </View>

            {/* Task Details */}
            <View style={[styles.detailsCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.detailRow}>
                <BookOpen size={20} color={currentTheme.colors.textSecondary} />
                <View style={styles.detailContent}>
                  <Text style={[styles.detailLabel, { color: currentTheme.colors.textSecondary }]}>Subject</Text>
                  <Text style={[styles.detailValue, { color: currentTheme.colors.textPrimary }]}>{task.subject}</Text>
                </View>
              </View>

              <View style={styles.detailRow}>
                <Calendar size={20} color={isOverdue ? '#FF5757' : currentTheme.colors.textSecondary} />
                <View style={styles.detailContent}>
                  <Text style={[styles.detailLabel, { color: currentTheme.colors.textSecondary }]}>Due Date</Text>
                  <Text style={[styles.detailValue, { color: isOverdue ? '#FF5757' : currentTheme.colors.textPrimary }]}>
                    {formatDate(task.due_date)}
                    {isOverdue && ' (Overdue)'}
                  </Text>
                </View>
              </View>

              <View style={styles.detailRow}>
                <Clock size={20} color={currentTheme.colors.textSecondary} />
                <View style={styles.detailContent}>
                  <Text style={[styles.detailLabel, { color: currentTheme.colors.textSecondary }]}>Estimated Time</Text>
                  <Text style={[styles.detailValue, { color: currentTheme.colors.textPrimary }]}>
                    {formatDuration(task.estimated_minutes)}
                  </Text>
                </View>
              </View>

              {task.description && (
                <View style={styles.detailRow}>
                  <Flag size={20} color={currentTheme.colors.textSecondary} />
                  <View style={styles.detailContent}>
                    <Text style={[styles.detailLabel, { color: currentTheme.colors.textSecondary }]}>Description</Text>
                    <Text style={[styles.detailValue, { color: currentTheme.colors.textPrimary }]}>
                      {task.description}
                    </Text>
                  </View>
                </View>
              )}
            </View>

            {/* AI Insights */}
            <View style={[styles.insightsCard, { backgroundColor: currentTheme.colors.surface }]}>
              <View style={styles.insightsHeader}>
                <Sparkles size={20} color={currentTheme.colors.primary} />
                <Text style={[styles.insightsTitle, { color: currentTheme.colors.textPrimary }]}>
                  AI Insights
                </Text>
                {loadingInsights && <ActivityIndicator size="small" color={currentTheme.colors.primary} />}
              </View>

              {loadingInsights ? (
                <View style={styles.loadingContainer}>
                  <Text style={[styles.loadingText, { color: currentTheme.colors.textSecondary }]}>
                    Analyzing task...
                  </Text>
                </View>
              ) : (
                aiInsights.map((insight, index) => (
                  <View key={index} style={[
                    styles.insightItem,
                    index === aiInsights.length - 1 && styles.insightItemLast
                  ]}>
                    <View style={styles.insightHeader}>
                      {insight.icon}
                      <Text style={[styles.insightTitle, { color: currentTheme.colors.textPrimary }]}>
                        {insight.title}
                      </Text>
                    </View>
                    <Text style={[styles.insightContent, { color: currentTheme.colors.textSecondary }]}>
                      {insight.content}
                    </Text>
                  </View>
                ))
              )}
            </View>

            {/* Quick Actions */}
            <View style={styles.actionsContainer}>
              <Text style={[styles.actionsTitle, { color: currentTheme.colors.textPrimary }]}>
                Quick Actions
              </Text>
              
              <View style={styles.actionButtons}>
                <View style={styles.primaryActions}>
                  {task.status === 'pending' && (
                    <TouchableOpacity
                      style={[styles.actionButton, { 
                        backgroundColor: currentTheme.colors.surface,
                        borderColor: currentTheme.colors.border
                      }]}
                      onPress={() => handleStatusChange('in_progress')}
                    >
                      <PlayCircle size={18} color={currentTheme.colors.primary} />
                      <Text style={[styles.actionButtonText, { color: currentTheme.colors.textPrimary }]}>Start Task</Text>
                    </TouchableOpacity>
                  )}
                  
                  {task.status !== 'completed' && (
                    <TouchableOpacity
                      style={[styles.actionButton, { 
                        backgroundColor: currentTheme.colors.surface,
                        borderColor: currentTheme.colors.border
                      }]}
                      onPress={() => handleStatusChange('completed')}
                    >
                      <CheckCircle2 size={18} color="#30D158" />
                      <Text style={[styles.actionButtonText, { color: currentTheme.colors.textPrimary }]}>Complete</Text>
                    </TouchableOpacity>
                  )}
                </View>
                
                <TouchableOpacity
                  style={[styles.deleteButton, { 
                    backgroundColor: currentTheme.colors.surface,
                    borderColor: currentTheme.colors.border
                  }]}
                  onPress={handleDelete}
                >
                  <Trash2 size={18} color="#FF5757" />
                  <Text style={[styles.deleteButtonText, { color: currentTheme.colors.textPrimary }]}>Delete</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </BlurView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  modalContainer: {
    flex: 1,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    marginTop: 60,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  editButton: {
    padding: 8,
    borderRadius: 12,
    backgroundColor: 'rgba(79, 140, 255, 0.15)',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  taskHeader: {
    paddingTop: 24,
    paddingBottom: 20,
  },
  taskTitle: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 16,
    lineHeight: 28,
  },
  statusContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  priorityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
  },
  priorityText: {
    fontSize: 14,
    fontWeight: '500',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  detailsCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  detailContent: {
    flex: 1,
    marginLeft: 12,
  },
  detailLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 20,
  },
  insightsCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  insightsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  insightsTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
    opacity: 0.7,
  },
  insightItem: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  insightItemLast: {
    borderBottomWidth: 0,
    marginBottom: 0,
    paddingBottom: 0,
  },
  insightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  insightContent: {
    fontSize: 16,
    lineHeight: 22,
    marginLeft: 28,
    opacity: 0.8,
  },
  actionsContainer: {
    marginBottom: 32,
  },
  actionsTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 12,
    opacity: 0.7,
  },
  actionButtons: {
    gap: 8,
  },
  primaryActions: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 8,
    flex: 1,
    minWidth: 100,
    justifyContent: 'center',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 8,
    justifyContent: 'center',
  },
  deleteButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
}); 