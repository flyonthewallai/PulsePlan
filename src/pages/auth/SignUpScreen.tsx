import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Image,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';

type AuthStackParamList = {
  Login: undefined;
  SignUp: undefined;
  ForgotPassword: undefined;
  Main: undefined;
};

type SignUpScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'SignUp'>;

interface PasswordRequirement {
  text: string;
  met: boolean;
}

export const SignUpScreen = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { signUp } = useAuth();
  const navigation = useNavigation<SignUpScreenNavigationProp>();

  // Password strength calculation
  const getPasswordStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    
    if (score < 3) return { strength: 'Weak', color: '#EF4444' };
    if (score < 5) return { strength: 'Medium', color: '#F59E0B' };
    return { strength: 'Strong', color: '#10B981' };
  };

  // Password requirements
  const getPasswordRequirements = (password: string): PasswordRequirement[] => [
    { text: 'At least 8 characters', met: password.length >= 8 },
    { text: 'Contains lowercase letter', met: /[a-z]/.test(password) },
    { text: 'Contains uppercase letter', met: /[A-Z]/.test(password) },
    { text: 'Contains number', met: /[0-9]/.test(password) },
    { text: 'Contains special character', met: /[^A-Za-z0-9]/.test(password) },
  ];

  const passwordStrength = getPasswordStrength(password);
  const passwordRequirements = getPasswordRequirements(password);
  const isPasswordValid = password.length >= 8 && passwordRequirements.slice(1, 4).some(req => req.met);

  const handleSignUp = async () => {
    if (!email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (!isPasswordValid) {
      Alert.alert('Error', 'Password must be at least 8 characters and contain at least one letter and one number');
      return;
    }

    setLoading(true);
    try {
      const { error } = await signUp(email, password);
      
      if (error) {
        Alert.alert('Error', error.message);
      } else {
        Alert.alert(
          'Success',
          'Account created successfully! Please check your email to confirm your account, then you\'ll be guided through setting up your personalized experience.',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      Alert.alert('Error', 'An unexpected error occurred');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.header}>
            <Image 
              source={require('../../../assets/icon.png')} 
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.title}>Create Account</Text>
            <Text style={styles.subtitle}>Join PulsePlan and start your learning journey</Text>
          </View>
          
          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Email</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
                autoComplete="email"
                placeholderTextColor="#9CA3AF"
              />
            </View>
            
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Password</Text>
              <View style={styles.passwordInputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Create a password"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                  autoComplete="password-new"
                  placeholderTextColor="#9CA3AF"
                />
                <TouchableOpacity
                  style={styles.passwordToggle}
                  onPress={() => setShowPassword(!showPassword)}
                >
                  <Ionicons name={showPassword ? 'eye' : 'eye-off'} size={20} color="#9CA3AF" />
                </TouchableOpacity>
              </View>
              
              {/* Password Strength Indicator */}
              {password.length > 0 && (
                <View style={styles.passwordFeedback}>
                  <View style={styles.strengthContainer}>
                    <Text style={styles.strengthLabel}>Password Strength: </Text>
                    <Text style={[styles.strengthText, { color: passwordStrength.color }]}>
                      {passwordStrength.strength}
                    </Text>
                  </View>
                  
                  {/* Strength Bar */}
                  <View style={styles.strengthBar}>
                    <View 
                      style={[
                        styles.strengthFill, 
                        { 
                          width: passwordStrength.strength === 'Weak' ? '33%' : 
                                passwordStrength.strength === 'Medium' ? '66%' : '100%',
                          backgroundColor: passwordStrength.color 
                        }
                      ]} 
                    />
                  </View>
                  
                  {/* Requirements List */}
                  <View style={styles.requirementsList}>
                    {passwordRequirements.map((requirement, index) => (
                      <View key={index} style={styles.requirementItem}>
                        <Ionicons 
                          name={requirement.met ? 'checkmark-circle' : 'close-circle'} 
                          size={16} 
                          color={requirement.met ? '#10B981' : '#EF4444'} 
                        />
                        <Text style={[
                          styles.requirementText,
                          { color: requirement.met ? '#10B981' : '#6B7280' }
                        ]}>
                          {requirement.text}
                        </Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}
            </View>
            
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Confirm Password</Text>
              <View style={styles.passwordInputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  secureTextEntry={!showConfirmPassword}
                  autoCapitalize="none"
                  autoComplete="password-new"
                  placeholderTextColor="#9CA3AF"
                />
                <TouchableOpacity
                  style={styles.passwordToggle}
                  onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  <Ionicons name={showConfirmPassword ? 'eye' : 'eye-off'} size={20} color="#9CA3AF" />
                </TouchableOpacity>
              </View>
              
              {/* Password Match Indicator */}
              {confirmPassword.length > 0 && (
                <View style={styles.matchIndicator}>
                  <Ionicons 
                    name={password === confirmPassword ? 'checkmark-circle' : 'close-circle'} 
                    size={16} 
                    color={password === confirmPassword ? '#10B981' : '#EF4444'} 
                  />
                  <Text style={[
                    styles.matchText,
                    { color: password === confirmPassword ? '#10B981' : '#EF4444' }
                  ]}>
                    {password === confirmPassword ? 'Passwords match' : 'Passwords do not match'}
                  </Text>
                </View>
              )}
            </View>
            
            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleSignUp}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Create Account</Text>
              )}
            </TouchableOpacity>
            
            <View style={styles.loginContainer}>
              <Text style={styles.loginText}>Already have an account? </Text>
              <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                <Text style={styles.loginLink}>Log In</Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logo: {
    width: 80,
    height: 80,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0D1B2A',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    backgroundColor: '#F9FAFB',
    color: '#1F2937',
  },
  button: {
    backgroundColor: '#00AEEF',
    height: 50,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#00AEEF',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginText: {
    fontSize: 14,
    color: '#6B7280',
  },
  loginLink: {
    fontSize: 14,
    color: '#00AEEF',
    fontWeight: '600',
  },
  passwordToggle: {
    position: 'absolute',
    right: 16,
    top: 16,
  },
  passwordInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  passwordFeedback: {
    flexDirection: 'column',
    alignItems: 'flex-start',
  },
  strengthContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  strengthLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginRight: 8,
  },
  strengthText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  strengthBar: {
    height: 8,
    width: '100%',
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 4,
  },
  requirementsList: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  requirementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 8,
  },
  requirementText: {
    fontSize: 14,
    color: '#6B7280',
  },
  matchIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  matchText: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 8,
  },
}); 