import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
  TextInput,
  Alert,
  Animated,
} from 'react-native';
import { Check, Plus, X, Trash2 } from 'lucide-react-native';
import { GestureHandlerRootView, PanGestureHandler as RNGHPanGestureHandler, State as GestureState } from 'react-native-gesture-handler';
import { useTheme } from '@/contexts/ThemeContext';

interface SimpleTodo {
  id: string;
  text: string;
  completed: boolean;
}

interface SimpleTodosCardProps {
  onPress?: () => void;
}

interface SwipeableRowProps {
  todo: SimpleTodo;
  onToggle: () => void;
  onDelete: () => void;
  children: React.ReactNode;
}

const SwipeableRow: React.FC<SwipeableRowProps> = ({ todo, onToggle, onDelete, children }) => {
  const translateX = React.useRef(new Animated.Value(0)).current;
  const { currentTheme } = useTheme();

  const onGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: translateX } }],
    { useNativeDriver: false }
  );

  const onHandlerStateChange = (event: any) => {
    const { state, translationX: gestureTranslationX, velocityX } = event.nativeEvent;
    
    if (state === GestureState.END) {
      // If swiped left significantly or with high velocity, delete
      if (gestureTranslationX < -80 || velocityX < -300) {
        // Animate to full left and delete
        Animated.timing(translateX, {
          toValue: -400,
          duration: 200,
          useNativeDriver: false,
        }).start(() => {
          onDelete();
        });
      } else {
        // Snap back to original position
        Animated.spring(translateX, {
          toValue: 0,
          tension: 100,
          friction: 8,
          useNativeDriver: false,
        }).start();
      }
    } else if (state === GestureState.CANCELLED || state === GestureState.FAILED) {
      // Reset position if gesture is cancelled
      Animated.spring(translateX, {
        toValue: 0,
        tension: 100,
        friction: 8,
        useNativeDriver: false,
      }).start();
    }
  };

  return (
    <View style={styles.swipeableContainer}>
      {/* Delete background - only show when actually swiping */}
      <Animated.View style={[
        styles.deleteBackground, 
        { 
          backgroundColor: '#FF3B30',
          opacity: translateX.interpolate({
            inputRange: [-80, -20, 0, 400],
            outputRange: [1, 0.2, 0, 0],
            extrapolate: 'clamp',
          }),
        }
      ]}>
        <Animated.View style={[
          styles.deleteIcon,
          {
            opacity: translateX.interpolate({
              inputRange: [-80, -20, 0, 400],
              outputRange: [1, 0.3, 0, 0],
              extrapolate: 'clamp',
            }),
          }
        ]}>
          <Trash2 size={24} color="#FFFFFF" />
        </Animated.View>
      </Animated.View>

      {/* Todo item */}
      <RNGHPanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
        activeOffsetX={[-10, 999999]}
        failOffsetX={[-999999, 1]}
        failOffsetY={[-30, 30]}
        shouldCancelWhenOutside={false}
      >
                    <Animated.View
              style={[
                styles.swipeableContent,
                {
                  transform: [{ 
                    translateX: translateX.interpolate({
                      inputRange: [-400, 0, 400],
                      outputRange: [-400, 0, 0],
                      extrapolate: 'clamp',
                    })
                  }],
                },
              ]}
            >
          {children}
        </Animated.View>
      </RNGHPanGestureHandler>
    </View>
  );
};

const SimpleTodosCard: React.FC<SimpleTodosCardProps> = ({ onPress }) => {
  const { currentTheme } = useTheme();
  const [todos, setTodos] = useState<SimpleTodo[]>([
    { id: '1', text: 'Go to Trader Joe\'s', completed: false },
    { id: '2', text: 'Call dentist', completed: true },
    { id: '3', text: 'Pick up dry cleaning', completed: false },
  ]);
  const [showModal, setShowModal] = useState(false);
  const [newTodoText, setNewTodoText] = useState('');
  const [currentTodoIndex, setCurrentTodoIndex] = useState(0);
  const cardTranslateX = React.useRef(new Animated.Value(0)).current;

  const toggleTodo = (id: string) => {
    const updatedTodos = todos.map(todo => 
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    );
    
    // Sort todos: incomplete first, completed last
    const sortedTodos = [
      ...updatedTodos.filter(todo => !todo.completed),
      ...updatedTodos.filter(todo => todo.completed)
    ];
    
    setTodos(sortedTodos);
  };

  const addTodo = () => {
    if (newTodoText.trim()) {
      const newTodo: SimpleTodo = {
        id: Date.now().toString(),
        text: newTodoText.trim(),
        completed: false,
      };
      // Add new todo at the top of incomplete todos
      const incompleteTodos = todos.filter(todo => !todo.completed);
      const completedTodos = todos.filter(todo => todo.completed);
      setTodos([newTodo, ...incompleteTodos, ...completedTodos]);
      setNewTodoText('');
    }
  };

  const deleteTodo = (id: string) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  const completedCount = todos.filter(todo => todo.completed).length;
  const totalCount = todos.length;

  // Card swipe handlers
  const onCardGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: cardTranslateX } }],
    { useNativeDriver: true }
  );

  const onCardHandlerStateChange = (event: any) => {
    const { state, translationX: gestureTranslationX, velocityX } = event.nativeEvent;
    
    if (state === GestureState.END) {
      // If swiped left significantly or with high velocity, go to next todo
      if ((gestureTranslationX < -40 || velocityX < -200) && todos.length > 1) {
        // Animate slide out to left
        Animated.timing(cardTranslateX, {
          toValue: -400,
          duration: 150,
          useNativeDriver: true,
        }).start(() => {
          // Update to next todo
          setCurrentTodoIndex((prevIndex) => (prevIndex + 1) % todos.length);
          // Reset position and animate in from right
          cardTranslateX.setValue(400);
          Animated.timing(cardTranslateX, {
            toValue: 0,
            duration: 150,
            useNativeDriver: true,
          }).start();
        });
      }
      // If swiped right significantly or with high velocity, go to previous todo
      else if ((gestureTranslationX > 40 || velocityX > 200) && todos.length > 1) {
        // Animate slide out to right
        Animated.timing(cardTranslateX, {
          toValue: 400,
          duration: 150,
          useNativeDriver: true,
        }).start(() => {
          // Update to previous todo
          setCurrentTodoIndex((prevIndex) => (prevIndex - 1 + todos.length) % todos.length);
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

  const currentTodo = todos[currentTodoIndex] || todos[0];

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
              {/* Current todo item */}
              <View style={styles.todoItem}>
                <TouchableOpacity
                  style={[
                    styles.checkbox,
                    currentTodo?.completed && styles.checkboxCompleted
                  ]}
                  onPress={() => currentTodo && toggleTodo(currentTodo.id)}
                >
                  {currentTodo?.completed && (
                    <Check size={12} color="#FFFFFF" strokeWidth={3} />
                  )}
                </TouchableOpacity>
                <Text style={[
                  styles.todoText,
                  { color: currentTheme.colors.textPrimary },
                  currentTodo?.completed && { 
                    textDecorationLine: 'line-through',
                    color: currentTheme.colors.textSecondary 
                  }
                ]}>
                  {currentTodo?.text || 'No todos yet'}
                </Text>
              </View>

              {/* Status indicator */}
              {totalCount > 1 && (
                <Text style={[styles.statusText, { color: currentTheme.colors.textSecondary }]}>
                  {currentTodoIndex + 1} of {totalCount}
                </Text>
              )}

              {/* Progress indicators */}
              <View style={styles.progressContainer}>
                {todos.slice(0, 4).map((todo, index) => (
                  <View
                    key={todo.id}
                    style={[
                      styles.progressDot,
                      todo.completed ? styles.progressDotCompleted : styles.progressDotIncomplete,
                      index === currentTodoIndex && styles.progressDotActive
                    ]}
                  />
                ))}
                {totalCount > 4 && (
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
              Simple To-Dos
            </Text>
            <View style={{ width: 24 }} />
          </View>

          {/* Add new todo */}
          <View style={styles.addTodoContainer}>
            <TextInput
              style={[
                styles.addTodoInput,
                {
                  backgroundColor: currentTheme.colors.background,
                  color: currentTheme.colors.textPrimary
                }
              ]}
              placeholder="Add a new todo..."
              placeholderTextColor={currentTheme.colors.textSecondary}
              value={newTodoText}
              onChangeText={setNewTodoText}
              onSubmitEditing={addTodo}
              returnKeyType="done"
            />
          </View>

          {/* Todos list */}
          <ScrollView style={styles.todosList} showsVerticalScrollIndicator={false}>
            {todos.map((todo) => (
              <SwipeableRow
                key={todo.id}
                todo={todo}
                onToggle={() => toggleTodo(todo.id)}
                onDelete={() => deleteTodo(todo.id)}
              >
                <TouchableOpacity
                  style={[styles.modalTodoItem, { backgroundColor: currentTheme.colors.surface }]}
                  onPress={() => toggleTodo(todo.id)}
                >
                  <TouchableOpacity
                    style={[
                      styles.modalCheckbox,
                      { borderColor: currentTheme.colors.border },
                      todo.completed && { backgroundColor: currentTheme.colors.primary, borderColor: currentTheme.colors.primary }
                    ]}
                    onPress={() => toggleTodo(todo.id)}
                  >
                    {todo.completed && (
                      <Check size={16} color="#FFFFFF" strokeWidth={3} />
                    )}
                  </TouchableOpacity>
                  <Text style={[
                    styles.modalTodoText,
                    { color: currentTheme.colors.textPrimary },
                    todo.completed && { 
                      textDecorationLine: 'line-through',
                      color: currentTheme.colors.textSecondary 
                    }
                  ]}>
                    {todo.text}
                  </Text>
                </TouchableOpacity>
              </SwipeableRow>
            ))}
          </ScrollView>

          {/* Stats */}
          <View style={[styles.statsContainer, { backgroundColor: currentTheme.colors.surface }]}>
            <Text style={[styles.statsText, { color: currentTheme.colors.textSecondary }]}>
              {completedCount} of {totalCount} completed
            </Text>
          </View>
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
  todoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#666666',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxCompleted: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  todoText: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  statusText: {
    fontSize: 14,
    marginLeft: 32,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginLeft: 32,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  progressDotCompleted: {
    backgroundColor: '#34C759',
  },
  progressDotIncomplete: {
    backgroundColor: '#666666',
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
  addTodoContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 16,
  },
  addTodoInput: {
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
    width: '100%',
  },
  todosList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  modalTodoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  modalCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalTodoText: {
    fontSize: 16,
    flex: 1,
  },
  statsContainer: {
    padding: 16,
    margin: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statsText: {
    fontSize: 14,
    fontWeight: '500',
  },
  swipeableContainer: {
    position: 'relative',
    marginBottom: 8,
  },
  deleteBackground: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    right: 0,
    left: 0,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingRight: 20,
  },
  deleteIcon: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  swipeableContent: {
    backgroundColor: 'transparent',
  },
});

export default SimpleTodosCard; 
