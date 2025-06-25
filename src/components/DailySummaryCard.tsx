import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { BrainCircuit, CheckCircle2, Clock, CheckCheck, Check, BarChart3 } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';
import DailyOverviewModal from './DailyOverviewModal';

export default function DailySummaryCard() {
  const { currentTheme } = useTheme();
  const [showMessage, setShowMessage] = useState(true);
  const [showOverviewModal, setShowOverviewModal] = useState(false);

  if (!showMessage) {
    return (
      <View style={styles.container}>
        {/* Overview Section Header */}
        <TouchableOpacity 
          style={styles.sectionHeader}
          onPress={() => setShowOverviewModal(true)}
          activeOpacity={0.7}
        >
          <Text style={[styles.sectionLabel, { color: currentTheme.colors.textSecondary }]}>
            OVERVIEW
          </Text>
          <BarChart3 size={16} color={currentTheme.colors.textSecondary} />
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.metricsCard}
          onPress={() => setShowOverviewModal(true)}
          activeOpacity={0.8}
        >
          <View style={styles.metricItem}>
            <View style={styles.metricLeft}>
              <CheckCircle2 color="#FFFFFF" size={20} style={styles.metricIcon} />
              <Text style={styles.metricText}>5 Tasks Today</Text>
            </View>
          </View>
          <View style={[styles.metricItem, styles.metricSpacing]}>
            <View style={styles.metricLeft}>
              <Clock color="#FFFFFF" size={20} style={styles.metricIcon} />
              <Text style={styles.metricText}>3.5h Est. Time</Text>
            </View>
          </View>
          <View style={[styles.metricItem, styles.metricSpacing]}>
            <View style={styles.metricLeft}>
              <CheckCheck color="#FFFFFF" size={20} style={styles.metricIcon} />
              <Text style={styles.metricText}>2 Done</Text>
            </View>
          </View>
        </TouchableOpacity>

        <DailyOverviewModal
          visible={showOverviewModal}
          onClose={() => setShowOverviewModal(false)}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.chatContainer}>
        <View style={[styles.logoContainer, { backgroundColor: currentTheme.colors.card }]}>
          <BrainCircuit color={currentTheme.colors.textPrimary} size={24} />
        </View>
        <View style={styles.messageContainer}>
          <View style={styles.messageHeader}>
            <Text style={[styles.agentName, { color: currentTheme.colors.textPrimary }]}>Pulse</Text>
            <TouchableOpacity 
              style={styles.dismissButton} 
              onPress={() => setShowMessage(false)}
            >
              <Check color={currentTheme.colors.textSecondary} size={18} />
            </TouchableOpacity>
          </View>
          <Text style={[styles.summaryText, { color: currentTheme.colors.textPrimary }]}>
            Today you have 3 priority tasks focused on Computer Science and Mathematics. 
            Your most important task is the "Algorithm Analysis" due at 2:00 PM. 
            I suggest starting with this as it requires focused concentration.
          </Text>
        </View>
      </View>

      {/* Overview Section Header */}
      <TouchableOpacity 
        style={styles.sectionHeader}
        onPress={() => setShowOverviewModal(true)}
        activeOpacity={0.7}
      >
        <Text style={[styles.sectionLabel, { color: currentTheme.colors.textSecondary }]}>
          OVERVIEW
        </Text>
        <BarChart3 size={16} color={currentTheme.colors.textSecondary} />
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.metricsCard}
        onPress={() => setShowOverviewModal(true)}
        activeOpacity={0.8}
      >
        <View style={styles.metricItem}>
          <View style={styles.metricLeft}>
            <CheckCircle2 color="#FFFFFF" size={20} style={styles.metricIcon} />
            <Text style={styles.metricText}>5 Tasks Today</Text>
          </View>
        </View>
        <View style={[styles.metricItem, styles.metricSpacing]}>
          <View style={styles.metricLeft}>
            <Clock color="#FFFFFF" size={20} style={styles.metricIcon} />
            <Text style={styles.metricText}>3.5h Est. Time</Text>
          </View>
        </View>
        <View style={[styles.metricItem, styles.metricSpacing]}>
          <View style={styles.metricLeft}>
            <CheckCheck color="#FFFFFF" size={20} style={styles.metricIcon} />
            <Text style={styles.metricText}>2 Done</Text>
          </View>
        </View>
      </TouchableOpacity>

      <DailyOverviewModal
        visible={showOverviewModal}
        onClose={() => setShowOverviewModal(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  chatContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 24,
    gap: 12,
  },
  logoContainer: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  messageContainer: {
    flex: 1,
  },
  messageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  agentName: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  dismissButton: {
    padding: 4,
    marginRight: -4,
  },
  summaryText: {
    fontSize: 19,
    lineHeight: 26,
  },
  metricsCard: {
    backgroundColor: '#000000',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    padding: 16,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  metricSpacing: {
    marginTop: 12,
  },
  metricLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricIcon: {
    opacity: 0.9,
  },
  metricText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '500',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
}); 