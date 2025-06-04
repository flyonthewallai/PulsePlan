import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  StatusBar,
  Image,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { colors } from '@/constants/theme';
import { signIn, signUp, signInWithMagicLink, resetPassword } from '@/lib/supabase-rn';
import { useAuth } from '@/contexts/AuthContext';

interface PasswordRequirement {
  text: string;
  met: boolean;
}

export default function AuthScreen() {
  const router = useRouter();
  const { refreshAuth } = useAuth();
  const signupInProgress = useRef(false);
  const [activeTab, setActiveTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
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
  
  const handleSignIn = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await signIn(email, password);
      
      if (error) {
        console.error('Sign in error:', error);
        Alert.alert('Sign In Failed', error.message || 'An error occurred during sign in');
        return;
      }

      if (data && data.user) {
        console.log('User signed in successfully:', data.user.email);
        // Refresh the auth context to pick up the new session
        await refreshAuth();
        // Navigation will be handled automatically by the auth context
      }
    } catch (error) {
      console.error('Unexpected sign in error:', error);
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async () => {
    // Prevent double execution with multiple checks
    if (loading || signupInProgress.current) {
      console.log('⚠️ Signup already in progress, skipping...');
      return;
    }
    
    if (!email || !password || !confirmPassword || !name) {
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

    // Set both loading state and ref flag
    setLoading(true);
    signupInProgress.current = true;
    
    try {
      console.log('🚀 Starting signup process for:', email);
      const { data, error } = await signUp(email, password, name);
      
      if (error) {
        console.error('Sign up error:', error);
        Alert.alert('Sign Up Failed', error.message || 'An error occurred during sign up');
        return;
      }

      if (data && data.user) {
        console.log('✅ Signup successful, navigating to onboarding...');
        // Navigate directly to onboarding without showing alert to prevent double execution
        router.push('/onboarding');
        // Clear form data
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        setName('');
      }
    } catch (error) {
      console.error('Unexpected sign up error:', error);
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      // Reset both flags
      setLoading(false);
      signupInProgress.current = false;
    }
  };

  const handleMagicLink = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter your email address');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await signInWithMagicLink(email);
      
      if (error) {
        console.error('Magic link error:', error);
        Alert.alert('Error', error.message || 'An error occurred sending magic link');
        return;
      }

      Alert.alert('Success', 'Check your email for a magic link to sign in!');
    } catch (error) {
      console.error('Unexpected magic link error:', error);
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter your email address first');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await resetPassword(email);
      
      if (error) {
        console.error('Reset password error:', error);
        Alert.alert('Error', error.message || 'An error occurred sending reset email');
        return;
      }

      Alert.alert('Success', 'Check your email for password reset instructions!');
    } catch (error) {
      console.error('Unexpected reset password error:', error);
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" />
      
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.logoContainer}>
            <View style={styles.logoBackground}>
              <Image 
                source={require('@/assets/images/icon.png')} 
                style={styles.logoImage}
                resizeMode="contain"
              />
            </View>
            <Text style={styles.appName}>PulsePlan</Text>
          </View>

          <View style={styles.tabContainer}>
            <TouchableOpacity
              style={[
                styles.tab,
                activeTab === 'login' && styles.activeTab,
              ]}
              onPress={() => setActiveTab('login')}
              disabled={loading}
            >
              <Text 
                style={[
                  styles.tabText,
                  activeTab === 'login' && styles.activeTabText,
                ]}
              >
                Login
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[
                styles.tab,
                activeTab === 'signup' && styles.activeTab,
              ]}
              onPress={() => setActiveTab('signup')}
              disabled={loading}
            >
              <Text 
                style={[
                  styles.tabText,
                  activeTab === 'signup' && styles.activeTabText,
                ]}
              >
                Sign Up
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.formContainer}>
            {activeTab === 'signup' && (
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Full Name *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Enter your full name"
                  placeholderTextColor={colors.textSecondary}
                  value={name}
                  onChangeText={setName}
                  editable={!loading}
                />
              </View>
            )}
            
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Email *</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your email"
                placeholderTextColor={colors.textSecondary}
                keyboardType="email-address"
                autoCapitalize="none"
                value={email}
                onChangeText={setEmail}
                editable={!loading}
              />
            </View>
            
            {(activeTab === 'login' || activeTab === 'signup') && (
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Password {activeTab === 'signup' && '*'}</Text>
                <View style={styles.passwordContainer}>
                  <TextInput
                    style={styles.passwordInput}
                    placeholder={activeTab === 'signup' ? "Create a password" : "Enter your password"}
                    placeholderTextColor={colors.textSecondary}
                    secureTextEntry={!showPassword}
                    value={password}
                    onChangeText={setPassword}
                    editable={!loading}
                  />
                  <TouchableOpacity
                    style={styles.passwordToggle}
                    onPress={() => setShowPassword(!showPassword)}
                  >
                    <Ionicons name={showPassword ? 'eye' : 'eye-off'} size={20} color={colors.textSecondary} />
                  </TouchableOpacity>
                </View>
                
                {/* Password Strength Indicator for Signup */}
                {activeTab === 'signup' && password.length > 0 && (
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
                            size={14} 
                            color={requirement.met ? '#10B981' : '#EF4444'} 
                          />
                          <Text style={[
                            styles.requirementText,
                            { color: requirement.met ? '#10B981' : colors.textSecondary }
                          ]}>
                            {requirement.text}
                          </Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )}
              </View>
            )}
            
            {activeTab === 'signup' && (
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Confirm Password *</Text>
                <View style={styles.passwordContainer}>
                  <TextInput
                    style={styles.passwordInput}
                    placeholder="Confirm your password"
                    placeholderTextColor={colors.textSecondary}
                    secureTextEntry={!showConfirmPassword}
                    value={confirmPassword}
                    onChangeText={setConfirmPassword}
                    editable={!loading}
                  />
                  <TouchableOpacity
                    style={styles.passwordToggle}
                    onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    <Ionicons name={showConfirmPassword ? 'eye' : 'eye-off'} size={20} color={colors.textSecondary} />
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
            )}
            
            {activeTab === 'login' && (
              <TouchableOpacity 
                style={styles.forgotPasswordContainer}
                onPress={handleForgotPassword}
                disabled={loading}
              >
                <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.footer}>
            <TouchableOpacity
              style={[styles.authButton, loading && styles.authButtonDisabled]}
              onPress={activeTab === 'login' ? handleSignIn : handleSignUp}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.authButtonText}>
                  {activeTab === 'login' ? 'Login' : 'Create Account'}
                </Text>
              )}
            </TouchableOpacity>

            {activeTab === 'login' && (
              <>
                <View style={styles.orContainer}>
                  <View style={styles.divider} />
                  <Text style={styles.orText}>or</Text>
                  <View style={styles.divider} />
                </View>

                <TouchableOpacity 
                  style={styles.magicLinkButton}
                  onPress={handleMagicLink}
                  disabled={loading}
                >
                  <Ionicons name="mail-outline" size={20} color={colors.textPrimary} />
                  <Text style={styles.magicLinkText}>Login with Magic Link</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 32,
  },
  logoBackground: {
    width: 120,
    height: 120,
    borderRadius: 0,
    backgroundColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: -10,
  },
  logoImage: {
    width: 120,
    height: 120,
  },
  appName: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  tabContainer: {
    flexDirection: 'row',
    marginBottom: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 12,
  },
  activeTab: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  tabText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  activeTabText: {
    color: colors.textPrimary,
  },
  formContainer: {
    marginBottom: 32,
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 16,
    color: colors.textPrimary,
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  passwordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  passwordInput: {
    flex: 1,
    padding: 16,
    color: colors.textPrimary,
    fontSize: 16,
  },
  passwordToggle: {
    padding: 16,
  },
  passwordFeedback: {
    marginTop: 12,
  },
  strengthContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  strengthLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  strengthText: {
    fontSize: 14,
    fontWeight: '600',
  },
  strengthBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 12,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  requirementsList: {
    gap: 6,
  },
  requirementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  requirementText: {
    fontSize: 12,
    fontWeight: '500',
  },
  matchIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 8,
  },
  matchText: {
    fontSize: 14,
    fontWeight: '500',
  },
  forgotPasswordContainer: {
    alignSelf: 'flex-end',
    marginTop: 8,
  },
  forgotPasswordText: {
    color: colors.primaryBlue,
    fontSize: 14,
    fontWeight: '500',
  },
  footer: {
    marginTop: 'auto',
    marginBottom: 32,
  },
  authButton: {
    backgroundColor: colors.primaryBlue,
    borderRadius: 28,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: colors.primaryBlue,
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  authButtonDisabled: {
    opacity: 0.7,
  },
  authButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  orContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  orText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginHorizontal: 16,
  },
  magicLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 28,
    paddingVertical: 16,
    gap: 8,
  },
  magicLinkText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.textPrimary,
  },
});