import { Link, type Href } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { useAuth } from '@/contexts/AuthContext';

type ApiError = {
  response?: {
    status?: number;
  };
};

function getLoginErrorMessage(error: unknown): string {
  const status = (error as ApiError).response?.status;

  if (status === 401) {
    return 'Email ou mot de passe incorrect.';
  }

  if (!status) {
    return 'Impossible de contacter le serveur. Vérifiez que FastAPI est démarré et que l’URL API est correcte.';
  }

  return 'Une erreur est survenue. Veuillez réessayer.';
}

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleLogin() {
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setErrorMessage('Saisissez une adresse email valide.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Le mot de passe doit contenir au moins 8 caractères.');
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({ email: normalizedEmail, password });
    } catch (error) {
      setErrorMessage(getLoginErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.keyboardAvoidingView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.container}>
          <View style={styles.heading}>
            <Text style={styles.title}>AI Agent BI</Text>
            <Text style={styles.subtitle}>Connectez-vous pour interroger vos données.</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.field}>
              <Text style={styles.label}>Email</Text>
              <TextInput
                autoCapitalize="none"
                autoComplete="email"
                keyboardType="email-address"
                onChangeText={setEmail}
                placeholder="vous@exemple.com"
                placeholderTextColor="#6B7280"
                style={styles.input}
                value={email}
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Mot de passe</Text>
              <TextInput
                autoComplete="current-password"
                onChangeText={setPassword}
                placeholder="Votre mot de passe"
                placeholderTextColor="#6B7280"
                secureTextEntry
                style={styles.input}
                value={password}
              />
            </View>

            {errorMessage && <Text style={styles.errorMessage}>{errorMessage}</Text>}

            <Pressable
              accessibilityRole="button"
              disabled={isSubmitting}
              onPress={handleLogin}
              style={({ pressed }) => [
                styles.submitButton,
                (pressed || isSubmitting) && styles.submitButtonPressed,
              ]}>
              {isSubmitting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.submitButtonText}>Se connecter</Text>
              )}
            </Pressable>
          </View>

          <View style={styles.registerPrompt}>
            <Text style={styles.registerText}>Pas encore de compte ?</Text>
            <Link href={'/register' as Href} style={styles.registerLink}>
              S’inscrire
            </Link>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    gap: 40,
  },
  heading: {
    gap: 8,
  },
  title: {
    color: '#0F172A',
    fontSize: 34,
    fontWeight: '700',
  },
  subtitle: {
    color: '#475569',
    fontSize: 16,
    lineHeight: 24,
  },
  form: {
    gap: 20,
  },
  field: {
    gap: 8,
  },
  label: {
    color: '#1E293B',
    fontSize: 15,
    fontWeight: '600',
  },
  input: {
    borderColor: '#CBD5E1',
    borderRadius: 10,
    borderWidth: 1,
    color: '#0F172A',
    fontSize: 16,
    minHeight: 52,
    paddingHorizontal: 14,
  },
  errorMessage: {
    color: '#B91C1C',
    fontSize: 14,
    lineHeight: 20,
  },
  submitButton: {
    alignItems: 'center',
    backgroundColor: '#2563EB',
    borderRadius: 10,
    justifyContent: 'center',
    minHeight: 52,
  },
  submitButtonPressed: {
    opacity: 0.75,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  registerPrompt: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
    justifyContent: 'center',
  },
  registerText: {
    color: '#475569',
    fontSize: 15,
  },
  registerLink: {
    color: '#2563EB',
    fontSize: 15,
    fontWeight: '700',
  },
});
