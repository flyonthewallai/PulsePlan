import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  Dimensions, 
  Alert,
  PanResponder,
  Animated,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { GestureHandlerRootView, LongPressGestureHandler, PanGestureHandler, State } from 'react-native-gesture-handler';
import { Task, useTasks } from '../contexts/TaskContext';
import { useTheme } from '../contexts/ThemeContext';
import TaskCreateModal from './TaskCreateModal';
import TaskDetailsModal from './TaskDetailsModal';

interface HourlyScheduleViewProps {
  tasks: Task[];
  studyStartHour: number;
  studyEndHour: number;
  date: Date;
}

interface DraggedTask extends Task {
  isDragging: boolean;
  startY: number;
  currentY: number;
}

interface TemporaryTask {
  id: string;
  startY: number;
  currentY: number;
  isDragging: boolean;
  hour: number;
}

const HOUR_HEIGHT = 60;
const HOUR_BORDER_HEIGHT = 1;
const TOTAL_HOUR_HEIGHT = HOUR_HEIGHT + HOUR_BORDER_HEIGHT;
const TIME_INDICATOR_HEIGHT = 20;
const { width } = Dimensions.get('window');

export default function HourlyScheduleView({ 
  tasks, 
  studyStartHour, 
  studyEndHour, 
  date 
}: HourlyScheduleViewProps) {
  const { updateTask, refreshTasks, loading } = useTasks();
  const { currentTheme } = useTheme();
  const instanceId = useRef(Date.now().toString()).current;
  const [draggedTask, setDraggedTask] = useState<DraggedTask | null>(null);
  const [temporaryTask, setTemporaryTask] = useState<TemporaryTask | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [newTaskHour, setNewTaskHour] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const [hasDragged, setHasDragged] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const panRef = useRef(new Animated.ValueXY()).current;
  const tempPanRef = useRef(new Animated.ValueXY()).current;
  const taskCreationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scheduleRef = useRef<View>(null);
  
  // Ensure we have valid study hours with fallbacks
  const validStartHour = studyStartHour || 9;
  const validEndHour = studyEndHour || 17;
  
  // Create array of hours between study start and end
  const studyHours: number[] = [];
  for (let hour = validStartHour; hour <= validEndHour; hour++) {
    studyHours.push(hour);
  }

  const formatHour = (hour: number) => {
    const time = new Date();
    time.setHours(hour, 0, 0, 0);
    return time.toLocaleTimeString('en-US', {
      hour: 'numeric',
      hour12: true,
    });
  };

  const getTasksForHour = (hour: number) => {
    return tasks.filter(task => {
      const taskTime = new Date(task.due_date);
      const taskHour = taskTime.getHours();
      return taskHour === hour && task.id !== draggedTask?.id;
    });
  };

  const getHourFromPosition = (y: number) => {
    const hourIndex = Math.floor(y / TOTAL_HOUR_HEIGHT);
    return validStartHour + Math.max(0, Math.min(hourIndex, studyHours.length - 1));
  };

  const getSubjectColor = (subject: string) => {
    const colors = {
      'Math': '#FF6B6B',
      'Mathematics': '#FF6B6B',
      'Science': '#4ECDC4',
      'Physics': '#4ECDC4',
      'Chemistry': '#4ECDC4',
      'Biology': '#4ECDC4',
      'Computer Science': '#45B7D1',
      'History': '#FFD93D',
      'English': '#95E1D3',
      'Literature': '#95E1D3',
      'Psychology': '#DDA0DD',
      'General': '#9B9B9B'
    };
    return colors[subject as keyof typeof colors] || '#9B9B9B';
  };

  const handleLongPress = (hour: number) => {
    if (isScrolling) {
      console.log('Ignoring long press during scroll');
      return;
    }
    
    const hourIndex = hour - validStartHour;
    const startY = hourIndex * TOTAL_HOUR_HEIGHT;
    
    const tempTask = {
      id: 'temp-' + Date.now(),
      startY,
      currentY: startY,
      isDragging: false,
      hour,
    };
    
    setTemporaryTask(tempTask);
    setHasDragged(false);
    tempPanRef.setValue({ x: 0, y: 0 });
    setNewTaskHour(hour);
  };

  const handleTempPanStart = () => {
    if (!temporaryTask) return;
    
    console.log('Temporary task pan started');
    setTemporaryTask(prev => prev ? { ...prev, isDragging: true } : null);
    setHasDragged(true);
    
    // Clear any pending timeout since user started dragging
    if (taskCreationTimeoutRef.current) {
      clearTimeout(taskCreationTimeoutRef.current);
      taskCreationTimeoutRef.current = null;
    }
  };

  const startDrag = (task: Task, startY: number) => {
    console.log('Starting drag for existing task:', task.title);
    setDraggedTask({
      ...task,
      isDragging: true,
      startY,
      currentY: startY,
    });
    panRef.setValue({ x: 0, y: 0 });
  };

  const handleTempPanGesture = (event: any) => {
    if (!temporaryTask) return;
    
    const { translationY } = event.nativeEvent;
    setHasDragged(true);
    tempPanRef.setValue({ x: 0, y: translationY });
  };

  const handleTempPanEnd = (event: any) => {
    if (!temporaryTask) return;

    if (taskCreationTimeoutRef.current) {
      clearTimeout(taskCreationTimeoutRef.current);
      taskCreationTimeoutRef.current = null;
    }

    const { translationY } = event.nativeEvent;
    
    if (Math.abs(translationY) < 20 && !hasDragged) {
      setNewTaskHour(temporaryTask.hour);
      setShowTaskModal(true);
      return;
    }
    
    const finalY = temporaryTask.startY + translationY;
    
    // Calculate hour based on the final position
    const hourIndex = Math.floor((finalY + HOUR_HEIGHT / 2) / TOTAL_HOUR_HEIGHT);
    const newHour = Math.max(validStartHour, Math.min(validEndHour, validStartHour + hourIndex));
    const newHourIndex = newHour - validStartHour;
    const snappedY = newHourIndex * TOTAL_HOUR_HEIGHT;
    
    setTemporaryTask(prev => {
      if (!prev) return null;
      return {
        ...prev,
        startY: snappedY,
        currentY: snappedY,
        isDragging: false,
        hour: newHour,
      };
    });
    
    tempPanRef.setValue({ x: 0, y: 0 });
    setNewTaskHour(newHour);
    setShowTaskModal(true);
  };

  const handlePanGesture = (event: any) => {
    if (!draggedTask) return;
    
    const { translationY } = event.nativeEvent;
    const newY = draggedTask.startY + translationY;
    
    setDraggedTask(prev => prev ? { ...prev, currentY: newY } : null);
    panRef.setValue({ x: 0, y: translationY });
  };

  const handlePanEnd = async (event: any) => {
    if (!draggedTask) return;

    const { translationY } = event.nativeEvent;
    const finalY = draggedTask.startY + translationY;
    
    // Calculate which hour slot this corresponds to
    const hourIndex = Math.round(finalY / TOTAL_HOUR_HEIGHT);
    const newHour = Math.max(validStartHour, Math.min(validEndHour, validStartHour + hourIndex));
    
    try {
      const taskDate = new Date(draggedTask.due_date);
      taskDate.setHours(newHour, 0, 0, 0);
      
      await updateTask(draggedTask.id, {
        ...draggedTask,
        due_date: taskDate.toISOString(),
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to update task time');
    }

    // Reset drag state
    setDraggedTask(null);
    panRef.setValue({ x: 0, y: 0 });
  };

  const getCurrentTimeIndicator = () => {
    const now = currentTime;
    const currentHour = now.getHours();
    const currentMinutes = now.getMinutes();
    
    if (currentHour >= validStartHour && currentHour <= validEndHour) {
      const currentSeconds = now.getSeconds();
      const totalMinutesInHour = currentMinutes + (currentSeconds / 60);
      const minuteProgress = totalMinutesInHour / 60;
      
      const hourSlotIndex = currentHour - validStartHour;
      const basePosition = hourSlotIndex * TOTAL_HOUR_HEIGHT;
      const minutePosition = minuteProgress * HOUR_HEIGHT;
      const topPosition = basePosition + minutePosition - (TIME_INDICATOR_HEIGHT / 2);
      
      const timeString = now.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
      
      return (
        <View style={[styles.currentTimeIndicator, { top: topPosition }]}>
          <View style={[styles.currentTimeContainer, { backgroundColor: currentTheme.colors.background }]}>
            <Text style={[styles.currentTimeText, { color: currentTheme.colors.primary }]}>
              {timeString}
            </Text>
          </View>
          <View style={[styles.currentTimeDot, { backgroundColor: currentTheme.colors.primary }]} />
          <View style={[styles.currentTimeLine, { backgroundColor: currentTheme.colors.primary }]} />
        </View>
      );
    }
    return null;
  };

  const renderDraggedTask = () => {
    if (!draggedTask) return null;

    return (
      <Animated.View
        style={[
          styles.draggedTaskBlock,
          {
            backgroundColor: getSubjectColor(draggedTask.subject),
            transform: panRef.getTranslateTransform(),
            top: draggedTask.startY,
            left: 72,
            right: 8,
            height: HOUR_HEIGHT,
            position: 'absolute',
            zIndex: 1000,
          }
        ]}
      >
        <Text style={styles.taskTitle} numberOfLines={1}>
          {draggedTask.title}
        </Text>
        <Text style={styles.taskSubject} numberOfLines={1}>
          {draggedTask.subject}
        </Text>
        {draggedTask.estimated_minutes && (
          <Text style={styles.taskDuration}>
            {draggedTask.estimated_minutes}min
          </Text>
        )}
      </Animated.View>
    );
  };

  const renderDropZone = () => {
    return (
      <>
        {studyHours.map((hour) => {
          const tasks = getTasksForHour(hour);
          return (
            <View key={hour} style={styles.hourRow}>
              <View style={styles.hourLabelContainer}>
                <Text style={[styles.hourLabel, { color: currentTheme.colors.textSecondary }]}>
                  {formatHour(hour)}
                </Text>
              </View>
              <View style={[styles.dropZone, { backgroundColor: currentTheme.colors.surface }]}>
                {tasks.map((task) => (
                  <TouchableOpacity
                    key={task.id}
                    style={[
                      styles.taskBlock,
                      { backgroundColor: getSubjectColor(task.subject) }
                    ]}
                    onPress={() => handleTaskPress(task)}
                    onLongPress={() => {
                      const hourIndex = hour - validStartHour;
                      const startY = hourIndex * TOTAL_HOUR_HEIGHT;
                      setDraggedTask({
                        ...task,
                        startY,
                        currentY: startY,
                        isDragging: true,
                      });
                    }}
                  >
                    <Text style={styles.taskTitle} numberOfLines={1}>
                      {task.title}
                    </Text>
                    <Text style={styles.taskSubject} numberOfLines={1}>
                      {task.subject}
                    </Text>
                    {task.estimated_minutes && (
                      <Text style={styles.taskDuration}>
                        {task.estimated_minutes}min
                      </Text>
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          );
        })}
      </>
    );
  };

  const handleScheduleLongPress = (event: any) => {
    if (isScrolling) {
      console.log('Ignoring long press during scroll');
      return;
    }

    const { y } = event;
    const hour = getHourFromPosition(y);
    
    if (hour < validStartHour || hour > validEndHour) {
      console.log('Long press outside valid hours');
      return;
    }

    const hourIndex = hour - validStartHour;
    const startY = hourIndex * TOTAL_HOUR_HEIGHT;
    
    const tempTask = {
      id: 'temp-' + Date.now(),
      startY,
      currentY: startY,
      isDragging: false,
      hour,
    };
    
    console.log('Creating temporary task:', { hour, startY });
    
    setTemporaryTask(tempTask);
    setHasDragged(false);
    tempPanRef.setValue({ x: 0, y: 0 });
    setNewTaskHour(hour);
  };

  const renderTemporaryTask = () => {
    if (!temporaryTask) return null;

    const translateY = tempPanRef.y;
    
    return (
      <PanGestureHandler
        onGestureEvent={handleTempPanGesture}
        onHandlerStateChange={handleTempPanEnd}
        id={`temp-task-pan-${temporaryTask.id}`}
      >
        <Animated.View
          style={[
            styles.temporaryTaskBlock,
            {
              transform: [
                { translateY: translateY }
              ],
              top: temporaryTask.startY,
              zIndex: 1000,
            },
          ]}
        >
          <View style={styles.temporaryTaskContent}>
            <Text style={[styles.temporaryTaskText, { color: currentTheme.colors.primary }]}>
              New Task
            </Text>
            <Text style={[styles.temporaryTaskTime, { color: currentTheme.colors.primary }]}>
              {formatHour(temporaryTask.hour)}
            </Text>
          </View>
        </Animated.View>
      </PanGestureHandler>
    );
  };

  const handleTaskPress = (task: Task) => {
    setSelectedTask(task);
    setShowDetailsModal(true);
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setShowTaskModal(true);
  };

  const handleCloseTaskModal = () => {
    // Only clear states if we're actually closing the modal
    if (showTaskModal) {
      setShowTaskModal(false);
      setEditingTask(null);
      // Clear temporary task when modal is closed without creating
      setTemporaryTask(null);
      setNewTaskHour(0);
      setHasDragged(false);
    }
  };

  const handleTaskCreated = async () => {
    try {
      // Clear states in a specific order
      setShowTaskModal(false);
      setEditingTask(null);
      setTemporaryTask(null);
      setNewTaskHour(0);
      setHasDragged(false);
      
      // Refresh tasks after a short delay to ensure state updates are complete
      await new Promise(resolve => setTimeout(resolve, 100));
      await refreshTasks();
    } catch (error) {
      console.error('Error handling task creation:', error);
    }
  };

  const handleDetailsModalClose = () => {
    setShowDetailsModal(false);
    setSelectedTask(null);
  };

  // Add effect to handle long press completion without dragging
  useEffect(() => {
    if (temporaryTask && !temporaryTask.isDragging && !hasDragged) {
      // If we have a temporary task that isn't being dragged, create task after delay
      const timeout = setTimeout(() => {
        if (temporaryTask && !temporaryTask.isDragging && !hasDragged) {
          console.log('Long press completed without dragging, creating task');
          setNewTaskHour(temporaryTask.hour);
          setShowTaskModal(true);
        }
      }, 1500); // Much longer delay to allow plenty of time for dragging to start
      
      return () => clearTimeout(timeout);
    }
  }, [temporaryTask, hasDragged]);

  useEffect(() => {
    return () => {
      // Cleanup effect to clear the timeout when the component unmounts
      if (taskCreationTimeoutRef.current) {
        clearTimeout(taskCreationTimeoutRef.current);
        taskCreationTimeoutRef.current = null;
      }
    };
  }, []);

  // Add useEffect for updating current time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <GestureHandlerRootView style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        onScrollBeginDrag={() => setIsScrolling(true)}
        onScrollEndDrag={() => {
          setTimeout(() => setIsScrolling(false), 200);
        }}
        scrollEventThrottle={16}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshTasks}
            tintColor="#FFFFFF"
            colors={["#FFFFFF"]}
            progressBackgroundColor="transparent"
          />
        }
      >
        <LongPressGestureHandler
          onHandlerStateChange={({ nativeEvent }) => {
            if (nativeEvent.state === State.ACTIVE) {
              handleScheduleLongPress(nativeEvent);
            }
          }}
          minDurationMs={500}
          maxDist={20}
          id={`schedule-long-press-${instanceId}`}
        >
          <View 
            ref={scheduleRef}
            style={styles.scheduleContainer}
          >
            {renderDropZone()}
            {getCurrentTimeIndicator()}
            {temporaryTask && renderTemporaryTask()}
          </View>
        </LongPressGestureHandler>
      </ScrollView>

      {draggedTask && (
        <PanGestureHandler
          onGestureEvent={handlePanGesture}
          onHandlerStateChange={handlePanEnd}
          id={`task-pan-${draggedTask.id}-${instanceId}`}
        >
          {renderDraggedTask()}
        </PanGestureHandler>
      )}

      <TaskCreateModal 
        visible={showTaskModal} 
        onClose={handleCloseTaskModal}
        editingTask={editingTask}
        initialDate={date}
        initialTime={(() => {
          const time = new Date();
          time.setHours(newTaskHour, 0, 0, 0);
          return time;
        })()}
        onTaskCreated={handleTaskCreated}
      />

      <TaskDetailsModal
        visible={showDetailsModal}
        onClose={handleDetailsModalClose}
        task={selectedTask}
        onEdit={handleEditTask}
      />
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scheduleContainer: {
    flex: 1,
    position: 'relative',
    paddingBottom: 20,
  },
  hourRow: {
    flexDirection: 'row',
    height: TOTAL_HOUR_HEIGHT,
    borderBottomWidth: HOUR_BORDER_HEIGHT,
    borderBottomColor: 'rgba(0, 0, 0, 0.1)',
  },
  hourLabelContainer: {
    width: 60,
    alignItems: 'flex-end',
    paddingRight: 12,
    justifyContent: 'center',
  },
  hourLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  dropZone: {
    flex: 1,
    marginLeft: 8,
    marginRight: 8,
    borderRadius: 8,
  },
  taskBlock: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: HOUR_HEIGHT,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    justifyContent: 'center',
  },
  taskTitle: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 2,
  },
  taskSubject: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 2,
  },
  taskDuration: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
  },
  draggedTaskBlock: {
    position: 'absolute',
    borderRadius: 8,
    padding: 8,
    height: HOUR_HEIGHT,
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    opacity: 0.9,
  },
  currentTimeIndicator: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: TIME_INDICATOR_HEIGHT,
    justifyContent: 'center',
    zIndex: 100,
    pointerEvents: 'none',
  },
  currentTimeContainer: {
    position: 'absolute',
    left: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  currentTimeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  currentTimeDot: {
    position: 'absolute',
    left: 72,
    width: 6,
    height: 6,
    borderRadius: 3,
    top: TIME_INDICATOR_HEIGHT / 2 - 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1,
    elevation: 2,
  },
  currentTimeLine: {
    position: 'absolute',
    left: 78,
    right: 8,
    height: 1,
    top: TIME_INDICATOR_HEIGHT / 2,
    opacity: 0.8,
  },
  temporaryTaskBlock: {
    position: 'absolute',
    left: 72,
    right: 8,
    height: HOUR_HEIGHT,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  temporaryTaskContent: {
    alignItems: 'center',
    width: '100%',
    height: '100%',
    justifyContent: 'center',
  },
  temporaryTaskText: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
    textAlign: 'center',
  },
  temporaryTaskTime: {
    fontSize: 12,
    opacity: 0.8,
    textAlign: 'center',
  },
  hourClickableArea: {
    height: TOTAL_HOUR_HEIGHT,
    width: '100%',
    position: 'relative',
  },
  taskWrapper: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 8,
    height: HOUR_HEIGHT,
  },
}); 