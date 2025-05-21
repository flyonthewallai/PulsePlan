import { useRef, useEffect } from 'react';
import { Animated, Dimensions } from 'react-native';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

interface UseModalAnimationProps {
  isVisible: boolean;
  onClose?: () => void;
  modalHeight?: number;
  animationDuration?: number;
}

export const useModalAnimation = ({
  isVisible,
  onClose,
  modalHeight = SCREEN_HEIGHT * 0.8,
  animationDuration = 300
}: UseModalAnimationProps) => {
  const translateY = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const overlayOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isVisible) {
      // Reset values
      translateY.setValue(SCREEN_HEIGHT);
      opacity.setValue(0);
      overlayOpacity.setValue(0);

      // Animate in
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: animationDuration,
          useNativeDriver: true,
        }),
        Animated.timing(overlayOpacity, {
          toValue: 1,
          duration: animationDuration,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Animate out
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: SCREEN_HEIGHT,
          duration: animationDuration,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver: true,
        }),
        Animated.timing(overlayOpacity, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver: true,
        }),
      ]).start(() => {
        if (onClose) {
          onClose();
        }
      });
    }
  }, [isVisible, animationDuration, modalHeight, onClose]);

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  return {
    translateY,
    opacity,
    overlayOpacity,
    handleClose,
    modalHeight,
  };
}; 