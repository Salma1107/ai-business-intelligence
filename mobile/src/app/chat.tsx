import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { useAuth } from '@/contexts/AuthContext';
import { sendChatMessage } from '@/services/api';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

type ApiError = {
  code?: string;
  response?: {
    status?: number;
  };
};

function getChatErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message === 'Réponse invalide reçue du serveur.') {
    return 'Le serveur a renvoyé une réponse invalide. Veuillez réessayer.';
  }

  const status = (error as ApiError).response?.status;
  const code = (error as ApiError).code;

  if (code === 'ECONNABORTED' || code === 'ETIMEDOUT') {
    return 'L’assistant met trop de temps à répondre. Veuillez réessayer.';
  }

  if (status === 401 || status === 403) {
    return 'Votre session a expiré. Veuillez vous reconnecter.';
  }

  if (!status) {
    return 'Impossible de contacter le serveur. Vérifiez que FastAPI est démarré et que l’URL API est correcte.';
  }

  if (status >= 500) {
    return 'Le serveur a rencontré une erreur. Veuillez réessayer dans un instant.';
  }

  return 'La question n’a pas pu être traitée. Veuillez réessayer.';
}

export default function ChatScreen() {
  const router = useRouter();
  const { logout, token } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  async function handleSend() {
    const normalizedQuestion = question.trim();

    if (!normalizedQuestion) {
      setErrorMessage('Saisissez une question avant de l’envoyer.');
      return;
    }

    if (!token) {
      setErrorMessage('Votre session a expiré. Veuillez vous reconnecter.');
      await logout();
      router.replace('/login');
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: normalizedQuestion,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setQuestion('');
    setErrorMessage(null);
    setIsSending(true);

    try {
      const { answer } = await sendChatMessage(normalizedQuestion, token);

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: answer,
        },
      ]);
    } catch (error) {
      const status = (error as ApiError).response?.status;
      setErrorMessage(getChatErrorMessage(error));

      if (status === 401 || status === 403) {
        await logout();
        router.replace('/login');
      }
    } finally {
      setIsSending(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboardAvoidingView}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Pressable accessibilityRole="button" onPress={() => router.replace('/home')}>
              <Text style={styles.backButton}>← Retour à l’accueil</Text>
            </Pressable>
            <Text style={styles.title}>Assistant BI</Text>
            <Text style={styles.subtitle}>Posez une question sur vos données.</Text>
          </View>

          <ScrollView
            contentContainerStyle={messages.length === 0 ? styles.emptyMessages : styles.messages}
            style={styles.messagesContainer}>
            {messages.length === 0 ? (
              <Text style={styles.emptyText}>Exemple : Quel produit est le plus vendu ?</Text>
            ) : (
              messages.map((message) => (
                <View
                  key={message.id}
                  style={message.role === 'user' ? styles.userMessage : styles.assistantMessage}>
                  <Text style={styles.messageRole}>
                    {message.role === 'user' ? 'Vous' : 'Assistant'}
                  </Text>
                  <Text style={styles.messageContent}>{message.content}</Text>
                </View>
              ))
            )}

            {isSending && (
              <View style={styles.loadingAnswer}>
                <ActivityIndicator color="#2563EB" />
                <Text style={styles.loadingText}>L’assistant prépare sa réponse…</Text>
              </View>
            )}
          </ScrollView>

          <View style={styles.composer}>
            {errorMessage && <Text style={styles.errorMessage}>{errorMessage}</Text>}
            <TextInput
              editable={!isSending}
              multiline
              onChangeText={setQuestion}
              placeholder="Posez votre question..."
              placeholderTextColor="#64748B"
              style={styles.input}
              value={question}
            />
            <Pressable
              accessibilityRole="button"
              disabled={isSending}
              onPress={handleSend}
              style={({ pressed }) => [
                styles.sendButton,
                (pressed || isSending) && styles.sendButtonPressed,
              ]}>
              {isSending ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.sendButtonText}>Envoyer</Text>
              )}
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: '#F8FAFC', flex: 1 },
  keyboardAvoidingView: { flex: 1 },
  container: { flex: 1, padding: 20 },
  header: { gap: 6, marginBottom: 16 },
  backButton: { color: '#2563EB', fontSize: 15, fontWeight: '600', marginBottom: 10 },
  title: { color: '#0F172A', fontSize: 30, fontWeight: '700' },
  subtitle: { color: '#475569', fontSize: 16 },
  messagesContainer: { flex: 1 },
  messages: { gap: 12, paddingBottom: 16 },
  emptyMessages: { alignItems: 'center', flexGrow: 1, justifyContent: 'center', padding: 24 },
  emptyText: { color: '#64748B', fontSize: 16, textAlign: 'center' },
  userMessage: { alignSelf: 'flex-end', backgroundColor: '#DBEAFE', borderRadius: 12, maxWidth: '85%', padding: 14 },
  assistantMessage: { alignSelf: 'flex-start', backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: 12, borderWidth: 1, maxWidth: '85%', padding: 14 },
  messageRole: { color: '#334155', fontSize: 13, fontWeight: '700', marginBottom: 4 },
  messageContent: { color: '#0F172A', fontSize: 16, lineHeight: 23 },
  loadingAnswer: { alignItems: 'center', flexDirection: 'row', gap: 10, padding: 12 },
  loadingText: { color: '#475569', fontSize: 14 },
  composer: { gap: 10, paddingTop: 12 },
  errorMessage: { color: '#B91C1C', fontSize: 14, lineHeight: 20 },
  input: { backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: 10, borderWidth: 1, color: '#0F172A', fontSize: 16, maxHeight: 120, minHeight: 52, padding: 14, textAlignVertical: 'top' },
  sendButton: { alignItems: 'center', backgroundColor: '#2563EB', borderRadius: 10, justifyContent: 'center', minHeight: 52 },
  sendButtonPressed: { opacity: 0.7 },
  sendButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
