import React, { useState, useRef, useEffect } from 'react';
import { 
  Modal, 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Platform, 
  KeyboardAvoidingView, 
  ScrollView, 
  ViewStyle, 
  TextStyle,
  Animated,
  Dimensions
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { Task, CreateTaskData } from '../contexts/TaskContext';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');
const MODAL_MAX_HEIGHT = SCREEN_HEIGHT * 0.85; // 85% of screen height

const SUBJECT_OPTIONS = [
  { id: 'Mathematics', icon: 'calculator-outline' },
  { id: 'Physics', icon: 'flash-outline' },
  { id: 'Biology', icon: 'leaf-outline' },
  { id: 'English', icon: 'book-outline' },
  { id: 'History', icon: 'time-outline' },
  { id: 'Computer Science', icon: 'code-outline' },
  { id: 'Chemistry', icon: 'flask-outline' },
  { id: 'Other', icon: 'ellipsis-horizontal-outline' }
];

interface TaskCreateModalProps {
  visible: boolean;
  onClose: () => void;
  onCreate: (task: CreateTaskData) => void;
  theme: any; // Replace with proper theme type
}

// Define the style types with proper React Native style types
interface TaskCreateModalStyles {
  overlay: ViewStyle;
  modalTouchable: ViewStyle;
  modalContainer: ViewStyle;
  handle: ViewStyle;
  keyboardAvoidingView: ViewStyle;
  scrollView: ViewStyle;
  scrollViewContent: ViewStyle;
  modal: ViewStyle;
  header: ViewStyle;
  title: TextStyle;
  closeButton: ViewStyle;
  form: ViewStyle;
  inputContainer: ViewStyle;
  label: TextStyle;
  input: TextStyle;
  textArea: TextStyle;
  subjectsContainer: ViewStyle;
  subjectOption: ViewStyle;
  subjectText: TextStyle;
  dateButton: ViewStyle;
  dateText: TextStyle;
  durationInput: ViewStyle;
  priorityContainer: ViewStyle;
  priorityOption: ViewStyle;
  priorityText: TextStyle;
  statusContainer: ViewStyle;
  statusOption: ViewStyle;
  statusText: TextStyle;
  errorContainer: ViewStyle;
  errorText: TextStyle;
  buttonContainer: ViewStyle;
  button: ViewStyle;
  cancelButton: ViewStyle;
  createButton: ViewStyle;
  buttonText: TextStyle;
  keyboardAvoidingContainer: ViewStyle;
  datePickerContainer: ViewStyle;
  datePicker: ViewStyle;
  datePickerButton: ViewStyle;
  datePickerButtonText: TextStyle;
}

// Temporary inline hook to bypass import issue
const useModalAnimation = ({ isVisible, onClose, modalHeight = Dimensions.get('window').height * 0.8, animationDuration = 300 }: {
  isVisible: boolean;
  onClose?: () => void;
  modalHeight?: number;
  animationDuration?: number;
}) => {
  const translateY = useRef(new Animated.Value(Dimensions.get('window').height)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const overlayOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isVisible) {
      translateY.setValue(Dimensions.get('window').height);
      opacity.setValue(0);
      overlayOpacity.setValue(0);

      Animated.parallel([
        Animated.timing(translateY, { toValue: 0, duration: animationDuration, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 1, duration: animationDuration, useNativeDriver: true }),
        Animated.timing(overlayOpacity, { toValue: 1, duration: animationDuration, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateY, { toValue: Dimensions.get('window').height, duration: animationDuration, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0, duration: animationDuration, useNativeDriver: true }),
        Animated.timing(overlayOpacity, { toValue: 0, duration: animationDuration, useNativeDriver: true }),
      ]).start(() => onClose?.());
    }
  }, [isVisible, animationDuration, onClose]);

  return { translateY, opacity, overlayOpacity, handleClose: () => onClose?.(), modalHeight };
};

export const TaskCreateModal = ({ visible, onClose, onCreate, theme }: TaskCreateModalProps) => {
  const {
    translateY,
    opacity,
    overlayOpacity,
    handleClose,
    modalHeight
  } = useModalAnimation({
    isVisible: visible,
    onClose,
    modalHeight: MODAL_MAX_HEIGHT,
    animationDuration: 300
  });
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState(SUBJECT_OPTIONS[0].id);
  const [dueDate, setDueDate] = useState(new Date());
  const [estimatedMinutes, setEstimatedMinutes] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [status, setStatus] = useState<'pending' | 'in_progress' | 'completed'>('pending');
  const [error, setError] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [tempDueDate, setTempDueDate] = useState<Date | null>(null);

  const handleCreate = () => {
    if (!title.trim() || !subject || !dueDate || !status) {
      setError('Please fill all required fields.');
      return;
    }
    setError('');
    onCreate({
      title: title.trim(),
      description: description.trim(),
      subject,
      due_date: dueDate.toISOString(),
      estimated_minutes: estimatedMinutes ? Number(estimatedMinutes) : undefined,
      status,
      priority,
    });
    // Reset form
    setTitle('');
    setDescription('');
    setSubject(SUBJECT_OPTIONS[0].id);
    setDueDate(new Date());
    setEstimatedMinutes('');
    setPriority('medium');
    setStatus('pending');
  };

  const handleDateChange = (event: any, selectedDate: any) => {
    if (Platform.OS === 'ios') {
      if (selectedDate) setTempDueDate(selectedDate);
    } else {
      setShowDatePicker(false);
      if (selectedDate) setDueDate(selectedDate);
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      'high': '#EF4444',
      'medium': '#F59E0B',
      'low': '#10B981',
      'default': '#6B7280'
    };
    return colors[priority] || colors.default;
  };

  // Create theme-dependent styles
  const themeStyles = React.useMemo(() => ({
    modalContainer: {
      width: '100%',
      borderTopLeftRadius: 28,
      borderTopRightRadius: 28,
      shadowColor: theme.colors.primary,
      shadowOffset: { 
        width: 0, 
        height: 8 
      },
      shadowOpacity: 0.15,
      shadowRadius: 24,
      elevation: 12,
      borderWidth: 1,
      borderColor: theme.colors.border + '20',
      backgroundColor: theme.colors.background + 'F0', // 94% opacity for frosted effect
    }
  }), [theme]);

  const styles = React.useMemo(() => StyleSheet.create({
    keyboardAvoidingContainer: {
      flex: 1,
    },
    overlay: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.35)',
      justifyContent: 'flex-end',
    },
    modalTouchable: {
      width: '100%',
    },
    scrollView: {
      maxHeight: MODAL_MAX_HEIGHT - 40,
    },
    scrollViewContent: {
      flexGrow: 1,
      paddingBottom: Platform.OS === 'ios' ? 40 : 20,
    },
    modal: {
      padding: 20,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 24,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      letterSpacing: 0.3,
    },
    closeButton: {
      width: 40,
      height: 40,
      borderRadius: 20,
      justifyContent: 'center',
      alignItems: 'center',
      shadowOffset: { width: 0, height: 2 },
      shadowRadius: 8,
      elevation: 3,
    },
    form: {
      gap: 20,
    },
    inputContainer: {
      gap: 8,
    },
    label: {
      fontSize: 14,
      fontWeight: '600',
      letterSpacing: 0.2,
    },
    input: {
      borderWidth: 1,
      borderRadius: 12,
      padding: 12,
      fontSize: 16,
      letterSpacing: 0.2,
    },
    textArea: {
      height: 100,
      textAlignVertical: 'top',
    },
    subjectsContainer: {
      flexDirection: 'row',
      gap: 8,
      paddingVertical: 4,
    },
    subjectOption: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 12,
      borderWidth: 1,
      gap: 6,
    },
    subjectText: {
      fontSize: 14,
      fontWeight: '500',
      letterSpacing: 0.2,
    },
    dateButton: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: 12,
      borderWidth: 1,
      gap: 8,
    },
    dateText: {
      fontSize: 16,
      letterSpacing: 0.2,
    },
    durationInput: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 12,
      borderRadius: 12,
      borderWidth: 1,
      gap: 8,
    },
    priorityContainer: {
      flexDirection: 'row',
      gap: 8,
    },
    priorityOption: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 12,
      borderRadius: 12,
      borderWidth: 1,
      gap: 6,
    },
    priorityText: {
      fontSize: 14,
      fontWeight: '500',
      letterSpacing: 0.2,
    },
    statusContainer: {
      flexDirection: 'row',
      gap: 8,
    },
    statusOption: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 12,
      borderRadius: 12,
      borderWidth: 1,
      gap: 6,
    },
    statusText: {
      fontSize: 14,
      fontWeight: '500',
      letterSpacing: 0.2,
    },
    errorContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      padding: 12,
      borderRadius: 12,
      backgroundColor: '#FEE2E2',
    },
    errorText: {
      fontSize: 14,
      fontWeight: '500',
      letterSpacing: 0.2,
    },
    buttonContainer: {
      flexDirection: 'row',
      gap: 12,
      marginTop: 8,
    },
    button: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 16,
      borderRadius: 12,
      gap: 8,
    },
    cancelButton: {
      shadowOffset: { width: 0, height: 2 },
      shadowRadius: 8,
      elevation: 3,
    },
    createButton: {
      shadowOffset: { width: 0, height: 2 },
      shadowRadius: 8,
      elevation: 3,
    },
    buttonText: {
      fontSize: 16,
      fontWeight: '600',
      letterSpacing: 0.2,
    },
    datePickerContainer: {
      marginTop: 8,
      borderRadius: 12,
      borderWidth: 1,
      overflow: 'hidden',
      backgroundColor: theme.colors.cardBackground,
      borderColor: theme.colors.border,
    },
    datePicker: {
      height: 200,
    },
    datePickerButton: {
      paddingVertical: 12,
      paddingHorizontal: 24,
      alignItems: 'center',
      borderWidth: 1.5,
      borderColor: theme.colors.primary,
      borderRadius: 12,
      margin: 16,
      backgroundColor: 'transparent',
    },
    datePickerButtonText: {
      fontSize: 16,
      fontWeight: '600',
      letterSpacing: 0.2,
      color: theme.colors.primary,
    },
  }), [theme]);

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={handleClose}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboardAvoidingContainer}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <Animated.View 
          style={[
            styles.overlay,
            { opacity: overlayOpacity }
          ]}
        >
          <TouchableOpacity 
            style={styles.overlay} 
            activeOpacity={1} 
            onPress={handleClose}
          >
            <TouchableOpacity 
              activeOpacity={1} 
              onPress={(e) => e.stopPropagation()}
              style={styles.modalTouchable}
            >
              <Animated.View 
                style={[
                  themeStyles.modalContainer,
                  { 
                    transform: [{ translateY }],
                    opacity,
                    maxHeight: modalHeight
                  }
                ]}
              >
                <ScrollView 
                  style={styles.scrollView}
                  contentContainerStyle={styles.scrollViewContent}
                  keyboardShouldPersistTaps="handled"
                  showsVerticalScrollIndicator={true}
                  bounces={true}
                >
                  <View style={styles.modal}>
                    <View style={styles.header}>
                      <Text style={[styles.title, { color: theme.colors.text }]}>
                        Create Task
                      </Text>
                      <TouchableOpacity
                        style={[
                          styles.closeButton,
                          { backgroundColor: theme.colors.cardBackground }
                        ]}
                        onPress={handleClose}
                      >
                        <Ionicons name="close" size={24} color={theme.colors.text} />
                      </TouchableOpacity>
                    </View>

                    <View style={styles.form}>
                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Title
                        </Text>
                        <TextInput
                          style={[
                            styles.input,
                            { 
                              backgroundColor: theme.colors.cardBackground,
                              color: theme.colors.text,
                              borderColor: theme.colors.border
                            }
                          ]}
                          placeholder="Enter task title"
                          placeholderTextColor={theme.colors.subtext}
                          value={title}
                          onChangeText={setTitle}
                        />
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Description
                        </Text>
                        <TextInput
                          style={[
                            styles.input,
                            styles.textArea,
                            { 
                              backgroundColor: theme.colors.cardBackground,
                              color: theme.colors.text,
                              borderColor: theme.colors.border
                            }
                          ]}
                          placeholder="Enter task description"
                          placeholderTextColor={theme.colors.subtext}
                          value={description}
                          onChangeText={setDescription}
                          multiline
                          numberOfLines={3}
                        />
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Subject
                        </Text>
                        <ScrollView 
                          horizontal 
                          showsHorizontalScrollIndicator={false}
                          contentContainerStyle={styles.subjectsContainer}
                        >
                          {SUBJECT_OPTIONS.map(option => (
                            <TouchableOpacity
                              key={option.id}
                              style={[
                                styles.subjectOption,
                                subject === option.id && {
                                  backgroundColor: theme.colors.primary + '15',
                                  borderColor: theme.colors.primary
                                }
                              ]}
                              onPress={() => setSubject(option.id)}
                              activeOpacity={0.8}
                            >
                              <Ionicons 
                                name={option.icon} 
                                size={20} 
                                color={subject === option.id ? theme.colors.primary : theme.colors.text} 
                              />
                              <Text style={[
                                styles.subjectText,
                                { 
                                  color: subject === option.id ? theme.colors.primary : theme.colors.text,
                                  opacity: subject === option.id ? 1 : 0.7
                                }
                              ]}>
                                {option.id}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </ScrollView>
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Due Date
                        </Text>
                        <TouchableOpacity 
                          style={[
                            styles.dateButton,
                            { 
                              backgroundColor: theme.colors.cardBackground,
                              borderColor: theme.colors.border
                            }
                          ]}
                          onPress={() => setShowDatePicker(true)}
                        >
                          <Ionicons 
                            name="calendar-outline" 
                            size={20} 
                            color={theme.colors.text} 
                          />
                          <Text style={[styles.dateText, { color: theme.colors.text }]}>
                            {dueDate.toLocaleString()}
                          </Text>
                        </TouchableOpacity>
                        {showDatePicker && (
                          Platform.OS === 'ios' ? (
                            <View style={[
                              styles.datePickerContainer,
                              { 
                                backgroundColor: theme.colors.cardBackground,
                                borderColor: theme.colors.border
                              }
                            ]}>
                              <DateTimePicker
                                value={tempDueDate || dueDate}
                                mode="datetime"
                                display="spinner"
                                onChange={handleDateChange}
                                textColor={theme.colors.text}
                                style={styles.datePicker}
                                themeVariant={theme.dark ? 'dark' : 'light'}
                              />
                              <TouchableOpacity
                                style={[
                                  styles.datePickerButton,
                                  { 
                                    paddingVertical: 12,
                                    paddingHorizontal: 24,
                                    alignItems: 'center',
                                    borderWidth: 1.5,
                                    borderColor: theme.colors.primary,
                                    borderRadius: 12,
                                    margin: 16,
                                    backgroundColor: 'transparent'
                                  }
                                ]}
                                onPress={() => {
                                  setShowDatePicker(false);
                                  if (tempDueDate) setDueDate(tempDueDate);
                                  setTempDueDate(null);
                                }}
                              >
                                <Text style={[styles.datePickerButtonText, { color: theme.colors.primary }]}>
                                  Done
                                </Text>
                              </TouchableOpacity>
                            </View>
                          ) : (
                            <DateTimePicker
                              value={dueDate}
                              mode="datetime"
                              display="default"
                              onChange={handleDateChange}
                              textColor={theme.colors.text}
                              themeVariant={theme.dark ? 'dark' : 'light'}
                            />
                          )
                        )}
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Estimated Duration
                        </Text>
                        <View style={[
                          styles.durationInput,
                          { 
                            backgroundColor: theme.colors.cardBackground,
                            borderColor: theme.colors.border
                          }
                        ]}>
                          <Ionicons 
                            name="time-outline" 
                            size={20} 
                            color={theme.colors.text} 
                          />
                          <TextInput
                            style={[
                              styles.input,
                              { 
                                color: theme.colors.text,
                                borderWidth: 0,
                                backgroundColor: 'transparent'
                              }
                            ]}
                            placeholder="Enter duration in minutes"
                            placeholderTextColor={theme.colors.subtext}
                            value={estimatedMinutes}
                            onChangeText={setEstimatedMinutes}
                            keyboardType="numeric"
                          />
                        </View>
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Priority
                        </Text>
                        <View style={styles.priorityContainer}>
                          {(['low', 'medium', 'high'] as const).map(opt => (
                            <TouchableOpacity
                              key={opt}
                              style={[
                                styles.priorityOption,
                                { 
                                  backgroundColor: priority === opt 
                                    ? getPriorityColor(opt) + '15'
                                    : theme.colors.cardBackground,
                                  borderColor: priority === opt 
                                    ? getPriorityColor(opt)
                                    : theme.colors.border
                                }
                              ]}
                              onPress={() => setPriority(opt)}
                              activeOpacity={0.8}
                            >
                              <Ionicons 
                                name={
                                  opt === 'high' ? 'arrow-up-circle-outline' :
                                  opt === 'medium' ? 'remove-circle-outline' :
                                  'arrow-down-circle-outline'
                                }
                                size={20}
                                color={getPriorityColor(opt)}
                              />
                              <Text style={[
                                styles.priorityText,
                                { color: getPriorityColor(opt) }
                              ]}>
                                {opt.charAt(0).toUpperCase() + opt.slice(1)}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </View>
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={[styles.label, { color: theme.colors.text }]}>
                          Status
                        </Text>
                        <View style={styles.statusContainer}>
                          {(['pending', 'in_progress', 'completed'] as const).map(opt => (
                            <TouchableOpacity
                              key={opt}
                              style={[
                                styles.statusOption,
                                { 
                                  backgroundColor: status === opt 
                                    ? theme.colors.primary + '15'
                                    : theme.colors.cardBackground,
                                  borderColor: status === opt 
                                    ? theme.colors.primary
                                    : theme.colors.border
                                }
                              ]}
                              onPress={() => setStatus(opt)}
                              activeOpacity={0.8}
                            >
                              <Ionicons 
                                name={
                                  opt === 'pending' ? 'time-outline' :
                                  opt === 'in_progress' ? 'sync-outline' :
                                  'checkmark-circle-outline'
                                }
                                size={20}
                                color={status === opt ? theme.colors.primary : theme.colors.text}
                              />
                              <Text style={[
                                styles.statusText,
                                { 
                                  color: status === opt ? theme.colors.primary : theme.colors.text,
                                  opacity: status === opt ? 1 : 0.7
                                }
                              ]}>
                                {opt.split('_').map(word => 
                                  word.charAt(0).toUpperCase() + word.slice(1)
                                ).join(' ')}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </View>
                      </View>

                      {error ? (
                        <View style={styles.errorContainer}>
                          <Ionicons name="alert-circle-outline" size={20} color={theme.colors.error} />
                          <Text style={[styles.errorText, { color: theme.colors.error }]}>
                            {error}
                          </Text>
                        </View>
                      ) : null}

                      <View style={styles.buttonContainer}>
                        <TouchableOpacity 
                          style={[
                            styles.button,
                            styles.cancelButton,
                            { 
                              backgroundColor: 'transparent',
                              borderWidth: 1.5,
                              borderColor: theme.colors.primary
                            }
                          ]} 
                          onPress={handleClose}
                        >
                          <Text style={[styles.buttonText, { color: theme.colors.primary }]}>
                            Cancel
                          </Text>
                        </TouchableOpacity>
                        <TouchableOpacity 
                          style={[
                            styles.button,
                            styles.createButton,
                            { 
                              backgroundColor: theme.colors.primary,
                              borderWidth: 0
                            }
                          ]} 
                          onPress={handleCreate}
                        >
                          <Text style={[styles.buttonText, { color: '#FFFFFF' }]}>
                            Create Task
                          </Text>
                          <Ionicons name="add-circle-outline" size={20} color="#FFFFFF" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  </View>
                </ScrollView>
              </Animated.View>
            </TouchableOpacity>
          </TouchableOpacity>
        </Animated.View>
      </KeyboardAvoidingView>
    </Modal>
  );
}; 