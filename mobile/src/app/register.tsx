import { Link, useRouter } from 'expo-router';
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

import { register } from '@/services/api';

type ApiError = {
  response?: {
    status?: number;
    data?: {
      detail?: unknown;
    };
  };
};

function getRegisterErrorMessage(error: unknown): string {
  const apiError = error as ApiError;
  const status = apiError.response?.status;
  const detail = apiError.response?.data?.detail;

  if (status === 400 && typeof detail === 'string') {
    return detail;
  }

  if (status === 422) {
    return 'Les informations saisies ne sont pas valides.';
  }

  if (!status) {
    return 'Impossible de contacter le serveur. Vérifiez que FastAPI est démarré et que l’URL API est correcte.';
  }

  return 'Une erreur est survenue lors de la création du compte. Veuillez réessayer.';
}

export default function RegisterScreen() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirmation, setPasswordConfirmation] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleRegister() {
    const normalizedFullName = fullName.trim();
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedFullName) {
      setErrorMessage('Saisissez votre nom complet.');
      return;
    }

    if (!normalizedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setErrorMessage('Saisissez une adresse email valide.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Le mot de passe doit contenir au moins 8 caractères.');
      return;
    }

    if (password !== passwordConfirmation) {
      setErrorMessage('Les deux mots de passe ne correspondent pas.');
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      const response = await register({
        full_name: normalizedFullName,
        email: normalizedEmail,
        password,
      });

      setSuccessMessage(response.message);
      setPassword('');
      setPasswordConfirmation('');
    } catch (error) {
      setErrorMessage(getRegisterErrorMessage(error));
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
            <Text style={styles.title}>Créer un compte</Text>
            <Text style={styles.subtitle}>Commencez à interroger vos données Business Intelligence.</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.field}>
              <Text style={styles.label}>Nom complet</Text>
              <TextInput
                autoComplete="name"
                onChangeText={setFullName}
                placeholder="Votre nom complet"
                placeholderTextColor="#6B7280"
                style={styles.input}
                value={fullName}
              />
            </View>

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
                autoComplete="new-password"
                onChangeText={setPassword}
                placeholder="Au moins 8 caractères"
                placeholderTextColor="#6B7280"
                secureTextEntry
                style={styles.input}
                value={password}
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Confirmer le mot de passe</Text>
              <TextInput
                autoComplete="new-password"
                onChangeText={setPasswordConfirmation}
                placeholder="Répétez votre mot de passe"
                placeholderTextColor="#6B7280"
                secureTextEntry
                style={styles.input}
                value={passwordConfirmation}
              />
            </View>

            {errorMessage && <Text style={styles.errorMessage}>{errorMessage}</Text>}
            {successMessage && <Text style={styles.successMessage}>{successMessage}</Text>}

            <Pressable
              accessibilityRole="button"
              disabled={isSubmitting}
              onPress={handleRegister}
              style={({ pressed }) => [
                styles.submitButton,
                (pressed || isSubmitting) && styles.submitButtonPressed,
              ]}>
              {isSubmitting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.submitButtonText}>Créer un compte</Text>
              )}
            </Pressable>

            {successMessage && (
              <Pressable onPress={() => router.replace('/login')} style={styles.loginButton}>
                <Text style={styles.loginButtonText}>Se connecter</Text>
              </Pressable>
            )}
          </View>

          <View style={styles.loginPrompt}>
            <Text style={styles.loginText}>Déjà un compte ?</Text>
            <Link href="/login" style={styles.loginLink}>
              Se connecter
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
    gap: 32,
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
    gap: 16,
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
  successMessage: {
    color: '#15803D',
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
  loginButton: {
    alignItems: 'center',
    borderColor: '#2563EB',
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 52,
  },
  loginButtonText: {
    color: '#2563EB',
    fontSize: 16,
    fontWeight: '700',
  },
  loginPrompt: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
    justifyContent: 'center',
  },
  loginText: {
    color: '#475569',
    fontSize: 15,
  },
  loginLink: {
    color: '#2563EB',
    fontSize: 15,
    fontWeight: '700',
  },
});
