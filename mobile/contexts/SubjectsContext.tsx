import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { subjectsService, Subject } from '../services/subjectsService';
import { useAuth } from './AuthContext';

interface SubjectsContextType {
  subjects: Subject[];
  loading: boolean;
  refreshSubjects: () => Promise<void>;
  getSubjectColor: (subjectName: string) => string;
  updateSubjectColor: (subjectId: string, color: string) => Promise<void>;
}

const SubjectsContext = createContext<SubjectsContextType | undefined>(undefined);

export const useSubjects = (): SubjectsContextType => {
  const context = useContext(SubjectsContext);
  if (!context) {
    throw new Error('useSubjects must be used within a SubjectsProvider');
  }
  return context;
};

interface SubjectsProviderProps {
  children: ReactNode;
}

export const SubjectsProvider: React.FC<SubjectsProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadSubjects();
    }
  }, [user]);

  const loadSubjects = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const userSubjects = await subjectsService.getUserSubjects(user.id);
      
      // If user has no subjects, create default ones
      if (userSubjects.length === 0) {
        const defaultSubjects = await subjectsService.createDefaultSubjects(user.id);
        setSubjects(defaultSubjects);
      } else {
        setSubjects(userSubjects);
      }
    } catch (error) {
      console.error('Error loading subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshSubjects = async () => {
    await loadSubjects();
  };

  const getSubjectColor = (subjectName: string): string => {
    // First try to find exact match
    const exactMatch = subjects.find(subject => 
      subject.name.toLowerCase() === subjectName.toLowerCase()
    );
    
    if (exactMatch) {
      return exactMatch.color;
    }

    // Try partial matches for common variations
    const partialMatch = subjects.find(subject => {
      const subjectLower = subject.name.toLowerCase();
      const searchLower = subjectName.toLowerCase();
      
      // Handle common variations
      return (
        subjectLower.includes(searchLower) ||
        searchLower.includes(subjectLower) ||
        (searchLower === 'math' && subjectLower === 'mathematics') ||
        (searchLower === 'mathematics' && subjectLower === 'math') ||
        (searchLower === 'english' && subjectLower === 'literature') ||
        (searchLower === 'literature' && subjectLower === 'english')
      );
    });

    if (partialMatch) {
      return partialMatch.color;
    }

    // Fallback to default color
    return '#64748B'; // Slate gray
  };

  const updateSubjectColor = async (subjectId: string, color: string) => {
    try {
      const updatedSubject = await subjectsService.updateSubject(subjectId, { color });
      setSubjects(prev => 
        prev.map(subject => 
          subject.id === subjectId ? updatedSubject : subject
        )
      );
    } catch (error) {
      console.error('Error updating subject color:', error);
      throw error;
    }
  };

  const value: SubjectsContextType = {
    subjects,
    loading,
    refreshSubjects,
    getSubjectColor,
    updateSubjectColor,
  };

  return (
    <SubjectsContext.Provider value={value}>
      {children}
    </SubjectsContext.Provider>
  );
}; 