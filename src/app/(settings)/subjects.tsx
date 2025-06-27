import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Plus, RefreshCw } from 'lucide-react-native';

import { useTheme } from '@/contexts/ThemeContext';

interface Subject {
  id: string;
  name: string;
  color: string;
}

const initialSubjects: Subject[] = [
    { id: '1', name: 'Mathematics', color: '#FF6B6B' },
    { id: '2', name: 'Science', color: '#4ECDC4' },
    { id: '3', name: 'History', color: '#FFD93D' },
    { id: '4', name: 'Literature', color: '#95E1D3' },
];

const SubjectCard = ({ subject }: { subject: Subject }) => {
    const { currentTheme } = useTheme();
    return (
        <TouchableOpacity 
            style={[styles.subjectCard, { backgroundColor: currentTheme.colors.surface }]}
            onPress={() => Alert.alert('Coming Soon', 'Subject color editing will be available soon!')}
            activeOpacity={0.7}
        >
            <View style={styles.subjectCardContent}>
                <View style={styles.subjectIcon}>
                    <View style={[styles.colorDot, { backgroundColor: subject.color }]} />
                </View>
                <View style={styles.subjectInfo}>
                    <Text style={[styles.subjectName, { color: currentTheme.colors.textPrimary }]}>{subject.name}</Text>
                </View>
            </View>
            <ChevronLeft color={currentTheme.colors.textSecondary} size={20} style={{ transform: [{ rotate: '180deg' }] }} />
        </TouchableOpacity>
    );
};

export default function SubjectsScreen() {
    const router = useRouter();
    const { currentTheme } = useTheme();
    const [subjects, setSubjects] = useState(initialSubjects);

    const handleAddSubject = () => {
        Alert.alert('Coming Soon', 'Adding new subjects will be available in a future update!');
    };

    const handleSyncSubjects = () => {
        Alert.alert('Canvas Sync', 'Canvas integration will sync your subjects automatically in a future update!');
    };

    return (
        <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
                </TouchableOpacity>
                <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Subjects</Text>
                <View style={styles.headerButtons}>
                    <TouchableOpacity onPress={handleSyncSubjects} style={styles.syncButton}>
                        <RefreshCw color={currentTheme.colors.textSecondary} size={22} />
                    </TouchableOpacity>
                    <TouchableOpacity onPress={handleAddSubject} style={styles.addButton}>
                        <Plus color={currentTheme.colors.primary} size={24} />
                    </TouchableOpacity>
                </View>
            </View>
            <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
                <Text style={[styles.description, { color: currentTheme.colors.textSecondary }]}>
                    Manage your subjects and customize their colors. These will be used to organize your assignments and schedule.
                </Text>

                <View style={styles.subjectsContainer}>
                    {subjects.map(subject => <SubjectCard key={subject.id} subject={subject} />)}
                </View>
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: { 
        flex: 1 
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 12,
        paddingHorizontal: 16,
        position: 'relative',
    },
    backButton: { 
        padding: 4 
    },
    headerButtons: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    syncButton: {
        padding: 4,
    },
    addButton: { 
        padding: 4 
    },
    headerTitle: { 
        fontSize: 17, 
        fontWeight: '600',
        position: 'absolute',
        left: 0,
        right: 0,
        textAlign: 'center',
        zIndex: 1,
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
    subjectsContainer: {
        gap: 12,
    },
    subjectCard: {
        borderRadius: 12,
        padding: 16,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    subjectCardContent: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
    },
    subjectIcon: {
        width: 24,
        height: 24,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 16,
    },
    subjectInfo: {
        flex: 1,
    },
    subjectName: {
        fontSize: 17,
        fontWeight: '600',
    },
    colorDot: {
        width: 24,
        height: 24,
        borderRadius: 12,
    },
}); 
 
 
 