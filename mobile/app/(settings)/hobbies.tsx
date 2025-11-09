import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform, Alert, ScrollView, Modal, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Plus, Clock, Info, Calendar, Music, Palette, Camera, Gamepad2, Book, Target, X, Sun, CloudSun, Sunset, Moon } from 'lucide-react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

import { useTheme } from '@/contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Hobby {
  id: string;
  name: string;
  icon: string;
  preferredTime: string;
  duration: number; // minutes
  info: string;
}

const HOBBY_STORAGE_KEY = '@pulse_hobbies';

const defaultHobbies: Hobby[] = [
  { id: '1', name: 'Music', icon: 'Music', preferredTime: 'evening', duration: 60, info: 'Practice guitar and piano' },
  { id: '2', name: 'Photography', icon: 'Camera', preferredTime: 'afternoon', duration: 90, info: 'Nature and street photography' },
  { id: '3', name: 'Reading', icon: 'Book', preferredTime: 'evening', duration: 45, info: 'Fiction and non-fiction books' },
  { id: '4', name: 'Gaming', icon: 'Gamepad2', preferredTime: 'evening', duration: 120, info: 'Video games and board games' },
  { id: '5', name: 'Drawing', icon: 'Palette', preferredTime: 'morning', duration: 60, info: 'Digital art and sketching' },
];

const getIconComponent = (iconName: string, size: number, color: string) => {
  switch (iconName) {
    case 'Music': return <Music size={size} color={color} />;
    case 'Camera': return <Camera size={size} color={color} />;
    case 'Book': return <Book size={size} color={color} />;
    case 'Gamepad2': return <Gamepad2 size={size} color={color} />;
    case 'Palette': return <Palette size={size} color={color} />;
    default: return <Target size={size} color={color} />;
  }
};

const HobbyCard = ({ 
  hobby, 
  onPress 
}: { 
  hobby: Hobby; 
  onPress: () => void;
}) => {
  const { currentTheme } = useTheme();

  return (
    <TouchableOpacity 
      style={[styles.hobbyCard, { backgroundColor: currentTheme.colors.surface }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.hobbyCardContent}>
        <View style={styles.hobbyIcon}>
          {getIconComponent(hobby.icon, 24, currentTheme.colors.textSecondary)}
        </View>
        <View style={styles.hobbyInfo}>
          <Text style={[styles.hobbyName, { color: currentTheme.colors.textPrimary }]}>{hobby.name}</Text>
        </View>
      </View>
      <ChevronLeft size={20} color={currentTheme.colors.textSecondary} style={{ transform: [{ rotate: '180deg' }] }} />
    </TouchableOpacity>
  );
};

const HobbyEditModal = ({ 
  visible, 
  hobby, 
  onSave, 
  onClose 
}: { 
  visible: boolean; 
  hobby: Hobby | null; 
  onSave: (hobby: Hobby) => void; 
  onClose: () => void;
}) => {
  const { currentTheme } = useTheme();
  const [name, setName] = useState('');
  const [preferredTime, setPreferredTime] = useState('evening');
  const [duration, setDuration] = useState(60);
  const [info, setInfo] = useState('');

  useEffect(() => {
    if (hobby) {
      setName(hobby.name);
      setPreferredTime(hobby.preferredTime);
      setDuration(hobby.duration);
      setInfo(hobby.info);
    } else {
      // Reset form when adding new hobby
      setName('');
      setPreferredTime('evening');
      setDuration(60);
      setInfo('');
    }
  }, [hobby, visible]);

  const handleSave = () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a hobby name');
      return;
    }

    const updatedHobby: Hobby = {
      id: hobby?.id || Date.now().toString(),
      name: name.trim(),
      icon: hobby?.icon || 'Target',
      preferredTime,
      duration,
      info: info.trim(),
    };

    onSave(updatedHobby);
  };

  const timeOptions = [
    { label: 'Morning', value: 'morning', icon: Sun },
    { label: 'Afternoon', value: 'afternoon', icon: CloudSun },
    { label: 'Evening', value: 'evening', icon: Sunset },
    { label: 'Night', value: 'night', icon: Moon },
  ];

  return (
    <Modal 
      visible={visible} 
      animationType="slide" 
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: currentTheme.colors.background }]}>
        {/* Header */}
        <View style={[styles.modalHeader, { backgroundColor: currentTheme.colors.background }]}>
          <TouchableOpacity 
            style={styles.modalCloseButton} 
            onPress={onClose}
          >
            <X color={currentTheme.colors.textPrimary} size={24} />
          </TouchableOpacity>
          
          <Text style={[styles.modalTitle, { color: currentTheme.colors.textPrimary }]}>
            {hobby ? 'Edit Hobby' : 'Add Hobby'}
          </Text>
          
          <TouchableOpacity 
            style={styles.modalSaveButton}
            onPress={handleSave}
          >
            <Text style={[styles.modalSaveText, { color: currentTheme.colors.primary }]}>
              Save
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <View style={styles.modalContent}>
          <View style={styles.formSection}>
            <Text style={[styles.formLabel, { color: currentTheme.colors.textSecondary }]}>NAME</Text>
            <View style={[styles.inputContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <TextInput
                style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
                value={name}
                onChangeText={setName}
                placeholder="Enter hobby name"
                placeholderTextColor={currentTheme.colors.textSecondary}
              />
            </View>
          </View>

          <View style={styles.formSection}>
            <Text style={[styles.formLabel, { color: currentTheme.colors.textSecondary }]}>PREFERRED TIME</Text>
            <View style={styles.timeOptionsContainer}>
              {timeOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <TouchableOpacity
                    key={option.value}
                    style={[
                      styles.timeOption,
                      { 
                        backgroundColor: preferredTime === option.value ? currentTheme.colors.primary : currentTheme.colors.surface,
                        borderColor: preferredTime === option.value ? currentTheme.colors.primary : 'transparent'
                      }
                    ]}
                    onPress={() => setPreferredTime(option.value)}
                  >
                    <IconComponent 
                      size={18} 
                      color={preferredTime === option.value ? '#FFFFFF' : currentTheme.colors.textSecondary} 
                    />
                    <Text style={[
                      styles.timeOptionText,
                      { color: preferredTime === option.value ? '#FFFFFF' : currentTheme.colors.textPrimary }
                    ]}>
                      {option.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          <View style={styles.formSection}>
            <Text style={[styles.formLabel, { color: currentTheme.colors.textSecondary }]}>DURATION (MINUTES)</Text>
            <View style={[styles.inputContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <TextInput
                style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
                value={duration.toString()}
                onChangeText={(text) => {
                  const num = parseInt(text) || 0;
                  setDuration(Math.max(5, Math.min(480, num))); // 5 minutes to 8 hours
                }}
                placeholder="60"
                keyboardType="numeric"
                placeholderTextColor={currentTheme.colors.textSecondary}
              />
            </View>
          </View>

          <View style={styles.formSection}>
            <Text style={[styles.formLabel, { color: currentTheme.colors.textSecondary }]}>NOTES</Text>
            <View style={[styles.inputContainer, styles.textAreaContainer, { backgroundColor: currentTheme.colors.surface }]}>
              <TextInput
                style={[styles.textInput, { color: currentTheme.colors.textPrimary }]}
                value={info}
                onChangeText={setInfo}
                placeholder="Add any notes about this hobby..."
                placeholderTextColor={currentTheme.colors.textSecondary}
                multiline
                textAlignVertical="top"
              />
            </View>
          </View>
        </View>
      </SafeAreaView>
    </Modal>
  );
};

export default function HobbiesScreen() {
  const router = useRouter();
  const { currentTheme } = useTheme();
  const [hobbies, setHobbies] = useState<Hobby[]>([]);
  const [selectedHobby, setSelectedHobby] = useState<Hobby | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    loadHobbies();
  }, []);

  const loadHobbies = async () => {
    try {
      const stored = await AsyncStorage.getItem(HOBBY_STORAGE_KEY);
      if (stored) {
        setHobbies(JSON.parse(stored));
      } else {
        setHobbies(defaultHobbies);
      }
    } catch (error) {
      console.error('Error loading hobbies:', error);
      setHobbies(defaultHobbies);
    }
  };

  const saveHobbies = async (updatedHobbies: Hobby[]) => {
    try {
      await AsyncStorage.setItem(HOBBY_STORAGE_KEY, JSON.stringify(updatedHobbies));
      setHobbies(updatedHobbies);
    } catch (error) {
      console.error('Error saving hobbies:', error);
      Alert.alert('Error', 'Failed to save hobbies');
    }
  };

  const handleHobbyPress = (hobby: Hobby) => {
    setSelectedHobby(hobby);
    setShowEditModal(true);
  };

  const handleAddHobby = () => {
    setSelectedHobby(null);
    setShowEditModal(true);
  };

  const handleSaveHobby = (hobby: Hobby) => {
    const existingIndex = hobbies.findIndex(h => h.id === hobby.id);
    let updatedHobbies;
    
    if (existingIndex >= 0) {
      updatedHobbies = [...hobbies];
      updatedHobbies[existingIndex] = hobby;
    } else {
      updatedHobbies = [...hobbies, hobby];
    }
    
    saveHobbies(updatedHobbies);
    setShowEditModal(false);
    setSelectedHobby(null);
  };

  const handleCloseModal = () => {
    setShowEditModal(false);
    setSelectedHobby(null);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Hobbies</Text>
        <TouchableOpacity onPress={handleAddHobby} style={styles.addButton}>
          <Plus color={currentTheme.colors.primary} size={24} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
          Add your hobbies and interests. PulsePlan will intelligently make time for them in your schedule based on your preferences.
        </Text>

        <View style={styles.hobbiesContainer}>
          {hobbies.map((hobby) => (
            <HobbyCard
              key={hobby.id}
              hobby={hobby}
              onPress={() => handleHobbyPress(hobby)}
            />
          ))}
        </View>
      </ScrollView>

      <HobbyEditModal
        visible={showEditModal}
        hobby={selectedHobby}
        onSave={handleSaveHobby}
        onClose={handleCloseModal}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  addButton: {
    padding: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  description: {
    fontSize: 15,
    lineHeight: 20,
    marginBottom: 24,
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  hobbiesContainer: {
    gap: 12,
  },
  hobbyCard: {
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  hobbyCardContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  hobbyIcon: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  hobbyInfo: {
    flex: 1,
  },
  hobbyName: {
    fontSize: 17,
    fontWeight: '600',
  },
  hobbyMeta: {
    fontSize: 13,
    marginBottom: 4,
  },
  hobbyDescription: {
    fontSize: 13,
    lineHeight: 16,
  },
  
  // Modal Styles
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  modalCloseButton: {
    padding: 8,
    marginLeft: -8,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  modalSaveButton: {
    padding: 8,
    marginRight: -8,
  },
  modalSaveText: {
    fontSize: 17,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 24,
  },
  formSection: {
    marginBottom: 24,
  },
  formLabel: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  inputContainer: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  textInput: {
    fontSize: 16,
    lineHeight: 22,
    minHeight: 24,
  },
  textAreaContainer: {
    minHeight: 120,
  },
  timeOptionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 16,
  },
  timeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '48%',
    paddingHorizontal: 12,
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  timeOptionText: {
    fontSize: 15,
    fontWeight: '500',
  },
}); 