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
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';

import { colors } from '@/constants/theme';
import { signIn, signUp, signInWithMagicLink, resetPassword, signInWithGoogle, signInWithMicrosoft, signInWithApple, isNewUser } from '@/lib/supabase-rn';
import { useAuth } from '@/contexts/AuthContext';

const { width, height } = Dimensions.get('window');

interface PasswordRequirement {
  text: string;
  met: boolean;
}

// Animated Neural Network Component
const NeuralNetwork = () => {
  const animatedValues = useRef(
    Array.from({ length: 12 }, () => new Animated.Value(0))
  ).current;

  useEffect(() => {
    const startAnimations = () => {
      const animations = animatedValues.map((value, index) => 
        Animated.loop(
          Animated.sequence([
            Animated.timing(value, {
              toValue: 1,
              duration: 2000 + (index * 200),
              useNativeDriver: true,
            }),
            Animated.timing(value, {
              toValue: 0,
              duration: 2000 + (index * 200),
              useNativeDriver: true,
            }),
          ])
        )
      );
      
      Animated.stagger(300, animations).start(() => {
        setTimeout(startAnimations, 1000);
      });
    };

    startAnimations();
  }, []);

  return (
    <View style={styles.neuralNetworkContainer}>
      {animatedValues.map((animValue, index) => (
        <Animated.View
          key={index}
          style={[
            styles.neuralNode,
            {
              left: `${(index % 4) * 25 + 10}%`,
              top: `${Math.floor(index / 4) * 30 + 10}%`,
              opacity: animValue,
              transform: [
                {
                  scale: animValue.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.3, 1],
                  }),
                },
              ],
            },
          ]}
        />
      ))}
      
      {/* Connection lines */}
      {[...Array(8)].map((_, index) => (
        <Animated.View
          key={`line-${index}`}
          style={[
            styles.connectionLine,
            {
              opacity: animatedValues[index % animatedValues.length],
              transform: [
                {
                  rotate: `${index * 45}deg`,
                },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
};

// Floating Particles Component
const FloatingParticles = () => {
  const particles = useRef(
    Array.from({ length: 20 }, () => ({
      animValue: new Animated.Value(0),
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 4 + 2,
    }))
  ).current;

  useEffect(() => {
    particles.forEach((particle, index) => {
      const animate = () => {
        Animated.loop(
          Animated.timing(particle.animValue, {
            toValue: 1,
            duration: 3000 + Math.random() * 2000,
            useNativeDriver: true,
          })
        ).start();
      };
      
      setTimeout(animate, index * 100);
    });
  }, []);

  return (
    <View style={styles.particlesContainer}>
      {particles.map((particle, index) => (
        <Animated.View
          key={index}
          style={[
            styles.particle,
            {
              left: particle.x,
              top: particle.y,
              width: particle.size,
              height: particle.size,
              opacity: particle.animValue.interpolate({
                inputRange: [0, 0.5, 1],
                outputRange: [0.1, 0.6, 0.1],
              }),
              transform: [
                {
                  translateY: particle.animValue.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, -50],
                  }),
                },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
};

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
  
  // Brand animation
  const logoScale = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Logo entrance animation
    Animated.sequence([
      Animated.timing(logoScale, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(taglineOpacity, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

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

  // OAuth Sign-In Handlers
  const handleGoogleSignIn = async () => {
    console.log('🔵 Google sign-in button pressed');
    setLoading(true);
    try {
      console.log('🔑 Initiating Google OAuth...');
      const { data, error } = await signInWithGoogle();
      
      if (error) {
        console.error('❌ Google OAuth error:', error);
        Alert.alert('Google Sign-In Error', error.message || 'Failed to sign in with Google. Please try again.');
        return;
      }

      if (data?.url) {
        console.log('🌐 Google OAuth URL generated, opening browser...');
        // For React Native, we need to open the OAuth URL in browser
        // This would typically use expo-auth-session or similar
        Alert.alert(
          'OAuth Setup Required', 
          'Google OAuth requires additional configuration. Please contact support or use email login for now.'
        );
      } else {
        console.log('⚠️ No OAuth URL received from Supabase');
        Alert.alert('Configuration Error', 'OAuth is not properly configured. Please use email login.');
      }
    } catch (error) {
      console.error('💥 Unexpected Google sign-in error:', error);
      Alert.alert('Error', 'An unexpected error occurred with Google sign-in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftSignIn = async () => {
    console.log('🔵 Microsoft sign-in button pressed');
    setLoading(true);
    try {
      console.log('🔑 Initiating Microsoft OAuth...');
      const { data, error } = await signInWithMicrosoft();
      
      if (error) {
        console.error('❌ Microsoft OAuth error:', error);
        Alert.alert('Microsoft Sign-In Error', error.message || 'Failed to sign in with Microsoft. Please try again.');
        return;
      }

      if (data?.url) {
        console.log('🌐 Microsoft OAuth URL generated, opening browser...');
        Alert.alert(
          'OAuth Setup Required', 
          'Microsoft OAuth requires additional configuration. Please contact support or use email login for now.'
        );
      } else {
        console.log('⚠️ No OAuth URL received from Supabase');
        Alert.alert('Configuration Error', 'OAuth is not properly configured. Please use email login.');
      }
    } catch (error) {
      console.error('💥 Unexpected Microsoft sign-in error:', error);
      Alert.alert('Error', 'An unexpected error occurred with Microsoft sign-in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAppleSignIn = async () => {
    console.log('🔵 Apple sign-in button pressed');
    setLoading(true);
    try {
      console.log('🔑 Initiating Apple OAuth...');
      const { data, error } = await signInWithApple();
      
      if (error) {
        console.error('❌ Apple OAuth error:', error);
        Alert.alert('Apple Sign-In Error', error.message || 'Failed to sign in with Apple. Please try again.');
        return;
      }

      if (data?.url) {
        console.log('🌐 Apple OAuth URL generated, opening browser...');
        Alert.alert(
          'OAuth Setup Required', 
          'Apple OAuth requires additional configuration. Please contact support or use email login for now.'
        );
      } else {
        console.log('⚠️ No OAuth URL received from Supabase');
        Alert.alert('Configuration Error', 'OAuth is not properly configured. Please use email login.');
      }
    } catch (error) {
      console.error('💥 Unexpected Apple sign-in error:', error);
      Alert.alert('Error', 'An unexpected error occurred with Apple sign-in. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSignIn = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      console.log('🔑 Attempting email/password sign in for:', email);
      const { data, error } = await signIn(email, password);
      
      if (error) {
        console.error('❌ Sign in error:', error);
        Alert.alert('Sign In Failed', error.message || 'An error occurred during sign in');
        return;
      }

      if (data && data.user) {
        console.log('✅ User signed in successfully:', data.user.email);
        
        // Check if user needs onboarding
        const needsOnboarding = isNewUser(data.user);
        console.log('🎯 Onboarding check result:', { needsOnboarding });
        
        // Refresh the auth context to pick up the new session
        await refreshAuth();
        
        // Navigation will be handled automatically by AuthContext based on onboarding status
        if (needsOnboarding) {
          console.log('🎉 New user detected, will redirect to onboarding');
        } else {
          console.log('👋 Returning user, will redirect to main app');
        }
      }
    } catch (error) {
      console.error('💥 Unexpected sign in error:', error);
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
        console.error('❌ Sign up error:', error);
        Alert.alert('Sign Up Failed', error.message || 'An error occurred during sign up');
        return;
      }

      if (data && data.user) {
        console.log('✅ Signup successful for user:', data.user.email);
        console.log('🎯 New user created, directing to onboarding...');
        
        // For new signups, always go to onboarding
        router.push('/onboarding');
        
        // Clear form data
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        setName('');
      }
    } catch (error) {
      console.error('💥 Unexpected sign up error:', error);
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
      console.log('🪄 Sending magic link to:', email);
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
      console.log('🔒 Sending password reset to:', email);
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
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      {/* Dynamic Background */}
      <LinearGradient
        colors={['#0A0A0A', '#1A1A2E', '#16213E', '#0F0F0F']}
        style={styles.backgroundGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      
      {/* Neural Network Background */}
      <NeuralNetwork />
      
      {/* Floating Particles */}
      <FloatingParticles />
      
      {/* Blur Overlay */}
      <BlurView intensity={20} style={styles.blurOverlay} />
      
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView 
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {/* Brand Header */}
            <View style={styles.brandContainer}>
              <Animated.View style={[styles.logoContainer, { transform: [{ scale: logoScale }] }]}>
                <LinearGradient
                  colors={['#4F8CFF', '#9D4DFF', '#FF6B6B']}
                  style={styles.logoBackground}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Image 
                    source={require('@/assets/images/icon.png')} 
                    style={styles.logoImage}
                    resizeMode="contain"
                  />
                </LinearGradient>
                <Text style={styles.appName}>PulsePlan</Text>
                <Text style={styles.brandSubtitle}>by FlyOnTheWall LLC</Text>
              </Animated.View>
              
              <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
                Quietly building loud ideas
              </Animated.Text>
            </View>

            {/* Auth Tabs */}
            <BlurView intensity={30} style={styles.tabContainer}>
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
            </BlurView>

            {/* OAuth Buttons */}
            <View style={styles.oauthContainer}>
              <TouchableOpacity
                style={styles.oauthButton}
                onPress={handleGoogleSignIn}
                disabled={loading}
              >
                <BlurView intensity={40} style={styles.oauthButtonBlur}>
                  <Ionicons name="logo-google" size={20} color="#EA4335" />
                  <Text style={styles.oauthButtonText}>Google</Text>
                </BlurView>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.oauthButton}
                onPress={handleMicrosoftSignIn}
                disabled={loading}
              >
                <BlurView intensity={40} style={styles.oauthButtonBlur}>
                  <Ionicons name="logo-microsoft" size={20} color="#00A4EF" />
                  <Text style={styles.oauthButtonText}>Microsoft</Text>
                </BlurView>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.oauthButton}
                onPress={handleAppleSignIn}
                disabled={loading}
              >
                <BlurView intensity={40} style={styles.oauthButtonBlur}>
                  <Ionicons name="logo-apple" size={20} color="#FFFFFF" />
                  <Text style={styles.oauthButtonText}>Apple</Text>
                </BlurView>
              </TouchableOpacity>
            </View>

            {/* Divider */}
            <View style={styles.dividerContainer}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or continue with email</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Form Container */}
            <BlurView intensity={30} style={styles.formContainer}>
              {activeTab === 'signup' && (
                <View style={styles.inputContainer}>
                  <Text style={styles.inputLabel}>Full Name *</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Enter your full name"
                    placeholderTextColor="rgba(255, 255, 255, 0.5)"
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
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
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
                      placeholderTextColor="rgba(255, 255, 255, 0.5)"
                      secureTextEntry={!showPassword}
                      value={password}
                      onChangeText={setPassword}
                      editable={!loading}
                    />
                    <TouchableOpacity
                      style={styles.passwordToggle}
                      onPress={() => setShowPassword(!showPassword)}
                    >
                      <Ionicons name={showPassword ? 'eye' : 'eye-off'} size={20} color="rgba(255, 255, 255, 0.7)" />
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
                              { color: requirement.met ? '#10B981' : 'rgba(255, 255, 255, 0.6)' }
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
                      placeholderTextColor="rgba(255, 255, 255, 0.5)"
                      secureTextEntry={!showConfirmPassword}
                      value={confirmPassword}
                      onChangeText={setConfirmPassword}
                      editable={!loading}
                    />
                    <TouchableOpacity
                      style={styles.passwordToggle}
                      onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      <Ionicons name={showConfirmPassword ? 'eye' : 'eye-off'} size={20} color="rgba(255, 255, 255, 0.7)" />
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
            </BlurView>

            {/* Action Buttons */}
            <View style={styles.footer}>
              <TouchableOpacity
                style={[styles.authButton, loading && styles.authButtonDisabled]}
                onPress={activeTab === 'login' ? handleSignIn : handleSignUp}
                disabled={loading}
              >
                <LinearGradient
                  colors={['#4F8CFF', '#9D4DFF']}
                  style={styles.authButtonGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={styles.authButtonText}>
                      {activeTab === 'login' ? 'Login' : 'Create Account'}
                    </Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>

              {activeTab === 'login' && (
                <TouchableOpacity 
                  style={styles.magicLinkButton}
                  onPress={handleMagicLink}
                  disabled={loading}
                >
                  <BlurView intensity={30} style={styles.magicLinkBlur}>
                    <Ionicons name="mail-outline" size={20} color="rgba(255, 255, 255, 0.9)" />
                    <Text style={styles.magicLinkText}>Login with Magic Link</Text>
                  </BlurView>
                </TouchableOpacity>
              )}
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  backgroundGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  neuralNetworkContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  neuralNode: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(79, 140, 255, 0.4)',
    shadowColor: '#4F8CFF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 3,
  },
  connectionLine: {
    position: 'absolute',
    left: '50%',
    top: '50%',
    width: 1,
    height: 100,
    backgroundColor: 'rgba(79, 140, 255, 0.2)',
    marginLeft: -0.5,
    marginTop: -50,
  },
  particlesContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  particle: {
    position: 'absolute',
    borderRadius: 2,
    backgroundColor: 'rgba(157, 77, 255, 0.3)',
  },
  blurOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  brandContainer: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  logoBackground: {
    width: 120,
    height: 120,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    shadowColor: '#4F8CFF',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
  },
  logoImage: {
    width: 80,
    height: 80,
  },
  appName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  brandSubtitle: {
    fontSize: 14,
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.7)',
    letterSpacing: 0.5,
  },
  tagline: {
    fontSize: 16,
    fontStyle: 'italic',
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    fontWeight: '300',
  },
  tabContainer: {
    flexDirection: 'row',
    marginBottom: 24,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: 'rgba(79, 140, 255, 0.3)',
  },
  tabText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.7)',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  oauthContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    gap: 12,
  },
  oauthButton: {
    flex: 1,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  oauthButtonBlur: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    gap: 8,
  },
  oauthButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  dividerText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
    marginHorizontal: 16,
    fontWeight: '500',
  },
  formContainer: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    overflow: 'hidden',
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 8,
    fontWeight: '600',
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    color: '#FFFFFF',
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  passwordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  passwordInput: {
    flex: 1,
    padding: 16,
    color: '#FFFFFF',
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
    color: 'rgba(255, 255, 255, 0.7)',
  },
  strengthText: {
    fontSize: 14,
    fontWeight: '600',
  },
  strengthBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
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
    color: '#4F8CFF',
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    marginTop: 'auto',
    marginBottom: 32,
  },
  authButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#4F8CFF',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  authButtonDisabled: {
    opacity: 0.7,
  },
  authButtonGradient: {
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  authButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  magicLinkButton: {
    marginTop: 16,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  magicLinkBlur: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  magicLinkText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});