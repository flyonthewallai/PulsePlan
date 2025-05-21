import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { Platform, View } from 'react-native';
import { Dashboard } from '../pages/Dashboard';
import { WeekView } from '../pages/WeekView';
import { Progress } from '../pages/Progress';
import { SettingsScreen } from '../pages/Settings';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const Tab = createBottomTabNavigator();

export const TabNavigator = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <View style={{ flex: 1, paddingTop: insets.top }}>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: theme.colors.cardBackground,
            borderTopColor: theme.colors.border,
            borderTopWidth: 1,
            paddingBottom: Platform.OS === 'ios' ? insets.bottom : 8,
            paddingTop: 8,
            height: Platform.OS === 'ios' ? 84 + insets.bottom : 60,
            elevation: 0,
            shadowOpacity: 0,
          },
          tabBarActiveTintColor: theme.colors.primary,
          tabBarInactiveTintColor: theme.colors.subtext,
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '500',
            marginBottom: Platform.OS === 'ios' ? 0 : 4,
          },
          tabBarItemStyle: {
            paddingVertical: 4,
          },
        }}
      >
        <Tab.Screen
          name="Home"
          component={Dashboard}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="home" size={size} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Week"
          component={WeekView}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="calendar" size={size} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Progress"
          component={Progress}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="stats-chart" size={size} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Settings"
          component={SettingsScreen}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="settings-outline" size={size} color={color} />
            ),
          }}
        />
      </Tab.Navigator>
    </View>
  );
}; 