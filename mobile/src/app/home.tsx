import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, SafeAreaView, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/contexts/AuthContext';

export default function HomeScreen() {
  const { logout } = useAuth();
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleLogout() {
    setIsLoggingOut(true);

    try {
      await logout();
    } finally {
      router.replace('/login');
      setIsLoggingOut(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.content}>
          <Text style={styles.title}>AI Agent BI</Text>
          <Text style={styles.welcome}>Bienvenue</Text>
          <Text style={styles.description}>
            Vous êtes connecté à votre assistant Business Intelligence.
          </Text>

          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/chat' as Href)}
            style={({ pressed }) => [styles.assistantButton, pressed && styles.assistantButtonPressed]}>
            <Text style={styles.assistantButtonText}>Accéder à l’assistant</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/dashboard' as Href)}
            style={({ pressed }) => [styles.dashboardButton, pressed && styles.dashboardButtonPressed]}>
            <Text style={styles.dashboardButtonText}>Voir le Dashboard</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/reports' as Href)}
            style={({ pressed }) => [styles.reportsButton, pressed && styles.reportsButtonPressed]}>
            <Text style={styles.reportsButtonText}>Rapports BI</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            disabled={isLoggingOut}
            onPress={handleLogout}
            style={({ pressed }) => [
              styles.logoutButton,
              (pressed || isLoggingOut) && styles.logoutButtonPressed,
            ]}>
            {isLoggingOut ? (
              <ActivityIndicator color="#B91C1C" />
            ) : (
              <Text style={styles.logoutButtonText}>Se déconnecter</Text>
            )}
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: '#F8FAFC',
    flex: 1,
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  content: {
    gap: 20,
  },
  title: {
    color: '#0F172A',
    fontSize: 34,
    fontWeight: '700',
  },
  welcome: {
    color: '#1E293B',
    fontSize: 24,
    fontWeight: '600',
  },
  description: {
    color: '#475569',
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 12,
  },
  assistantButton: {
    alignItems: 'center',
    backgroundColor: '#2563EB',
    borderRadius: 10,
    justifyContent: 'center',
    minHeight: 52,
  },
  assistantButtonPressed: {
    opacity: 0.75,
  },
  assistantButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  dashboardButton: {
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderColor: '#2563EB',
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 52,
  },
  dashboardButtonPressed: {
    opacity: 0.7,
  },
  dashboardButtonText: {
    color: '#2563EB',
    fontSize: 16,
    fontWeight: '700',
  },
  reportsButton: {
    alignItems: 'center',
    backgroundColor: '#EFF6FF',
    borderRadius: 10,
    justifyContent: 'center',
    minHeight: 52,
  },
  reportsButtonPressed: {
    opacity: 0.7,
  },
  reportsButtonText: {
    color: '#1D4ED8',
    fontSize: 16,
    fontWeight: '700',
  },
  logoutButton: {
    alignItems: 'center',
    borderColor: '#B91C1C',
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 52,
  },
  logoutButtonPressed: {
    opacity: 0.65,
  },
  logoutButtonText: {
    color: '#B91C1C',
    fontSize: 16,
    fontWeight: '700',
  },
});
