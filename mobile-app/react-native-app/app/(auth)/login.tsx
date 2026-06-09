import { router } from 'expo-router';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from 'firebase/auth';
import { ref, set, update, serverTimestamp } from 'firebase/database';
import React, { useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { auth, db, hasFirebaseConfig } from '../../lib/firebase';

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

function friendlyAuthError(code: string): string {
  switch (code) {
    case 'auth/invalid-email':
      return 'Invalid email address.';
    case 'auth/user-disabled':
      return 'This account has been disabled.';
    case 'auth/user-not-found':
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password.';
    case 'auth/email-already-in-use':
      return 'An account with this email already exists. Try signing in.';
    case 'auth/weak-password':
      return 'Password is too weak. Use at least 6 characters.';
    case 'auth/too-many-requests':
      return 'Too many attempts. Please try again later.';
    default:
      return `Authentication failed (${code}).`;
  }
}

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [touched, setTouched] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);

  const emailOk = useMemo(() => isValidEmail(email), [email]);
  const passwordOk = useMemo(() => password.trim().length >= 6, [password]);
  const canSubmit = emailOk && passwordOk && !isSubmitting;

  const errorText = useMemo(() => {
    if (authError) return authError;
    if (!touched) return '';
    if (!emailOk) return 'Enter a valid email address.';
    if (!passwordOk) return 'Password must be at least 6 characters.';
    return '';
  }, [touched, emailOk, passwordOk, authError]);

  const onSignIn = async () => {
    setTouched(true);
    setAuthError('');
    if (!emailOk || !passwordOk) return;

    if (!hasFirebaseConfig || !auth) {
      setAuthError('Firebase is not configured. Set EXPO_PUBLIC_FIREBASE_* env vars.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (isSignUp) {
        const cred = await createUserWithEmailAndPassword(auth, email.trim(), password);
        if (db) {
          set(ref(db, `users/${cred.user.uid}`), {
            email: cred.user.email,
            displayName: null,
            createdAt: serverTimestamp(),
            lastLoginAt: serverTimestamp(),
            source: 'mobile',
          }).catch(() => {});
        }
      } else {
        const cred = await signInWithEmailAndPassword(auth, email.trim(), password);
        if (db) {
          update(ref(db, `users/${cred.user.uid}`), {
            lastLoginAt: serverTimestamp(),
          }).catch(() => {});
        }
      }
      router.replace('/(tabs)');
    } catch (e: any) {
      const code = e?.code ?? '';
      setAuthError(friendlyAuthError(code));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.select({ ios: 'padding', android: undefined })}
        style={styles.container}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Sign in</Text>
          <Text style={styles.subtitle}>Log in to continue to Smishing Detection.</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Email</Text>
          <TextInput
            value={email}
            onChangeText={(t) => setEmail(t)}
            onBlur={() => setTouched(true)}
            placeholder="you@example.com"
            placeholderTextColor="#6b7280"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            textContentType="emailAddress"
            style={styles.input}
            returnKeyType="next"
          />

          <Text style={[styles.label, { marginTop: 10 }]}>Password</Text>
          <TextInput
            value={password}
            onChangeText={(t) => setPassword(t)}
            onBlur={() => setTouched(true)}
            placeholder="Your password"
            placeholderTextColor="#6b7280"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            textContentType="password"
            style={styles.input}
            returnKeyType="done"
            onSubmitEditing={onSignIn}
          />

          {!!errorText && <Text style={styles.errorText}>{errorText}</Text>}

          <Pressable
            onPress={onSignIn}
            disabled={!canSubmit}
            style={({ pressed }) => [
              styles.button,
              !canSubmit && styles.buttonDisabled,
              pressed && canSubmit && styles.buttonPressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel={isSignUp ? 'Create account' : 'Sign in'}
          >
            <Text style={styles.buttonText}>
              {isSubmitting
                ? isSignUp ? 'Creating account…' : 'Signing in…'
                : isSignUp ? 'Create account' : 'Sign in'}
            </Text>
          </Pressable>

          <Pressable onPress={() => { setIsSignUp((v) => !v); setAuthError(''); }}>
            <Text style={styles.footerHint}>
              {isSignUp
                ? 'Already have an account? Sign in'
                : "Don't have an account? Create one"}
            </Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0b1220',
  },
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 20,
    gap: 14,
  },
  header: {
    gap: 6,
  },
  title: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: '800',
    letterSpacing: 0.2,
  },
  subtitle: {
    color: '#cbd5e1',
    fontSize: 14,
    lineHeight: 20,
  },
  card: {
    backgroundColor: '#0f1b33',
    borderWidth: 1,
    borderColor: '#1f2a44',
    borderRadius: 14,
    padding: 14,
  },
  label: {
    color: '#e5e7eb',
    fontSize: 13,
    fontWeight: '700',
  },
  input: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#253252',
    backgroundColor: '#0b1220',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 12,
    color: '#ffffff',
    fontSize: 14,
  },
  errorText: {
    marginTop: 10,
    color: '#fbbf24',
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
  },
  button: {
    marginTop: 14,
    backgroundColor: '#2563eb',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonPressed: {
    opacity: 0.9,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.2,
  },
  footerHint: {
    marginTop: 12,
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 18,
  },
});

