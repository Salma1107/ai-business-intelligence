import { type Href, useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { SalesLineChart } from '@/components/dashboard/SalesLineChart';
import { useAuth } from '@/contexts/AuthContext';
import {
  getKpiSummary,
  getSalesTimeseries,
  type KpiSummary,
  type SalesTimeSeriesPoint,
} from '@/services/api';

type ApiError = {
  response?: { status?: number };
};

function formatNumber(value: number | null): string {
  if (value === null) {
    return '—';
  }

  return new Intl.NumberFormat('fr-FR', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  }).format(value);
}

function getDashboardErrorMessage(error: unknown): string {
  const status = (error as ApiError).response?.status;

  if (status === 401 || status === 403) {
    return 'Votre session a expiré. Veuillez vous reconnecter.';
  }

  if (!status) {
    return 'Impossible de contacter le serveur. Vérifiez que FastAPI est démarré.';
  }

  return 'Impossible de charger les données du Dashboard. Veuillez réessayer.';
}

export default function DashboardScreen() {
  const router = useRouter();
  const { logout, token } = useAuth();
  const [summary, setSummary] = useState<KpiSummary | null>(null);
  const [series, setSeries] = useState<SalesTimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadDashboard = useCallback(
    async (isRefresh = false) => {
      if (!token) {
        await logout();
        router.replace('/login');
        return;
      }

      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setErrorMessage(null);

      try {
        const [nextSummary, nextSeries] = await Promise.all([
          getKpiSummary(token),
          getSalesTimeseries(token),
        ]);
        setSummary(nextSummary);
        setSeries(nextSeries);
      } catch (error) {
        const status = (error as ApiError).response?.status;
        setErrorMessage(getDashboardErrorMessage(error));

        if (status === 401 || status === 403) {
          await logout();
          router.replace('/login');
        }
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [logout, router, token]
  );

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.centeredState}>
          <ActivityIndicator color="#2563EB" size="large" />
          <Text style={styles.stateText}>Chargement des données Business Intelligence…</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Pressable accessibilityRole="button" onPress={() => router.replace('/home' as Href)}>
          <Text style={styles.backButton}>← Retour à l’accueil</Text>
        </Pressable>

        <View style={styles.heading}>
          <Text style={styles.title}>Dashboard BI</Text>
          <Text style={styles.subtitle}>Vue d’ensemble de vos données.</Text>
        </View>

        {errorMessage ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorMessage}>{errorMessage}</Text>
          </View>
        ) : null}

        {summary ? (
          <View style={styles.kpiRow}>
            <View style={styles.kpiCard}>
              <Text style={styles.kpiLabel}>Ventes totales</Text>
              <Text style={styles.kpiValue}>{formatNumber(summary.total_sales)}</Text>
            </View>
            <View style={styles.kpiCard}>
              <Text style={styles.kpiLabel}>Profit total</Text>
              <Text style={styles.kpiValue}>{formatNumber(summary.total_profit)}</Text>
            </View>
          </View>
        ) : null}

        {series.length > 0 ? (
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>Évolution des ventes</Text>
            <Text style={styles.chartDescription}>Ventes mensuelles</Text>
            <SalesLineChart series={series} />
          </View>
        ) : (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>Aucune donnée de ventes n’est disponible pour le moment.</Text>
          </View>
        )}

        <Pressable
          accessibilityRole="button"
          disabled={refreshing}
          onPress={() => void loadDashboard(true)}
          style={({ pressed }) => [styles.refreshButton, (pressed || refreshing) && styles.refreshButtonPressed]}>
          {refreshing ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.refreshButtonText}>Actualiser</Text>}
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: '#F8FAFC', flex: 1 },
  container: { gap: 20, padding: 24, paddingBottom: 40 },
  centeredState: { alignItems: 'center', flex: 1, gap: 14, justifyContent: 'center', padding: 24 },
  stateText: { color: '#475569', fontSize: 16, textAlign: 'center' },
  backButton: { color: '#2563EB', fontSize: 15, fontWeight: '600' },
  heading: { gap: 6 },
  title: { color: '#0F172A', fontSize: 32, fontWeight: '700' },
  subtitle: { color: '#475569', fontSize: 16 },
  kpiRow: { flexDirection: 'row', gap: 12 },
  kpiCard: { backgroundColor: '#FFFFFF', borderColor: '#DBE3EF', borderRadius: 12, borderWidth: 1, flex: 1, gap: 8, minHeight: 116, padding: 16 },
  kpiLabel: { color: '#475569', fontSize: 14, fontWeight: '600' },
  kpiValue: { color: '#0F172A', fontSize: 22, fontWeight: '700' },
  chartCard: { backgroundColor: '#FFFFFF', borderColor: '#DBE3EF', borderRadius: 12, borderWidth: 1, overflow: 'hidden', padding: 16 },
  chartTitle: { color: '#0F172A', fontSize: 19, fontWeight: '700' },
  chartDescription: { color: '#64748B', fontSize: 14, marginBottom: 8, marginTop: 4 },
  errorCard: { backgroundColor: '#FEF2F2', borderColor: '#FECACA', borderRadius: 10, borderWidth: 1, padding: 14 },
  errorMessage: { color: '#B91C1C', fontSize: 14, lineHeight: 20 },
  emptyCard: { alignItems: 'center', backgroundColor: '#FFFFFF', borderColor: '#DBE3EF', borderRadius: 12, borderWidth: 1, minHeight: 150, justifyContent: 'center', padding: 24 },
  emptyText: { color: '#64748B', fontSize: 16, textAlign: 'center' },
  refreshButton: { alignItems: 'center', backgroundColor: '#2563EB', borderRadius: 10, justifyContent: 'center', minHeight: 52 },
  refreshButtonPressed: { opacity: 0.72 },
  refreshButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
