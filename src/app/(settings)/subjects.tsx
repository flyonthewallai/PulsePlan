import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ChevronLeft, Plus } from 'lucide-react-native';

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

const SubjectRow = ({ subject }: { subject: Subject }) => {
    const { currentTheme } = useTheme();
    return (
        <TouchableOpacity 
            style={[styles.row, { borderBottomColor: currentTheme.colors.border }]} 
            onPress={() => Alert.alert('Coming Soon', 'Subject color editing will be available soon!')}
        >
            <View style={styles.rowLeft}>
                <View style={[styles.colorDot, { backgroundColor: subject.color }]} />
                <Text style={[styles.rowTitle, { color: currentTheme.colors.textPrimary }]}>{subject.name}</Text>
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

    return (
        <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
            <View style={[styles.header, { borderBottomColor: currentTheme.colors.border }]}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <ChevronLeft color={currentTheme.colors.textPrimary} size={24} />
                </TouchableOpacity>
                <Text style={[styles.headerTitle, { color: currentTheme.colors.textPrimary }]}>Subjects</Text>
                <TouchableOpacity onPress={handleAddSubject} style={styles.addButton}>
                    <Plus color={currentTheme.colors.primary} size={24} />
                </TouchableOpacity>
            </View>
            <ScrollView>
                <View style={[styles.sectionBody, { backgroundColor: currentTheme.colors.surface, borderColor: currentTheme.colors.border }]}>
                    {subjects.map(subject => <SubjectRow key={subject.id} subject={subject} />)}
                </View>
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 12,
        paddingHorizontal: 16,
        borderBottomWidth: 1,
    },
    backButton: { padding: 4 },
    addButton: { padding: 4 },
    headerTitle: { fontSize: 17, fontWeight: '600' },
    sectionBody: {
        borderRadius: 10,
        margin: 20,
        overflow: 'hidden',
        borderWidth: 1,
    },
    row: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 16,
        borderBottomWidth: 1,
    },
    rowLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 16,
    },
    rowTitle: { fontSize: 17 },
    colorDot: {
        width: 24,
        height: 24,
        borderRadius: 12,
    },
}); 
 
 
 