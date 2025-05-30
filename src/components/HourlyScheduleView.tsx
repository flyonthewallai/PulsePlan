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
import { colors } from '../constants/theme';
import { Task, useTasks } from '../contexts/TaskContext';
import TaskCreateModal from './TaskCreateModal';

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
const { width } = Dimensions.get('window');

export default function HourlyScheduleView({ 
  tasks, 
  studyStartHour, 
  studyEndHour, 
  date 
}: HourlyScheduleViewProps) {
  const { updateTask, refreshTasks, loading } = useTasks();
  const [draggedTask, setDraggedTask] = useState<DraggedTask | null>(null);
  const [temporaryTask, setTemporaryTask] = useState<TemporaryTask | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [newTaskHour, setNewTaskHour] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const [hasDragged, setHasDragged] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const panRef = useRef(new Animated.ValueXY()).current;
  const tempPanRef = useRef(new Animated.ValueXY()).current;
  const taskCreationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Ensure we have valid study hours with fallbacks
  const validStartHour = studyStartHour || 9;
  const validEndHour = studyEndHour || 17;
  
  console.log('HourlyScheduleView props:', { studyStartHour, studyEndHour, validStartHour, validEndHour });
  
  // Create array of hours between study start and end
  const studyHours = [];
  for (let hour = validStartHour; hour <= validEndHour; hour++) {
    studyHours.push(hour);
  }
  
  console.log('Study hours array:', studyHours);

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
    const hourIndex = Math.floor(y / HOUR_HEIGHT);
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
    // Don't create task if user is scrolling
    if (isScrolling) {
      console.log('Ignoring long press during scroll');
      return;
    }
    
    console.log('Creating task for hour:', hour, 'formatted:', formatHour(hour));
    const hourIndex = hour - validStartHour;
    const startY = hourIndex * (HOUR_HEIGHT + 1) + 5; // Simplified calculation matching current time indicator
    
    // Create temporary task block and immediately set it to dragging state
    setTemporaryTask({
      id: 'temp-' + Date.now(),
      startY,
      currentY: startY,
      isDragging: true, // Set to true immediately so it can be dragged during the same gesture
      hour,
    });
    
    // Reset drag state
    setHasDragged(false);
    tempPanRef.setValue({ x: 0, y: 0 });
    
    // Set a timeout to create the task if no dragging occurs
    taskCreationTimeoutRef.current = setTimeout(() => {
      if (!hasDragged) {
        console.log('No dragging detected, creating task at original position');
        setNewTaskHour(hour);
        setShowTaskModal(true);
      }
    }, 1000); // 1 second timeout
  };

  const startDrag = (task: Task, startY: number) => {
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
    
    // Mark that dragging has occurred and clear timeout
    if (!hasDragged) {
      setHasDragged(true);
      if (taskCreationTimeoutRef.current) {
        clearTimeout(taskCreationTimeoutRef.current);
        taskCreationTimeoutRef.current = null;
      }
    }
    
    const newY = temporaryTask.startY + translationY;
    
    setTemporaryTask(prev => prev ? { ...prev, currentY: newY } : null);
    tempPanRef.setValue({ x: 0, y: translationY });
  };

  const handleTempPanEnd = (event: any) => {
    if (!temporaryTask) return;

    // Clear timeout since we're handling the drag end
    if (taskCreationTimeoutRef.current) {
      clearTimeout(taskCreationTimeoutRef.current);
      taskCreationTimeoutRef.current = null;
    }

    const { translationY } = event.nativeEvent;
    const finalY = temporaryTask.startY + translationY;
    
    // Calculate which hour slot this corresponds to
    const hourIndex = Math.round(finalY / HOUR_HEIGHT);
    const newHour = Math.max(validStartHour, Math.min(validEndHour, validStartHour + hourIndex));
    const newHourIndex = newHour - validStartHour;
    const snappedY = newHourIndex * (HOUR_HEIGHT + 1) + 5; // Simplified calculation matching current time indicator
    
    console.log('Drag ended - finalY:', finalY, 'hourIndex:', hourIndex, 'newHour:', newHour, 'formatted:', formatHour(newHour));
    
    // Update temporary task to snapped position
    setTemporaryTask(prev => prev ? {
      ...prev,
      startY: snappedY,
      currentY: snappedY,
      isDragging: false,
      hour: newHour,
    } : null);
    
    // Reset animation
    tempPanRef.setValue({ x: 0, y: 0 });
    
    // Show creation modal with the final hour
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
    const hourIndex = Math.round(finalY / HOUR_HEIGHT);
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
    
    // Only show indicator if current time is within study hours
    if (currentHour >= validStartHour && currentHour <= validEndHour) {
      // Calculate precise position within the hour
      const currentSeconds = now.getSeconds();
      const totalMinutesInHour = currentMinutes + currentSeconds / 60;
      const minuteProgress = totalMinutesInHour / 60;
      
      // Simplified calculation: each hour slot is HOUR_HEIGHT + 1px margin
      const hourSlotIndex = currentHour - validStartHour;
      const topPosition = hourSlotIndex * (HOUR_HEIGHT + 1) + minuteProgress * HOUR_HEIGHT + 5 - 2; // +5 for scheduleContainer paddingTop, -2 to align with timeText visual position
      
      // Debug logging
      console.log('Current Time Indicator Debug:', {
        currentTime: now.toLocaleTimeString(),
        currentHour,
        currentMinutes,
        currentSeconds,
        validStartHour,
        validEndHour,
        hourSlotIndex,
        minuteProgress: (minuteProgress * 100).toFixed(1) + '%',
        topPosition,
        calculation: `${hourSlotIndex} * (${HOUR_HEIGHT} + 1) + ${minuteProgress.toFixed(3)} * ${HOUR_HEIGHT} + 5 = ${topPosition}`,
        previousCalculation: `OLD: ${hourSlotIndex * HOUR_HEIGHT + minuteProgress * HOUR_HEIGHT + hourSlotIndex * 1 + 5}`
      });
      
      const timeString = now.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
      
      return (
        <View 
          style={[
            styles.currentTimeIndicator, 
            { top: topPosition }
          ]} 
        >
          <View style={styles.currentTimeContainer}>
            <Text style={styles.currentTimeText}>{timeString}</Text>
          </View>
          <View style={styles.currentTimeDot} />
          <View style={styles.currentTimeLine} />
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
            height: HOUR_HEIGHT, // Full hour height to align with hour lines
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
    if (!draggedTask && !temporaryTask?.isDragging) return null;

    let dropHour, dropSlotIndex;
    
    if (draggedTask) {
      const hourIndex = Math.round(draggedTask.currentY / HOUR_HEIGHT);
      dropHour = Math.max(validStartHour, Math.min(validEndHour, validStartHour + hourIndex));
      dropSlotIndex = dropHour - validStartHour;
    } else if (temporaryTask?.isDragging) {
      const hourIndex = Math.round(temporaryTask.currentY / HOUR_HEIGHT);
      dropHour = Math.max(validStartHour, Math.min(validEndHour, validStartHour + hourIndex));
      dropSlotIndex = dropHour - validStartHour;
    }

    // Ensure dropSlotIndex is defined before rendering
    if (dropSlotIndex === undefined) return null;

    return (
      <View
        style={[
          styles.dropZone,
          {
            top: dropSlotIndex * (HOUR_HEIGHT + 1) + 5, // Simplified calculation matching current time indicator
            left: 72,
            right: 8,
            height: HOUR_HEIGHT, // Full hour height to align with hour lines
          }
        ]}
      />
    );
  };

  const renderTemporaryTask = () => {
    if (!temporaryTask) return null;

    return (
      <Animated.View
        style={[
          styles.temporaryTaskBlock,
          {
            backgroundColor: colors.primaryBlue,
            transform: tempPanRef.getTranslateTransform(),
            top: temporaryTask.startY,
            left: 72,
            right: 8,
            height: HOUR_HEIGHT, // Full hour height to align with hour lines
            position: 'absolute',
            zIndex: 1001,
          }
        ]}
      >
        <Text style={styles.temporaryTaskText}>New Task</Text>
        <Text style={styles.temporaryTaskTime}>
          {formatHour(temporaryTask.hour)} - {formatHour(temporaryTask.hour + 1)}
        </Text>
      </Animated.View>
    );
  };

  const handleModalClose = () => {
    setShowTaskModal(false);
    setTemporaryTask(null); // Clean up temporary task when modal closes
    setHasDragged(false); // Reset drag state
    
    // Clear any pending timeout
    if (taskCreationTimeoutRef.current) {
      clearTimeout(taskCreationTimeoutRef.current);
      taskCreationTimeoutRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      // Cleanup effect to clear the timeout when the component unmounts
      if (taskCreationTimeoutRef.current) {
        clearTimeout(taskCreationTimeoutRef.current);
        taskCreationTimeoutRef.current = null;
      }
    };
  }, []);

  // Add useEffect to update current time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <GestureHandlerRootView style={styles.container}>
      <View style={styles.container}>
        <ScrollView 
          showsVerticalScrollIndicator={false}
          style={styles.scrollView}
          scrollEnabled={!draggedTask?.isDragging && !temporaryTask?.isDragging}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={refreshTasks}
              tintColor={colors.primaryBlue}
              colors={[colors.primaryBlue]}
              progressBackgroundColor="transparent"
            />
          }
          onScrollBeginDrag={() => setIsScrolling(true)}
          onScrollEndDrag={() => {
            // Add a small delay to prevent accidental task creation right after scrolling
            setTimeout(() => setIsScrolling(false), 100);
          }}
          onMomentumScrollBegin={() => setIsScrolling(true)}
          onMomentumScrollEnd={() => {
            setTimeout(() => setIsScrolling(false), 100);
          }}
        >
          <View style={styles.scheduleContainer}>
            {studyHours.map((hour, index) => {
              const hourTasks = getTasksForHour(hour);
              
              return (
                <View key={hour} style={styles.hourSlot}>
                  <View style={styles.timeColumn}>
                    <Text style={styles.timeText}>{formatHour(hour)}</Text>
                  </View>
                  
                  <View style={styles.taskColumn}>
                    {/* Hour line at the top of each hour */}
                    <View style={styles.hourLine} />
                    
                    {/* Clickable area for the entire hour slot */}
                    <LongPressGestureHandler
                      onHandlerStateChange={({ nativeEvent }) => {
                        if (nativeEvent.state === State.ACTIVE) {
                          handleLongPress(hour);
                        }
                      }}
                      minDurationMs={800}
                      maxDist={20}
                    >
                      <PanGestureHandler
                        id={`hour-pan-${hour}`}
                        onGestureEvent={({ nativeEvent }) => {
                          if (temporaryTask && temporaryTask.isDragging) {
                            handleTempPanGesture({ nativeEvent });
                          }
                        }}
                        onHandlerStateChange={({ nativeEvent }) => {
                          if (nativeEvent.state === State.END && temporaryTask && temporaryTask.isDragging) {
                            handleTempPanEnd({ nativeEvent });
                          }
                        }}
                      >
                        <Animated.View style={styles.hourClickableArea}>
                          {/* Tasks within this hour */}
                          {hourTasks.length > 0 && (
                            hourTasks.map((task, taskIndex) => (
                              <PanGestureHandler
                                key={task.id}
                                onGestureEvent={handlePanGesture}
                                onHandlerStateChange={({ nativeEvent }) => {
                                  if (nativeEvent.state === State.BEGAN) {
                                    const startY = index * (HOUR_HEIGHT + 1) + 5; // Simplified calculation matching current time indicator
                                    startDrag(task, startY);
                                  } else if (nativeEvent.state === State.END) {
                                    handlePanEnd({ nativeEvent });
                                  }
                                }}
                              >
                                <Animated.View style={styles.taskWrapper}>
                                  <TouchableOpacity
                                    style={[
                                      styles.taskBlock,
                                      { backgroundColor: getSubjectColor(task.subject) }
                                    ]}
                                    activeOpacity={0.8}
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
                                </Animated.View>
                              </PanGestureHandler>
                            ))
                          )}
                        </Animated.View>
                      </PanGestureHandler>
                    </LongPressGestureHandler>
                  </View>
                </View>
              );
            })}
            
            {/* Current time indicator */}
            {getCurrentTimeIndicator()}
            
            {/* Drop zone indicator */}
            {renderDropZone()}
            
            {/* Dragged task */}
            {renderDraggedTask()}
            
            {/* Temporary task */}
            {renderTemporaryTask()}
          </View>
        </ScrollView>
      </View>

      <TaskCreateModal
        visible={showTaskModal}
        onClose={handleModalClose}
        initialDate={date}
        initialTime={(() => {
          const time = new Date();
          time.setHours(newTaskHour, 0, 0, 0);
          return time;
        })()}
        initialTimeEstimate="60"
      />
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
  },
  scrollView: {
    flex: 1,
  },
  scheduleContainer: {
    position: 'relative',
    paddingBottom: 20,
    paddingTop: 5,
  },
  hourSlot: {
    flexDirection: 'row',
    height: HOUR_HEIGHT,
    marginBottom: 1,
  },
  timeColumn: {
    width: 60,
    alignItems: 'flex-end',
    paddingRight: 12,
    justifyContent: 'flex-start',
    position: 'relative',
  },
  timeText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '500',
    position: 'absolute',
    top: -2,
    right: 12,
  },
  taskColumn: {
    flex: 1,
    position: 'relative',
    paddingLeft: 12,
  },
  hourLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  taskBlock: {
    backgroundColor: colors.primaryBlue,
    borderRadius: 8,
    padding: 8,
    height: HOUR_HEIGHT - 10,
    justifyContent: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  draggedTaskBlock: {
    borderRadius: 8,
    padding: 8,
    height: HOUR_HEIGHT, // Full hour height to align with hour lines
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    opacity: 0.9,
  },
  taskTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
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
  currentTimeIndicator: {
    position: 'absolute',
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    zIndex: 10,
  },
  currentTimeContainer: {
    backgroundColor: '#FF3B30',
    borderRadius: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginRight: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  currentTimeText: {
    fontSize: 11,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  currentTimeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF3B30',
    marginRight: 4,
  },
  currentTimeLine: {
    flex: 1,
    height: 2,
    backgroundColor: '#FF3B30',
    borderRadius: 1,
  },
  dropZone: {
    position: 'absolute',
    backgroundColor: 'rgba(79, 140, 255, 0.3)',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: colors.primaryBlue,
    borderStyle: 'dashed',
    zIndex: 999,
  },
  temporaryTaskBlock: {
    borderRadius: 8,
    padding: 8,
    height: HOUR_HEIGHT, // Full hour height to align with hour lines
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    opacity: 0.9,
  },
  temporaryTaskText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 2,
  },
  temporaryTaskTime: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
  hourClickableArea: {
    height: HOUR_HEIGHT,
    width: '100%',
    position: 'relative',
    backgroundColor: 'rgba(255, 255, 255, 0.02)', // Very subtle background for testing
  },
  taskWrapper: {
    position: 'absolute',
    top: 0, // Simplified - no offset
    left: 0,
    right: 8,
    height: HOUR_HEIGHT, // Full hour height to align with hour lines
  },
}); 