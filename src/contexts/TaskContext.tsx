import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from './AuthContext';
import { API_URL, testConnection } from '../config/api';
import NetInfo from '@react-native-community/netinfo';

// Define task type
export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string;
  subject: string;
  due_date: string;
  estimated_minutes?: number;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  scheduling_rationale?: string;
  created_at: string;
}

// Type for the task data when creating (without id, user_id, created_at)
export type CreateTaskData = Omit<Task, 'id' | 'user_id' | 'created_at'>;

interface TaskContextType {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  refreshTasks: () => Promise<void>;
  createTask: (task: CreateTaskData) => Promise<void>;
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  isOnline: boolean;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

const CACHE_KEY = 'cached_tasks';
const LAST_SYNC_KEY = 'last_sync_timestamp';

export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { session } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [lastSync, setLastSync] = useState<number>(0);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const cacheUpdateTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingCacheUpdate = useRef<Task[] | null>(null);

  // Monitor network status
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOnline(state.isConnected ?? false);
    });
    return () => unsubscribe();
  }, []);

  // Load initial data
  useEffect(() => {
    let mounted = true;

    const loadInitialData = async () => {
      try {
        // Load cached data first
        const cachedData = await AsyncStorage.getItem(CACHE_KEY);
        const lastSyncData = await AsyncStorage.getItem(LAST_SYNC_KEY);
        
        if (mounted && cachedData) {
          setTasks(JSON.parse(cachedData));
        }
        if (mounted && lastSyncData) {
          setLastSync(parseInt(lastSyncData));
        }

        // Then fetch fresh data if online and authenticated
        if (mounted && session?.access_token && isOnline) {
          setLoading(true);
          const res = await fetch(`${API_URL}/tasks`, {
            headers: {
              Authorization: `Bearer ${session.access_token}`,
            },
          });

          if (!res.ok) {
            throw new Error(`Failed to fetch tasks: ${res.status}`);
          }

          const data = await res.json();
          if (mounted) {
            setTasks(data);
            await updateCache(data);
          }
        }
      } catch (err) {
        console.error('Error in initial data load:', err);
        // Don't set error state here as we're using cached data
      } finally {
        if (mounted) {
          setLoading(false);
          setIsInitialLoad(false);
        }
      }
    };

    loadInitialData();

    return () => {
      mounted = false;
    };
  }, [session?.access_token, isOnline]);

  const updateCache = useCallback(async (newTasks: Task[]) => {
    // Debounce cache updates to reduce AsyncStorage operations
    pendingCacheUpdate.current = newTasks;

    if (cacheUpdateTimeoutRef.current) {
      clearTimeout(cacheUpdateTimeoutRef.current);
    }

    cacheUpdateTimeoutRef.current = setTimeout(async () => {
      try {
        const tasksToCache = pendingCacheUpdate.current;
        if (tasksToCache) {
          await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(tasksToCache));
          const timestamp = Date.now();
          await AsyncStorage.setItem(LAST_SYNC_KEY, timestamp.toString());
          setLastSync(timestamp);
        }
      } catch (err) {
        console.error('Error updating task cache:', err);
      }
    }, 300); // Debounce for 300ms
  }, []);

  const refreshTasks = useCallback(async () => {
    if (!session?.access_token) return;

    setLoading(true);
    setError(null);

    try {
      // If offline, show cached data
      if (!isOnline) {
        setError('You are offline. Showing cached tasks.');
        return;
      }

      // Test API connection first
      console.log(`🔍 Testing connection to API: ${API_URL}`);
      const connectionOk = await testConnection();
      if (!connectionOk) {
        throw new Error(`Cannot reach server at ${API_URL}. Please check if the server is running.`);
      }

      console.log(`✅ Connected to API successfully`);
      const res = await fetch(`${API_URL}/tasks`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`Failed to fetch tasks: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();
      console.log(`📋 Fetched ${data.length} tasks from server`);
      setTasks(data);
      await updateCache(data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, isOnline]);

  const createTask = async (taskData: CreateTaskData) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      // Test API connection first
      console.log(`🔍 Testing connection for task creation: ${API_URL}`);
      const connectionOk = await testConnection();
      if (!connectionOk) {
        throw new Error(`Cannot reach server at ${API_URL}. Please check if the server is running.`);
      }

      const res = await fetch(`${API_URL}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(taskData),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to create task: ${res.status} ${res.statusText} - ${errorText}`);
      }

      const newTask = await res.json();
      console.log(`✅ Created task: ${newTask.title}`);
      const updatedTasks = [...tasks, newTask];
      setTasks(updatedTasks);
      await updateCache(updatedTasks);
    } catch (err) {
      console.error('Error creating task:', err);
      throw err;
    }
  };

  const updateTask = useCallback(async (taskId: string, updates: Partial<Task>) => {
    if (!session?.access_token) {
      throw new Error('Not authenticated');
    }

    try {
      setLoading(true);

      // Optimistically update local state first for immediate UI response
      let newTasks: Task[];
      setTasks(prevTasks => {
        newTasks = prevTasks.map(task =>
          task.id === taskId ? { ...task, ...updates } : task
        );
        return newTasks;
      });

      // Make API call in background
      const res = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(updates),
      });

      if (!res.ok) {
        // Revert optimistic update on error
        setTasks(prevTasks => prevTasks.map(task =>
          task.id === taskId ? { ...task, ...Object.keys(updates).reduce((acc, key) => {
            delete acc[key as keyof Task];
            return acc;
          }, { ...task }) } : task
        ));
        throw new Error(`Failed to update task: ${res.status}`);
      }

      const updatedTask = await res.json();

      // Update with server response
      setTasks(prevTasks => {
        const finalTasks = prevTasks.map(task =>
          task.id === taskId ? { ...task, ...updatedTask } : task
        );
        updateCache(finalTasks);
        return finalTasks;
      });


      return updatedTask;
    } catch (err) {
      console.error('Error updating task:', err);
      setError(err instanceof Error ? err.message : 'Failed to update task');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, updateCache]);

  const deleteTask = async (taskId: string) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      const res = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`Failed to delete task: ${res.status}`);
      }

      const updatedTasks = tasks.filter(task => task.id !== taskId);
      setTasks(updatedTasks);
      await updateCache(updatedTasks);
    } catch (err) {
      console.error('Error deleting task:', err);
      throw err;
    }
  };

  return (
    <TaskContext.Provider value={{
      tasks,
      loading: loading && !isInitialLoad, // Only show loading for manual refreshes
      error,
      refreshTasks,
      createTask,
      updateTask,
      deleteTask,
      isOnline,
    }}>
      {children}
    </TaskContext.Provider>
  );
};

export const useTasks = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  return context;
}; 