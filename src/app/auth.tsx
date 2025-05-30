import React, { useState, useEffect } from 'react';
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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { ArrowRight, Mail } from 'lucide-react-native';
import { useRouter } from 'expo-router';

import { colors } from '@/constants/theme';
import { signIn, signUp, signInWithMagicLink, resetPassword } from '@/lib/supabase-rn';
import { useAuth } from '@/contexts/AuthContext';

export default function AuthScreen() {
  const router = useRouter();
  const { refreshAuth } = useAuth();
  const [activeTab, setActiveTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  
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
        // Navigation will be handled automatically by the index page
      }
    } catch (error) {
      console.error('Unexpected sign in error:', error);
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async () => {
    if (!email || !name) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await signUp(email, password || 'temp-password', name);
      
      if (error) {
        console.error('Sign up error:', error);
        Alert.alert('Sign Up Failed', error.message || 'An error occurred during sign up');
        return;
      }

      if (data && data.user) {
        Alert.alert(
          'Success', 
          'Please check your email for a confirmation link.',
          [{ text: 'OK', onPress: () => setActiveTab('login') }]
        );
      }
    } catch (error) {
      console.error('Unexpected sign up error:', error);
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setLoading(false);
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
      
      <View style={styles.logoContainer}>
        <LinearGradient
          colors={[colors.primaryBlue, colors.accentPurple]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.logoBackground}
        >
          <Text style={styles.logoText}>PP</Text>
        </LinearGradient>
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
            <Text style={styles.inputLabel}>Name *</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter your name"
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
        
        {activeTab === 'login' && (
          <>
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Password</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your password"
                placeholderTextColor={colors.textSecondary}
                secureTextEntry
                value={password}
                onChangeText={setPassword}
                editable={!loading}
              />
            </View>
            
            <TouchableOpacity 
              style={styles.forgotPasswordContainer}
              onPress={handleForgotPassword}
              disabled={loading}
            >
              <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      <View style={styles.footer}>
        {activeTab === 'login' ? (
          <>
            <LinearGradient
              colors={[colors.primaryBlue, colors.accentPurple]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.authButton}
            >
              <TouchableOpacity
                style={styles.authButtonTouchable}
                onPress={handleSignIn}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <>
                    <Text style={styles.authButtonText}>Login</Text>
                    <ArrowRight size={20} color="#fff" />
                  </>
                )}
              </TouchableOpacity>
            </LinearGradient>

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
              <Mail size={20} color={colors.textPrimary} />
              <Text style={styles.magicLinkText}>Login with Magic Link</Text>
            </TouchableOpacity>
          </>
        ) : (
          <LinearGradient
            colors={[colors.primaryBlue, colors.accentPurple]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.authButton}
          >
            <TouchableOpacity
              style={styles.authButtonTouchable}
              onPress={handleSignUp}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <>
                  <Text style={styles.authButtonText}>Create Account</Text>
                  <ArrowRight size={20} color="#fff" />
                </>
              )}
            </TouchableOpacity>
          </LinearGradient>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundDark,
    paddingHorizontal: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 40,
  },
  logoBackground: {
    width: 80,
    height: 80,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
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
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 16,
    color: colors.textPrimary,
    fontSize: 16,
  },
  forgotPasswordContainer: {
    alignSelf: 'flex-end',
  },
  forgotPasswordText: {
    color: colors.primaryBlue,
    fontSize: 14,
  },
  footer: {
    marginTop: 'auto',
    marginBottom: 32,
  },
  authButton: {
    borderRadius: 28,
  },
  authButtonTouchable: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  authButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginRight: 8,
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
  },
  magicLinkText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.textPrimary,
    marginLeft: 8,
  },
});