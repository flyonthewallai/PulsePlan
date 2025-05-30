import { View, ActivityIndicator } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { colors } from '@/constants/theme';

export default function Index() {
  const { loading } = useAuth();

  console.log('📱 Index component render - navigation handled by AuthContext');

  return (
    <View style={{ 
      flex: 1, 
      justifyContent: 'center', 
      alignItems: 'center', 
      backgroundColor: colors.backgroundDark 
    }}>
      <ActivityIndicator size="large" color={colors.primaryBlue} />
    </View>
  );
}