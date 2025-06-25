import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Modal, 
  TouchableOpacity,
  TextInput,
  ScrollView,
  Keyboard,
  Alert,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Book, Calendar, Clock, Flag, X, Check } from 'lucide-react-native';

import { useTasks, CreateTaskData, Task } from '../contexts/TaskContext';
import { useTheme } from '../contexts/ThemeContext';

type TaskCreateModalProps = {
  visible: boolean;
  onClose: () => void;
  initialDate?: Date;
  initialTime?: Date;
  initialTimeEstimate?: string;
  editingTask?: Task | null;
  onTaskCreated?: () => void;
};

export default function TaskCreateModal({ visible, onClose, initialDate, initialTime, initialTimeEstimate, editingTask, onTaskCreated }: TaskCreateModalProps) {
  const { createTask, updateTask, loading } = useTasks();
  const { currentTheme } = useTheme();
  const [isCreating, setIsCreating] = useState(false);
  
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('medium');
  const [selectedDate, setSelectedDate] = useState(initialDate || new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedTime, setSelectedTime] = useState(() => {
    if (initialTime) return initialTime;
    const defaultTime = new Date();
    defaultTime.setHours(23, 59, 0, 0); // 11:59 PM
    return defaultTime;
  });
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [timeEstimate, setTimeEstimate] = useState(initialTimeEstimate || '60');
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const [currentFocusedInput, setCurrentFocusedInput] = useState<string | null>(null);
  const [showSubjectPicker, setShowSubjectPicker] = useState(false);
  
  // Local subjects - later we can sync these with Supabase
  const [localSubjects] = useState([
    { id: '1', name: 'Mathematics', color: '#FF6B6B' },
    { id: '2', name: 'Computer Science', color: '#4ECDC4' },
    { id: '3', name: 'Physics', color: '#45B7D1' },
    { id: '4', name: 'Chemistry', color: '#96CEB4' },
    { id: '5', name: 'Biology', color: '#FFEAA7' },
    { id: '6', name: 'History', color: '#DDA0DD' },
    { id: '7', name: 'English', color: '#98D8C8' },
    { id: '8', name: 'Psychology', color: '#F7DC6F' },
  ]);
  
  const scrollViewRef = useRef<ScrollView>(null);
  const titleInputRef = useRef<TextInput>(null);
  const subjectInputRef = useRef<TextInput>(null);
  const dateInputRef = useRef<TextInput>(null);
  const timeEstimateInputRef = useRef<TextInput>(null);
  const modalRef = useRef<View>(null);
  
  useEffect(() => {
    const keyboardWillShow = Keyboard.addListener('keyboardWillShow', (e) => {
      setKeyboardHeight(e.endCoordinates.height);
      // Simple scroll when keyboard appears
      scrollViewRef.current?.scrollTo({
        y: 100,
        animated: true
      });
    });
    
    const keyboardWillHide = Keyboard.addListener('keyboardWillHide', () => {
      setKeyboardHeight(0);
      // Reset scroll position when keyboard hides
      scrollViewRef.current?.scrollTo({
        y: 0,
        animated: true
      });
    });
    
    return () => {
      keyboardWillShow.remove();
      keyboardWillHide.remove();
    };
  }, []);
  
  const handleInputFocus = (inputName: string) => {
    setCurrentFocusedInput(inputName);
  };
  
  const handleDateChange = (event: any, selectedDate?: Date) => {
    if (selectedDate) {
      setSelectedDate(selectedDate);
    }
  };
  
  const handleTimeChange = (event: any, selectedTime?: Date) => {
    if (selectedTime) {
      setSelectedTime(selectedTime);
    }
  };
  
  const showDatePickerModal = () => {
    setShowDatePicker(true);
  };
  
  const showTimePickerModal = () => {
    setShowTimePicker(true);
  };
  
  const hideDatePicker = () => {
    setShowDatePicker(false);
  };
  
  const hideTimePicker = () => {
    setShowTimePicker(false);
  };
  
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };
  
  const formatTime = (time: Date) => {
    return time.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };
  
  const handleSubjectSelect = (subjectName: string) => {
    setSubject(subjectName || '');
    setShowSubjectPicker(false);
  };
  
  const getSelectedSubject = () => {
    return localSubjects.find(s => s.name === subject);
  };
  
  const handleSave = async () => {
    // Validation
    if (!title.trim()) {
      Alert.alert('Error', 'Please enter a task title');
      return;
    }

    setIsCreating(true);
    
    try {
      // Combine date and time into a single due_date
      const dueDateTime = new Date(selectedDate);
      dueDateTime.setHours(selectedTime.getHours());
      dueDateTime.setMinutes(selectedTime.getMinutes());
      
      if (editingTask) {
        // Update existing task
        const updateData = {
          title: title.trim(),
          subject: subject || 'General',
          due_date: dueDateTime.toISOString(),
          estimated_minutes: timeEstimate ? parseInt(timeEstimate) : undefined,
          priority,
        };

        await updateTask(editingTask.id, updateData);
        Alert.alert('Success', 'Task updated successfully!');
      } else {
        // Create new task
        const taskData: CreateTaskData = {
          title: title.trim(),
          description: '', // We can add a description field later
          subject: subject || 'General',
          due_date: dueDateTime.toISOString(),
          estimated_minutes: timeEstimate ? parseInt(timeEstimate) : undefined,
          status: 'pending',
          priority,
        };

        await createTask(taskData);
        Alert.alert('Success', 'Task created successfully!');
      }
      
      // Call onTaskCreated before resetting the form
      onTaskCreated?.();
      
      // Reset form after successful creation
      resetForm();
    } catch (error) {
      console.error('Error saving task:', error);
      Alert.alert('Error', `Failed to ${editingTask ? 'update' : 'create'} task. Please try again.`);
    } finally {
      setIsCreating(false);
    }
  };
  
  const resetForm = () => {
    setTitle('');
    setSubject('General');
    setPriority('medium');
    setSelectedDate(initialDate || new Date());
    const resetTime = initialTime || (() => {
      const defaultTime = new Date();
      defaultTime.setHours(23, 59, 0, 0); // 11:59 PM
      return defaultTime;
    })();
    setSelectedTime(resetTime);
    setTimeEstimate(initialTimeEstimate || '60');
    setCurrentFocusedInput(null);
    onClose();
  };
  
  // Populate form when editing
  useEffect(() => {
    if (editingTask && visible) {
      setTitle(editingTask.title);
      setSubject(editingTask.subject);
      setPriority(editingTask.priority);
      
      const dueDate = new Date(editingTask.due_date);
      setSelectedDate(dueDate);
      setSelectedTime(dueDate);
      
      setTimeEstimate(editingTask.estimated_minutes?.toString() || '60');
    } else if (!editingTask && visible) {
      // Only reset form for new task when modal becomes visible
      setTitle('');
      setSubject('General');
      setPriority('medium');
      setTimeEstimate('60');
    }
  }, [editingTask, visible]);
  
  const getPriorityColor = (value: string) => {
    switch (value) {
      case 'high':
        return currentTheme.colors.error;
      case 'medium':
        return currentTheme.colors.warning;
      case 'low':
        return currentTheme.colors.success;
      default:
        return currentTheme.colors.textSecondary;
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View ref={modalRef} style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
        <View style={[styles.modalHeader, { backgroundColor: currentTheme.colors.background, borderBottomColor: 'rgba(255, 255, 255, 0.1)' }]}>
          <TouchableOpacity onPress={onClose} style={styles.cancelButton}>
            <X color={currentTheme.colors.textPrimary} size={24} />
          </TouchableOpacity>
          <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>
            {editingTask ? 'Edit Task' : 'New Task'}
          </Text>
          <TouchableOpacity onPress={handleSave} disabled={isCreating} style={styles.saveButton}>
            <Text style={[styles.saveButtonText, { color: isCreating ? currentTheme.colors.textSecondary : currentTheme.colors.primary }]}>
              {isCreating ? 'Saving...' : 'Save'}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView 
          ref={scrollViewRef}
          style={styles.modalContent}
          contentContainerStyle={styles.scrollContentContainer}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>TASK TITLE</Text>
            <TextInput
              ref={titleInputRef}
              style={[styles.modalInput, { backgroundColor: currentTheme.colors.surface, color: currentTheme.colors.textPrimary }]}
              placeholder="What do you need to do?"
              placeholderTextColor={currentTheme.colors.textSecondary}
              value={title}
              onChangeText={setTitle}
              onFocus={() => handleInputFocus('title')}
              autoFocus
            />
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>SUBJECT</Text>
            <TouchableOpacity 
              style={[styles.subjectPicker, { backgroundColor: currentTheme.colors.surface }]}
              onPress={() => setShowSubjectPicker(true)}
            >
              <View style={styles.subjectPickerContent}>
                {subject && subject !== 'General' ? (
                  <View style={styles.selectedSubject}>
                    <View 
                      style={[
                        styles.subjectColorDot, 
                        { backgroundColor: getSelectedSubject()?.color || currentTheme.colors.textSecondary }
                      ]} 
                    />
                    <Text style={[styles.selectedSubjectText, { color: currentTheme.colors.textPrimary }]}>{subject}</Text>
                  </View>
                ) : (
                  <Text style={[styles.subjectPlaceholder, { color: currentTheme.colors.textSecondary }]}>Select subject (optional)</Text>
                )}
              </View>
              <Text style={[styles.dropdownArrow, { color: currentTheme.colors.textSecondary }]}>▼</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>PRIORITY</Text>
            <View style={styles.prioritySelector}>
              {(['high', 'medium', 'low'] as const).map((value) => (
                <TouchableOpacity
                  key={value}
                  style={[
                    styles.priorityButton,
                    { backgroundColor: currentTheme.colors.surface },
                    priority === value && { backgroundColor: currentTheme.colors.primary + '20' },
                  ]}
                  onPress={() => setPriority(value)}
                >
                  <View 
                    style={[
                      styles.priorityDot,
                      { backgroundColor: getPriorityColor(value) },
                    ]} 
                  />
                  <Text 
                    style={[
                      styles.priorityText,
                      { color: currentTheme.colors.textSecondary },
                      priority === value && { color: currentTheme.colors.textPrimary },
                    ]}
                  >
                    {value.charAt(0).toUpperCase() + value.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          <View style={styles.inputRow}>
            <View style={[styles.inputGroup, styles.inputHalf]}>
              <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>DUE DATE</Text>
              <TouchableOpacity
                style={[styles.inputWithIcon, { backgroundColor: currentTheme.colors.surface }]}
                onPress={showDatePickerModal}
              >
                <Text style={[styles.selectedDateText, { color: currentTheme.colors.textPrimary }]}>{formatDate(selectedDate)}</Text>
              </TouchableOpacity>
            </View>
            
            <View style={[styles.inputGroup, styles.inputHalf]}>
              <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>DUE TIME</Text>
              <TouchableOpacity
                style={[styles.inputWithIcon, { backgroundColor: currentTheme.colors.surface }]}
                onPress={showTimePickerModal}
              >
                <Text style={[styles.selectedDateText, { color: currentTheme.colors.textPrimary }]}>{formatTime(selectedTime)}</Text>
              </TouchableOpacity>
            </View>
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, { color: currentTheme.colors.textSecondary }]}>TIME ESTIMATE</Text>
            <TextInput
              ref={timeEstimateInputRef}
              style={[styles.modalInput, { backgroundColor: currentTheme.colors.surface, color: currentTheme.colors.textPrimary }]}
              placeholder="How long will it take? (minutes)"
              placeholderTextColor={currentTheme.colors.textSecondary}
              keyboardType="number-pad"
              value={timeEstimate}
              onChangeText={setTimeEstimate}
              onFocus={() => handleInputFocus('timeEstimate')}
            />
          </View>
          
          {/* Add some bottom padding for better UX */}
          <View style={styles.bottomPadding} />
        </ScrollView>
      </View>

      {/* Date Picker */}
      {showDatePicker && (
        <Modal
          visible={showDatePicker}
          animationType="slide"
          transparent={true}
          onRequestClose={hideDatePicker}
        >
          <TouchableOpacity 
            style={styles.datePickerOverlay}
            activeOpacity={1}
            onPress={hideDatePicker}
          >
            <View style={styles.datePickerContainer}>
              <View style={[styles.datePickerModal, { backgroundColor: currentTheme.colors.surface }]}>
                <View style={[styles.datePickerHeader, { borderBottomColor: currentTheme.colors.border }]}>
                  <TouchableOpacity onPress={hideDatePicker}>
                    <Text style={[styles.datePickerCancel, { color: currentTheme.colors.textSecondary }]}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={[styles.datePickerTitle, { color: currentTheme.colors.textPrimary }]}>Select Date</Text>
                  <TouchableOpacity onPress={hideDatePicker}>
                    <Text style={[styles.datePickerDone, { color: currentTheme.colors.primary }]}>Done</Text>
                  </TouchableOpacity>
                </View>
                <View style={[styles.pickerContainer, { backgroundColor: currentTheme.colors.surface }]}>
                  <DateTimePicker
                    value={selectedDate}
                    mode="date"
                    display="spinner"
                    onChange={handleDateChange}
                    minimumDate={new Date()}
                    textColor={currentTheme.colors.textPrimary}
                  />
                </View>
              </View>
            </View>
          </TouchableOpacity>
        </Modal>
      )}

      {/* Time Picker */}
      {showTimePicker && (
        <Modal
          visible={showTimePicker}
          animationType="slide"
          transparent={true}
          onRequestClose={hideTimePicker}
        >
          <TouchableOpacity 
            style={styles.datePickerOverlay}
            activeOpacity={1}
            onPress={hideTimePicker}
          >
            <View style={styles.datePickerContainer}>
              <View style={[styles.datePickerModal, { backgroundColor: currentTheme.colors.surface }]}>
                <View style={[styles.datePickerHeader, { borderBottomColor: currentTheme.colors.border }]}>
                  <TouchableOpacity onPress={hideTimePicker}>
                    <Text style={[styles.datePickerCancel, { color: currentTheme.colors.textSecondary }]}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={[styles.datePickerTitle, { color: currentTheme.colors.textPrimary }]}>Select Time</Text>
                  <TouchableOpacity onPress={hideTimePicker}>
                    <Text style={[styles.datePickerDone, { color: currentTheme.colors.primary }]}>Done</Text>
                  </TouchableOpacity>
                </View>
                <View style={[styles.pickerContainer, { backgroundColor: currentTheme.colors.surface }]}>
                  <DateTimePicker
                    value={selectedTime}
                    mode="time"
                    display="spinner"
                    onChange={handleTimeChange}
                    textColor={currentTheme.colors.textPrimary}
                  />
                </View>
              </View>
            </View>
          </TouchableOpacity>
        </Modal>
      )}

      {/* Subject Picker Modal */}
      <Modal
        visible={showSubjectPicker}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowSubjectPicker(false)}
      >
        <View style={[styles.pickerModalContainer, { backgroundColor: currentTheme.colors.background }]}>
          <View style={[styles.pickerHeader, { borderBottomColor: currentTheme.colors.border }]}>
            <TouchableOpacity onPress={() => setShowSubjectPicker(false)}>
              <Text style={[styles.cancelButton, { color: currentTheme.colors.textSecondary }]}>Cancel</Text>
            </TouchableOpacity>
            <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>Select Subject</Text>
            <View style={styles.placeholder} />
          </View>
          
          <ScrollView style={styles.pickerContent}>
            {/* None option */}
            <TouchableOpacity
              style={[
                styles.subjectCard,
                { backgroundColor: currentTheme.colors.surface },
                (!subject || subject === 'General') && { backgroundColor: currentTheme.colors.primary + '20' }
              ]}
              onPress={() => handleSubjectSelect('General')}
            >
              <View style={styles.subjectRowLeft}>
                <View 
                  style={[styles.subjectColorDot, { backgroundColor: currentTheme.colors.textSecondary }]} 
                />
                <Text style={[styles.subjectRowTitle, { color: currentTheme.colors.textPrimary }]}>
                  None
                </Text>
              </View>
              {(!subject || subject === 'General') && (
                <Text style={[styles.checkmark, { color: currentTheme.colors.primary }]}>✓</Text>
              )}
            </TouchableOpacity>
            
            {localSubjects.map((subjectItem) => (
              <TouchableOpacity
                key={subjectItem.id}
                style={[
                  styles.subjectCard,
                  { backgroundColor: currentTheme.colors.surface },
                  subject === subjectItem.name && { backgroundColor: currentTheme.colors.primary + '20' }
                ]}
                onPress={() => handleSubjectSelect(subjectItem.name)}
              >
                <View style={styles.subjectRowLeft}>
                  <View 
                    style={[styles.subjectColorDot, { backgroundColor: subjectItem.color }]} 
                  />
                  <Text style={[styles.subjectRowTitle, { color: currentTheme.colors.textPrimary }]}>
                    {subjectItem.name}
                  </Text>
                </View>
                {subject === subjectItem.name && (
                  <Text style={[styles.checkmark, { color: currentTheme.colors.primary }]}>✓</Text>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </Modal>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  cancelButton: {
    padding: 4,
  },
  saveButton: {
    padding: 4,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
  },
  scrollContentContainer: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  inputHalf: {
    width: '48%',
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  modalInput: {
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
  },
  inputWithIcon: {
    justifyContent: 'center',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  iconInput: {
    flex: 1,
    paddingVertical: 12,
    paddingLeft: 12,
    fontSize: 16,
    justifyContent: 'center',
  },
  prioritySelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  priorityButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '30%',
    paddingVertical: 12,
    borderRadius: 12,
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  priorityText: {
    fontSize: 14,
  },

  bottomPadding: {
    height: 20,
  },
  subjectPicker: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  subjectPickerContent: {
    flex: 1,
  },
  selectedSubject: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  subjectPlaceholder: {
    fontSize: 16,
  },
  dropdownArrow: {
    fontSize: 12,
    marginLeft: 8,
  },
  selectedSubjectText: {
    fontSize: 16,
  },
  subjectColorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  pickerModalContainer: {
    flex: 1,
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  placeholder: {
    width: 60,
  },
  pickerContent: {
    padding: 20,
  },
  subjectCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  subjectRowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  subjectRowTitle: {
    fontSize: 17,
  },
  checkmark: {
    fontSize: 18,
    fontWeight: '600',
  },
  selectedDateText: {
    fontSize: 16,
  },
  datePickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  datePickerContainer: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  datePickerModal: {
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: 400,
  },
  datePickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
  },
  datePickerCancel: {
    fontSize: 16,
  },
  datePickerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  datePickerDone: {
    fontSize: 16,
    fontWeight: '600',
  },
  pickerContainer: {
    borderRadius: 12,
    overflow: 'hidden',
  },
});