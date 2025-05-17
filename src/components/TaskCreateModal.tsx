import React, { useState } from 'react';
import { Modal, View, Text, TextInput, TouchableOpacity, StyleSheet, Platform, KeyboardAvoidingView, ScrollView, ViewStyle, TextStyle } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

const SUBJECT_OPTIONS = ['Assignment', 'Exam', 'Meeting', 'Other'];

const ROWS = [
  ['Assignment', 'Exam'],
  ['Meeting', 'Other']
];

// Define task type (matching the new schema)
interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string;
  subject: string;
  due_date: string;
  estimated_minutes?: number;
  status: 'pending' | 'in_progress' | 'completed';
  priority?: 'low' | 'medium' | 'high';
  created_at: string;
}

// Type for the task data when creating (without id, user_id, created_at)
type CreateTaskData = Omit<Task, 'id' | 'user_id' | 'created_at'>;

interface TaskCreateModalProps {
  visible: boolean;
  onClose: () => void;
  onCreate: (task: CreateTaskData) => void;
  darkMode: boolean;
}

// Define the style types with proper React Native style types
interface TaskCreateModalStyles {
  overlay: ViewStyle;
  modal: ViewStyle;
  darkModal: ViewStyle;
  lightModal: ViewStyle;
  modalWithSpacing: ViewStyle;
  title: TextStyle;
  darkText: TextStyle;
  lightText: TextStyle;
  input: TextStyle;
  darkInput: TextStyle;
  lightInput: TextStyle;
  dropdownContainer: ViewStyle;
  dropdownRow: ViewStyle;
  dropdownOption: ViewStyle;
  darkSelected: ViewStyle;
  lightSelected: ViewStyle;
  error: TextStyle;
  buttonRow: ViewStyle;
  button: ViewStyle;
  cancelButton: ViewStyle;
  createButton: ViewStyle;
  buttonText: TextStyle;
  dropdownText: TextStyle;
  selectedText: TextStyle;
  darkUnselectedText: TextStyle;
  lightUnselectedText: TextStyle;
  textArea: TextStyle;
  label: TextStyle;
  keyboardAvoidingView: ViewStyle;
  scrollView: ViewStyle;
  scrollViewContent: ViewStyle;
}

export const TaskCreateModal = ({ visible, onClose, onCreate, darkMode }: TaskCreateModalProps) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState(SUBJECT_OPTIONS[0]);
  const [dueDate, setDueDate] = useState(new Date());
  const [estimatedMinutes, setEstimatedMinutes] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [status, setStatus] = useState<'pending' | 'in_progress' | 'completed'>('pending');
  const [error, setError] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);

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
    setSubject(SUBJECT_OPTIONS[0]);
    setDueDate(new Date());
    setEstimatedMinutes('');
    setPriority('medium');
    setStatus('pending');
  };

  const handleDateChange = (event: any, selectedDate: any) => {
    setShowDatePicker(false);
    if (selectedDate) setDueDate(selectedDate);
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardAvoidingView}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 40 : 0}
        >
          <ScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollViewContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <View style={[styles.modal, darkMode ? styles.darkModal : styles.lightModal]}>
              <Text style={[styles.title, darkMode ? styles.darkText : styles.lightText]}>Create Task</Text>
              <TextInput
                style={[styles.input, darkMode ? styles.darkInput : styles.lightInput]}
                placeholder="Title"
                placeholderTextColor={darkMode ? '#D1D5DB' : '#6B7280'}
                value={title}
                onChangeText={setTitle}
              />
              <TextInput
                style={[styles.input, darkMode ? styles.darkInput : styles.lightInput, styles.textArea]}
                placeholder="Description"
                placeholderTextColor={darkMode ? '#D1D5DB' : '#6B7280'}
                value={description}
                onChangeText={setDescription}
                multiline
                numberOfLines={3}
              />
              <View style={styles.dropdownContainer}>
                <Text style={[styles.label, darkMode ? styles.darkText : styles.lightText]}>Subject</Text>
                <View style={styles.dropdownRow}>
                  {SUBJECT_OPTIONS.map(opt => {
                    const selected = subject === opt;
                    return (
                      <TouchableOpacity
                        key={opt}
                        style={[
                          styles.dropdownOption,
                          selected && (darkMode ? styles.darkSelected : styles.lightSelected)
                        ]}
                        onPress={() => setSubject(opt)}
                        activeOpacity={0.8}
                      >
                        <Text
                          style={[
                            styles.dropdownText,
                            selected
                              ? styles.selectedText
                              : darkMode ? styles.darkUnselectedText : styles.lightUnselectedText
                          ]}
                        >
                          {opt.charAt(0).toUpperCase() + opt.slice(1)}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
              <TouchableOpacity onPress={() => setShowDatePicker(true)}>
                <Text style={[styles.input, darkMode ? styles.darkInput : styles.lightInput]}>Due: {dueDate.toLocaleString()}</Text>
              </TouchableOpacity>
              {showDatePicker && (
                <DateTimePicker
                  value={dueDate}
                  mode="datetime"
                  display={Platform.OS === 'ios' ? 'inline' : 'default'}
                  onChange={handleDateChange}
                />
              )}
              <TextInput
                style={[styles.input, darkMode ? styles.darkInput : styles.lightInput]}
                placeholder="Estimated Minutes"
                placeholderTextColor={darkMode ? '#D1D5DB' : '#6B7280'}
                value={estimatedMinutes}
                onChangeText={setEstimatedMinutes}
                keyboardType="numeric"
              />
              <View style={styles.dropdownContainer}>
                <Text style={[styles.label, darkMode ? styles.darkText : styles.lightText]}>Priority</Text>
                <View style={styles.dropdownRow}>
                  {(['low', 'medium', 'high'] as const).map(opt => {
                    const selected = priority === opt;
                    return (
                      <TouchableOpacity
                        key={opt}
                        style={[
                          styles.dropdownOption,
                          selected && (darkMode ? styles.darkSelected : styles.lightSelected)
                        ]}
                        onPress={() => setPriority(opt)}
                        activeOpacity={0.8}
                      >
                        <Text
                          style={[
                            styles.dropdownText,
                            selected
                              ? styles.selectedText
                              : darkMode ? styles.darkUnselectedText : styles.lightUnselectedText
                          ]}
                        >
                          {opt.charAt(0).toUpperCase() + opt.slice(1)}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
              <View style={styles.dropdownContainer}>
                <Text style={[styles.label, darkMode ? styles.darkText : styles.lightText]}>Status</Text>
                <View style={styles.dropdownRow}>
                  {(['pending', 'in_progress', 'completed'] as const).map(opt => {
                    const selected = status === opt;
                    return (
                      <TouchableOpacity
                        key={opt}
                        style={[
                          styles.dropdownOption,
                          selected && (darkMode ? styles.darkSelected : styles.lightSelected)
                        ]}
                        onPress={() => setStatus(opt)}
                        activeOpacity={0.8}
                      >
                        <Text
                          style={[
                            styles.dropdownText,
                            selected
                              ? styles.selectedText
                              : darkMode ? styles.darkUnselectedText : styles.lightUnselectedText
                          ]}
                        >
                          {opt.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <View style={styles.buttonRow}>
                <TouchableOpacity style={[styles.button, styles.cancelButton]} onPress={onClose}>
                  <Text style={styles.buttonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.button, styles.createButton]} onPress={handleCreate}>
                  <Text style={styles.buttonText}>Create</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create<TaskCreateModalStyles>({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  keyboardAvoidingView: {
    width: '100%',
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    width: '100%',
    maxHeight: '80%',
  },
  scrollViewContent: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
  },
  modal: {
    width: '90%',
    borderRadius: 16,
    padding: 20,
    maxWidth: 500,
  },
  darkModal: {
    backgroundColor: '#1F2937',
  },
  lightModal: {
    backgroundColor: '#FFFFFF',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    fontSize: 16,
  },
  darkInput: {
    borderColor: '#374151',
    color: '#FFFFFF',
    backgroundColor: '#111827',
  },
  lightInput: {
    borderColor: '#E5E7EB',
    color: '#0D1B2A',
    backgroundColor: '#F9FAFB',
  },
  dropdownContainer: {
    marginBottom: 16,
    gap: 8,
  },
  dropdownRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
    gap: 8,
  },
  dropdownOption: {
    flex: 1,
    padding: 8,
    marginHorizontal: 2,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
  },
  darkSelected: {
    backgroundColor: '#00AEEF',
    borderColor: '#00AEEF',
  },
  lightSelected: {
    backgroundColor: '#00AEEF',
    borderColor: '#00AEEF',
  },
  darkText: {
    color: '#FFFFFF',
  },
  lightText: {
    color: '#0D1B2A',
  },
  error: {
    color: '#EF4444',
    marginBottom: 8,
    textAlign: 'center',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  cancelButton: {
    backgroundColor: '#6B7280',
  },
  createButton: {
    backgroundColor: '#00AEEF',
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 16,
  },
  dropdownText: {
    fontSize: 16,
  },
  selectedText: {
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  darkUnselectedText: {
    fontWeight: 'normal',
    color: '#D1D5DB',
  },
  lightUnselectedText: {
    fontWeight: 'normal',
    color: '#0D1B2A',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  label: {
    fontSize: 14,
    marginBottom: 4,
  },
}); 