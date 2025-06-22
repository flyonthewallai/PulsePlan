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
import { SvgUri } from 'react-native-svg';

import { colors } from '@/constants/theme';
import { signIn, signUp, signInWithMagicLink, resetPassword, signInWithGoogle, signInWithApple, isNewUser } from '@/lib/supabase-rn';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';

const { width, height } = Dimensions.get('window');

interface PasswordRequirement {
  text: string;
  met: boolean;
}

const GoogleIcon = () => (
  <SvgUri
    width="24"
    height="24"
    uri="https://fonts.gstatic.com/s/i/productlogos/googleg/v6/24px.svg"
    style={{ marginRight: 12 }}
  />
);

export default function AuthScreen() {
  const router = useRouter();
  const { refreshAuth } = useAuth();
  const { currentTheme } = useTheme();
  const signupInProgress = useRef(false);
  const [activeTab, setActiveTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);
  
  const logoAnim = useRef({ opacity: new Animated.Value(0), translateY: new Animated.Value(20), scale: new Animated.Value(0.9) }).current;
  const appNameAnim = useRef({ opacity: new Animated.Value(0), translateY: new Animated.Value(20) }).current;
  const taglineAnim = useRef({ opacity: new Animated.Value(0), translateY: new Animated.Value(20) }).current;
  const subtitleAnim = useRef({ opacity: new Animated.Value(0), translateY: new Animated.Value(20) }).current;

  useEffect(() => {
    const logoAnimation = Animated.parallel([
        Animated.timing(logoAnim.opacity, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.spring(logoAnim.translateY, { toValue: 0, tension: 40, friction: 7, useNativeDriver: true }),
        Animated.spring(logoAnim.scale, { toValue: 1, tension: 40, friction: 7, useNativeDriver: true }),
    ]);

    const createTextAnimation = (animValues: { opacity: Animated.Value, translateY: Animated.Value }) => Animated.parallel([
        Animated.timing(animValues.opacity, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.spring(animValues.translateY, { toValue: 0, tension: 40, friction: 7, useNativeDriver: true }),
    ]);

    Animated.stagger(100, [
        logoAnimation,
        createTextAnimation(appNameAnim),
        createTextAnimation(taglineAnim),
        createTextAnimation(subtitleAnim),
    ]).start();
  }, []);

  const getPasswordStrength = (password: string) => {
    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    
    if (score < 3) return { strength: 'Weak', color: currentTheme.colors.error };
    if (score < 5) return { strength: 'Medium', color: currentTheme.colors.warning };
    return { strength: 'Strong', color: currentTheme.colors.success };
  };

  const getPasswordRequirements = (password: string): PasswordRequirement[] => [
    { text: 'At least 8 characters', met: password.length >= 8 },
    { text: 'Contains a number', met: /[0-9]/.test(password) },
    { text: 'Contains a lowercase letter', met: /[a-z]/.test(password) },
    { text: 'Contains an uppercase letter', met: /[A-Z]/.test(password) },
  ];

  const passwordStrength = getPasswordStrength(password);
  const passwordRequirements = getPasswordRequirements(password);
  const isPasswordValid = password.length > 0 && passwordRequirements.every(req => req.met);

  const handleGoogleSignIn = async () => {
    console.log('🔵 Google sign-in button pressed');
    setLoading(true);
    try {
      const { data, error } = await signInWithGoogle();
      if (error) throw error;
      // ... (rest of the function remains same)
    } catch (error) {
      Alert.alert('Google Sign-In Error', (error as Error).message || 'Failed to sign in with Google.');
    } finally {
      setLoading(false);
    }
  };

  const handleAppleSignIn = async () => {
    console.log('⚪️ Apple sign-in button pressed');
    setLoading(true);
    try {
      const { data, error } = await signInWithApple();
      if (error) throw error;
      // ... (rest of the function remains same)
    } catch (error) {
      Alert.alert('Apple Sign-In Error', (error as Error).message || 'Failed to sign in with Apple.');
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
      const { data, error } = await signIn(email, password);
      if (error) throw error;
      if (data && data.user) {
        await refreshAuth();
        // Navigation is handled by AuthContext
      }
    } catch (error) {
      Alert.alert('Sign In Failed', (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async () => {
    if (loading || signupInProgress.current) return;
    if (!email || !password || !confirmPassword || !name) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }
    if (!isPasswordValid) {
      Alert.alert('Error', 'Please ensure your password meets all requirements.');
      return;
    }

    setLoading(true);
    signupInProgress.current = true;
    try {
      const { data, error } = await signUp(email, password, name);
      if (error) throw error;
      if (data && data.user) {
        await refreshAuth();
        router.push('/onboarding'); // Go to onboarding after signup
      }
    } catch (error) {
      Alert.alert('Sign Up Failed', (error as Error).message);
    } finally {
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
      await signInWithMagicLink(email);
      Alert.alert('Success', 'Check your email for a magic link to sign in!');
    } catch (error) {
      Alert.alert('Error', (error as Error).message);
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
      await resetPassword(email);
      Alert.alert('Success', 'Check your email for password reset instructions!');
    } catch (error) {
      Alert.alert('Error', (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const isLogin = activeTab === 'login';

  const renderForm = () => {
    const passwordReqs = getPasswordRequirements(password);

    return (
      <View style={styles.formContainer}>
        {/* ... (input fields and other elements) ... */}
      </View>
    );
  };
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: currentTheme.colors.background }]}>
      <StatusBar barStyle={currentTheme.id.includes('dark') ? "light-content" : "dark-content"} />
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          <View style={styles.header}>
            <Animated.Image
              source={require('../assets/images/icon.png')}
              style={[
                styles.logo,
                {
                  opacity: logoAnim.opacity,
                  transform: [{ translateY: logoAnim.translateY }, { scale: logoAnim.scale }],
                },
              ]}
            />
            <Animated.Text
              style={[
                styles.appName,
                {
                  color: currentTheme.colors.textPrimary,
                  opacity: appNameAnim.opacity,
                  transform: [{ translateY: appNameAnim.translateY }],
                },
              ]}
            >
              PulsePlan
            </Animated.Text>
            <Animated.Text
              style={[
                styles.tagline,
                {
                  color: currentTheme.colors.textSecondary,
                  opacity: taglineAnim.opacity,
                  transform: [{ translateY: taglineAnim.translateY }],
                },
              ]}
            >
              Your academic life, optimized.
            </Animated.Text>
            <Animated.Text
              style={[
                styles.subtitle,
                {
                  color: currentTheme.colors.textSecondary,
                  opacity: subtitleAnim.opacity,
                  transform: [{ translateY: subtitleAnim.translateY }],
                },
              ]}
            >
              by Fly on the Wall LLC
            </Animated.Text>
          </View>

          {!showEmailForm && (
            <View style={styles.socialAuthContainer}>
              <TouchableOpacity style={[styles.socialButton, { backgroundColor: '#2E2E2E' }]} onPress={handleGoogleSignIn} disabled={loading}>
                <GoogleIcon />
                <Text style={styles.socialButtonText}>Continue with Google</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.socialButton, { backgroundColor: '#2E2E2E' }]} onPress={handleAppleSignIn} disabled={loading}>
                <Ionicons name="logo-apple" size={26} color="white" style={{ marginRight: 12 }} />
                <Text style={styles.socialButtonText}>Continue with Apple</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.socialButton, { backgroundColor: '#2E2E2E' }]} 
                onPress={() => setShowEmailForm(true)} 
                disabled={loading}
              >
                <Ionicons name="mail" size={24} color="white" style={{ marginRight: 12 }} />
                <Text style={styles.socialButtonText}>Continue with Email</Text>
              </TouchableOpacity>
            </View>
          )}
          
          {showEmailForm && (
            <>
              <View style={styles.formContainer}>
                <View style={styles.formHeader}>
                  <TouchableOpacity 
                    onPress={() => setShowEmailForm(false)} 
                    style={styles.backButton}
                    disabled={loading}
                  >
                    <Ionicons name="arrow-back" size={24} color={currentTheme.colors.primary} />
                  </TouchableOpacity>
                  <Text style={[styles.formTitle, { color: currentTheme.colors.textPrimary }]}>
                    {isLogin ? 'Sign In' : 'Create Account'}
                  </Text>
                </View>

                {!isLogin && (
                  <TextInput
                    style={[styles.input, { backgroundColor: currentTheme.colors.surface, color: currentTheme.colors.textPrimary }]}
                    placeholder="Full Name"
                    placeholderTextColor={currentTheme.colors.textSecondary}
                    value={name}
                    onChangeText={setName}
                    editable={!loading}
                  />
                )}
                <TextInput
                  style={[styles.input, { backgroundColor: currentTheme.colors.surface, color: currentTheme.colors.textPrimary }]}
                  placeholder="Email"
                  placeholderTextColor={currentTheme.colors.textSecondary}
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  editable={!loading}
                />
                <TextInput
                  style={[styles.input, { backgroundColor: currentTheme.colors.surface, color: currentTheme.colors.textPrimary }]}
                  placeholder="Password"
                  placeholderTextColor={currentTheme.colors.textSecondary}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  editable={!loading}
                  textContentType={isLogin ? 'password' : 'newPassword'}
                  selectionColor={currentTheme.colors.primary}
                />
                {!isLogin && password.length > 0 && (
                  <View style={styles.passwordFeedbackContainer}>
                    <View style={styles.strengthBar}>
                      <View style={[styles.strengthFill, { 
                        width: `${Math.min(100, (passwordStrength.strength === 'Weak' ? 33 : passwordStrength.strength === 'Medium' ? 66 : 100))}%`,
                        backgroundColor: passwordStrength.color,
                      }]} />
                    </View>
                    <Text style={[styles.strengthText, { color: passwordStrength.color }]}>
                      Strength: {passwordStrength.strength}
                    </Text>
                    {passwordRequirements.map((req, index) => (
                      <View key={index} style={styles.requirementRow}>
                        <Ionicons 
                          name={req.met ? 'checkmark-circle' : 'ellipse-outline'}
                          size={14} 
                          color={req.met ? currentTheme.colors.success : currentTheme.colors.textSecondary} 
                        />
                        <Text style={[styles.requirementText, { color: req.met ? currentTheme.colors.success : currentTheme.colors.textSecondary }]}>
                          {req.text}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
                {!isLogin && (
                  <TextInput
                    style={[styles.input, { backgroundColor: currentTheme.colors.surface, color: currentTheme.colors.textPrimary }]}
                    placeholder="Confirm Password"
                    placeholderTextColor={currentTheme.colors.textSecondary}
                    value={confirmPassword}
                    onChangeText={setConfirmPassword}
                    secureTextEntry={!showConfirmPassword}
                    editable={!loading}
                    textContentType="oneTimeCode"
                    selectionColor={currentTheme.colors.primary}
                  />
                )}
                {isLogin && (
                  <TouchableOpacity onPress={handleForgotPassword} style={styles.forgotPasswordButton}>
                    <Text style={[styles.forgotPasswordText, { color: currentTheme.colors.textSecondary }]}>Forgot Password?</Text>
                  </TouchableOpacity>
                )}
              </View>

              <TouchableOpacity onPress={isLogin ? handleSignIn : handleSignUp} disabled={loading}>
                <LinearGradient
                  colors={currentTheme.id.includes('dark') ? [currentTheme.colors.primary, '#4A90E2'] : [currentTheme.colors.primary, '#63B4FF']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.authButton}
                >
                  {loading ? (
                    <ActivityIndicator color="#FFFFFF" />
                  ) : (
                    <Text style={styles.authButtonText}>{isLogin ? 'Sign In' : 'Create Account'}</Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            
              {isLogin && (
                <TouchableOpacity style={styles.magicLinkButton} onPress={handleMagicLink} disabled={loading}>
                  <Text style={[styles.magicLinkText, { color: currentTheme.colors.textSecondary }]}>Sign in with Magic Link</Text>
                </TouchableOpacity>
              )}

              <View style={styles.footer}>
                <TouchableOpacity onPress={() => {
                  setActiveTab(isLogin ? 'signup' : 'login');
                  if (!showEmailForm) {
                    setShowEmailForm(true);
                  }
                }} disabled={loading}>
                  <Text style={[styles.footerText, { color: currentTheme.colors.textSecondary }]}>
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <Text style={{ color: currentTheme.colors.primary, fontWeight: '600' }}>
                      {isLogin ? 'Sign Up' : 'Sign In'}
                    </Text>
                  </Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logo: {
    width: 100,
    height: 100,
    borderRadius: 24, // Softer corners
  },
  appName: {
    marginTop: 12,
    fontSize: 28,
    fontWeight: '700',
  },
  tagline: {
    marginTop: 12,
    fontSize: 16,
    fontWeight: '500',
  },
  subtitle: {
    marginTop: 4,
    fontSize: 12,
    fontWeight: '400',
  },
  socialAuthContainer: {
    flexDirection: 'column',
    marginBottom: 24,
    gap: 16,
  },
  socialButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
  },
  socialButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 12,
  },
  dividerLine: {
    flex: 1,
    height: 1,
  },
  dividerText: {
    marginHorizontal: 16,
    fontSize: 12,
    fontWeight: '600',
  },
  authButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  authButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  footer: {
    marginTop: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
  },
  formContainer: {
    marginBottom: 16,
    gap: 16,
  },
  input: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    fontSize: 16,
  },
  passwordFeedbackContainer: {
    gap: 8,
    marginBottom: 8,
  },
  strengthBar: {
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(128, 128, 128, 0.2)',
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthText: {
    fontSize: 12,
    fontWeight: '500',
  },
  requirementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  requirementText: {
    fontSize: 12,
  },
  forgotPasswordButton: {
    alignSelf: 'flex-end',
    marginBottom: 8,
  },
  forgotPasswordText: {
    fontSize: 12,
    fontWeight: '500',
  },
  magicLinkButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  magicLinkText: {
    fontSize: 14,
    fontWeight: '500',
  },
  formHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  backButton: {
    padding: 8,
    marginRight: 12,
  },
  formTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
});

