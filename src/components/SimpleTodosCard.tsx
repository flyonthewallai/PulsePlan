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

  return (
    <>
      <TouchableOpacity
        style={[styles.card]}
        onPress={() => setShowModal(true)}
        activeOpacity={0.8}
      >
        <View style={styles.cardContent}>
          {/* First todo item */}
          <View style={styles.todoItem}>
            <TouchableOpacity
              style={[
                styles.checkbox,
                todos[0]?.completed && styles.checkboxCompleted
              ]}
              onPress={() => todos[0] && toggleTodo(todos[0].id)}
            >
              {todos[0]?.completed && (
                <Check size={12} color="#FFFFFF" strokeWidth={3} />
              )}
            </TouchableOpacity>
            <Text style={[
              styles.todoText,
              todos[0]?.completed && styles.todoTextCompleted
            ]}>
              {todos[0]?.text || 'No todos yet'}
            </Text>
          </View>

          {/* Progress indicators */}
          <View style={styles.progressContainer}>
            {todos.slice(0, 3).map((todo, index) => (
              <View
                key={todo.id}
                style={[
                  styles.progressDot,
                  todo.completed ? styles.progressDotCompleted : styles.progressDotIncomplete
                ]}
              />
            ))}
            {todos.length > 3 && (
              <Text style={styles.moreIndicator}>—</Text>
            )}
          </View>
        </View>
      </TouchableOpacity>

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
              style={[styles.addTodoInput]}
              placeholder="Add a new todo..."
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
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
    </>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#000000',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    padding: 16,
    marginHorizontal: 20,
    marginTop: 8,
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
    color: '#FFFFFF',
    flex: 1,
  },
  todoTextCompleted: {
    textDecorationLine: 'line-through',
    color: '#999999',
  },
  statusText: {
    fontSize: 14,
    color: '#999999',
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
    backgroundColor: '#000000',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
    width: '100%',
    color: '#FFFFFF',
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
