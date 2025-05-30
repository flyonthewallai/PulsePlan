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
import { Book, Calendar, Clock, Flag } from 'lucide-react-native';

import { colors } from '../constants/theme';
import { useTasks, CreateTaskData } from '../contexts/TaskContext';

type TaskCreateModalProps = {
  visible: boolean;
  onClose: () => void;
  initialDate?: Date;
  initialTime?: Date;
  initialTimeEstimate?: string;
};

export default function TaskCreateModal({ visible, onClose, initialDate, initialTime, initialTimeEstimate }: TaskCreateModalProps) {
  const { createTask, loading } = useTasks();
  const [isCreating, setIsCreating] = useState(false);
  
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('medium');
  const [selectedDate, setSelectedDate] = useState(initialDate || new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedTime, setSelectedTime] = useState(initialTime || new Date());
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
    setSubject(subjectName);
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
    
    if (!subject) {
      Alert.alert('Error', 'Please select a subject');
      return;
    }

    setIsCreating(true);
    
    try {
      // Combine date and time into a single due_date
      const dueDateTime = new Date(selectedDate);
      dueDateTime.setHours(selectedTime.getHours());
      dueDateTime.setMinutes(selectedTime.getMinutes());
      
      const taskData: CreateTaskData = {
        title: title.trim(),
        description: '', // We can add a description field later
        subject,
        due_date: dueDateTime.toISOString(),
        estimated_minutes: timeEstimate ? parseInt(timeEstimate) : undefined,
        status: 'pending',
        priority,
      };

      await createTask(taskData);
      
      // Reset form and close modal
      resetForm();
      onClose();
      
      Alert.alert('Success', 'Task created successfully!');
    } catch (error) {
      console.error('Error creating task:', error);
      Alert.alert('Error', 'Failed to create task. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };
  
  const resetForm = () => {
    setTitle('');
    setSubject('');
    setPriority('medium');
    setSelectedDate(initialDate || new Date());
    setSelectedTime(initialTime || new Date());
    setTimeEstimate(initialTimeEstimate || '60');
    setCurrentFocusedInput(null);
  };
  
  // Reset form when modal opens or initial values change
  useEffect(() => {
    if (visible) {
      resetForm();
    }
  }, [visible, initialDate, initialTime, initialTimeEstimate]);
  
  const getPriorityColor = (value: string) => {
    switch (value) {
      case 'high':
        return colors.taskColors.high;
      case 'medium':
        return colors.taskColors.medium;
      case 'low':
        return colors.taskColors.low;
      default:
        return colors.taskColors.default;
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View ref={modalRef} style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.cancelButton}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.modalTitle}>New Task</Text>
          <TouchableOpacity onPress={handleSave} disabled={isCreating}>
            <Text style={[
              styles.modalSaveButton,
              isCreating && styles.modalSaveButtonDisabled
            ]}>
              {isCreating ? 'Creating...' : 'Create'}
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
            <Text style={styles.inputLabel}>Task Title</Text>
            <TextInput
              ref={titleInputRef}
              style={styles.modalInput}
              placeholder="What do you need to do?"
              placeholderTextColor={colors.textSecondary}
              value={title}
              onChangeText={setTitle}
              onFocus={() => handleInputFocus('title')}
              autoFocus
            />
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Subject</Text>
            <TouchableOpacity 
              style={styles.subjectPicker}
              onPress={() => setShowSubjectPicker(true)}
            >
              <Book size={20} color={colors.textSecondary} />
              <View style={styles.subjectPickerContent}>
                {subject ? (
                  <View style={styles.selectedSubject}>
                    <View 
                      style={[
                        styles.subjectColorDot, 
                        { backgroundColor: getSelectedSubject()?.color || colors.textSecondary }
                      ]} 
                    />
                    <Text style={styles.selectedSubjectText}>{subject}</Text>
                  </View>
                ) : (
                  <Text style={styles.subjectPlaceholder}>Select subject</Text>
                )}
              </View>
              <Text style={styles.dropdownArrow}>▼</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Priority</Text>
            <View style={styles.prioritySelector}>
              {(['high', 'medium', 'low'] as const).map((value) => (
                <TouchableOpacity
                  key={value}
                  style={[
                    styles.priorityButton,
                    priority === value && styles.selectedPriorityButton,
                    { borderColor: getPriorityColor(value) },
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
                      priority === value && styles.selectedPriorityText,
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
              <Text style={styles.inputLabel}>Due Date</Text>
              <View style={styles.inputWithIcon}>
                <Calendar size={20} color={colors.textSecondary} />
                <TouchableOpacity
                  style={styles.iconInput}
                  onPress={showDatePickerModal}
                >
                  <Text style={styles.selectedDateText}>{formatDate(selectedDate)}</Text>
                </TouchableOpacity>
              </View>
            </View>
            
            <View style={[styles.inputGroup, styles.inputHalf]}>
              <Text style={styles.inputLabel}>Due Time</Text>
              <View style={styles.inputWithIcon}>
                <Clock size={20} color={colors.textSecondary} />
                <TouchableOpacity
                  style={styles.iconInput}
                  onPress={showTimePickerModal}
                >
                  <Text style={styles.selectedDateText}>{formatTime(selectedTime)}</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Time Estimate</Text>
            <View style={styles.inputWithIcon}>
              <Flag size={20} color={colors.textSecondary} />
              <TextInput
                ref={timeEstimateInputRef}
                style={styles.iconInput}
                placeholder="How long will it take? (min)"
                placeholderTextColor={colors.textSecondary}
                keyboardType="number-pad"
                value={timeEstimate}
                onChangeText={setTimeEstimate}
                onFocus={() => handleInputFocus('timeEstimate')}
              />
            </View>
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
              <View style={styles.datePickerModal}>
                <View style={styles.datePickerHeader}>
                  <TouchableOpacity onPress={hideDatePicker}>
                    <Text style={styles.datePickerCancel}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={styles.datePickerTitle}>Select Date</Text>
                  <TouchableOpacity onPress={hideDatePicker}>
                    <Text style={styles.datePickerDone}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={selectedDate}
                  mode="date"
                  display="spinner"
                  onChange={handleDateChange}
                  minimumDate={new Date()}
                  textColor={colors.textPrimary}
                />
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
              <View style={styles.datePickerModal}>
                <View style={styles.datePickerHeader}>
                  <TouchableOpacity onPress={hideTimePicker}>
                    <Text style={styles.datePickerCancel}>Cancel</Text>
                  </TouchableOpacity>
                  <Text style={styles.datePickerTitle}>Select Time</Text>
                  <TouchableOpacity onPress={hideTimePicker}>
                    <Text style={styles.datePickerDone}>Done</Text>
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={selectedTime}
                  mode="time"
                  display="spinner"
                  onChange={handleTimeChange}
                  textColor={colors.textPrimary}
                />
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
        <View style={styles.pickerModalContainer}>
          <View style={styles.pickerHeader}>
            <TouchableOpacity onPress={() => setShowSubjectPicker(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Select Subject</Text>
            <View style={styles.placeholder} />
          </View>
          
          <ScrollView style={styles.pickerContent}>
            {localSubjects.map((subjectItem) => (
              <TouchableOpacity
                key={subjectItem.id}
                style={[
                  styles.subjectOption,
                  subject === subjectItem.name && styles.selectedSubjectOption
                ]}
                onPress={() => handleSubjectSelect(subjectItem.name)}
              >
                <View style={styles.subjectOptionContent}>
                  <View 
                    style={[styles.subjectColorDot, { backgroundColor: subjectItem.color }]} 
                  />
                  <Text style={[
                    styles.subjectOptionText,
                    subject === subjectItem.name && styles.selectedSubjectOptionText
                  ]}>
                    {subjectItem.name}
                  </Text>
                </View>
                {subject === subjectItem.name && (
                  <Text style={styles.checkmark}>✓</Text>
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
    backgroundColor: colors.backgroundDark,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
    backgroundColor: colors.backgroundDark,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  cancelButton: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  modalSaveButton: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primaryBlue,
  },
  modalSaveButtonDisabled: {
    color: colors.textSecondary,
    opacity: 0.5,
  },
  modalContent: {
    flex: 1,
    padding: 20,
    backgroundColor: colors.backgroundDark,
  },
  scrollContentContainer: {
    paddingBottom: 50,
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
    fontSize: 16,
    fontWeight: '500',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.textPrimary,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  inputWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  iconInput: {
    flex: 1,
    paddingVertical: 12,
    paddingLeft: 12,
    color: colors.textPrimary,
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
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  selectedPriorityButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  priorityText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  selectedPriorityText: {
    color: colors.textPrimary,
    fontWeight: '500',
  },
  bottomPadding: {
    height: 20,
  },
  subjectPicker: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  subjectPickerContent: {
    flex: 1,
    marginLeft: 12,
  },
  selectedSubject: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  subjectPlaceholder: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  dropdownArrow: {
    fontSize: 12,
    color: colors.textSecondary,
    marginLeft: 8,
  },
  selectedSubjectText: {
    fontSize: 16,
    color: colors.textPrimary,
  },
  subjectColorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  pickerModalContainer: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  placeholder: {
    width: 60, // Fixed width instead of flex to center the title
  },
  pickerContent: {
    padding: 20,
  },
  subjectOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    marginBottom: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  selectedSubjectOption: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderColor: colors.primaryBlue,
  },
  subjectOptionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  subjectOptionText: {
    fontSize: 16,
    color: colors.textPrimary,
  },
  selectedSubjectOptionText: {
    color: colors.textPrimary,
    fontWeight: '600',
  },
  checkmark: {
    fontSize: 18,
    color: colors.primaryBlue,
    fontWeight: '600',
  },
  selectedDateText: {
    fontSize: 16,
    color: colors.textPrimary,
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
    backgroundColor: colors.backgroundDark,
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
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  datePickerCancel: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  datePickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  datePickerDone: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primaryBlue,
  },
});