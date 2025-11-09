import React from 'react';
import { 
  View, 
  Text, 
  StyleSheet,
  Dimensions,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  Easing,
  withDelay,
} from 'react-native-reanimated';

import { colors } from '../constants/theme';

type ChartData = {
  name: string;
  color: string;
  hours: number;
};

type BarChartProps = {
  data: ChartData[];
};

const { width } = Dimensions.get('window');
const CHART_WIDTH = width - 48;
const BAR_HEIGHT = 24;
const MAX_HEIGHT = 8; // Maximum value to normalize the data

export default function BarChart({ data }: BarChartProps) {
  // Find the maximum value for scaling
  const maxValue = Math.max(...data.map(item => item.hours), MAX_HEIGHT);
  
  return (
    <View style={styles.container}>
      {data.map((item, index) => {
        // Calculate width percentage based on the value
        const widthPercentage = (item.hours / maxValue) * 100;
        
        // Create animated width value
        const animWidth = useSharedValue(0);
        
        // Start animation after component mounts
        React.useEffect(() => {
          animWidth.value = withDelay(
            index * 150,
            withTiming(widthPercentage, {
              duration: 800,
              easing: Easing.bezier(0.25, 0.1, 0.25, 1),
            })
          );
        }, []);
        
        // Create animated style
        const animatedStyle = useAnimatedStyle(() => {
          return {
            width: `${animWidth.value}%`,
          };
        });
        
        return (
          <View key={item.name} style={styles.barContainer}>
            <Text style={styles.barLabel}>{item.name}</Text>
            <View style={styles.barBackground}>
              <Animated.View
                style={[
                  styles.bar,
                  { backgroundColor: item.color },
                  animatedStyle,
                ]}
              />
            </View>
            <Text style={styles.barValue}>{item.hours}h</Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: CHART_WIDTH,
    alignSelf: 'center',
  },
  barContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  barLabel: {
    width: 60,
    fontSize: 14,
    color: colors.textSecondary,
    marginRight: 8,
  },
  barBackground: {
    flex: 1,
    height: BAR_HEIGHT,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    overflow: 'hidden',
  },
  bar: {
    height: '100%',
    borderRadius: 12,
  },
  barValue: {
    width: 40,
    fontSize: 14,
    color: colors.textPrimary,
    textAlign: 'right',
    marginLeft: 8,
  },
});