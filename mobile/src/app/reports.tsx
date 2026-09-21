import { type Href, useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuth } from '@/contexts/AuthContext';
import {
  generateReport,
  getKpiSummary,
  getSalesTimeseries,
  type KpiSummary,
  type ReportResponse,
  type SalesTimeSeriesPoint,
} from '@/services/api';

type ApiError = {
  code?: string;
  response?: { status?: number };
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(value);
}

/**
 * Conserve uniquement les indicateurs utiles et les trois derniers mois :
 * le Report Agent reçoit des données réelles, sans lui transmettre toute la série.
 */
function buildReportContext(summary: KpiSummary, series: SalesTimeSeriesPoint[]): string {
  const recentPeriods = series.slice(-3);
  const latest = recentPeriods.at(-1);
  const previous = recentPeriods.at(-2);
  const recentSales = recentPeriods
    .map((point) => `${point.period} : ${formatNumber(point.total_sales)}`)
    .join(' ; ');

  const lines = [
    'Données Business Intelligence réelles du Dashboard :',
    `Ventes totales : ${formatNumber(summary.total_sales)}.`,
    `Profit total : ${formatNumber(summary.total_profit)}.`,
    `Nombre de commandes : ${formatNumber(summary.total_orders)}.`,
  ];

  if (summary.margin_pct !== null) {
    lines.push(`Marge globale : ${formatNumber(summary.margin_pct)} %.`);
  }

  if (recentSales) {
    lines.push(`Ventes des périodes récentes : ${recentSales}.`);
  }

  if (latest && previous && previous.total_sales !== 0) {
    const change = ((latest.total_sales - previous.total_sales) / previous.total_sales) * 100;
    lines.push(
      `Évolution entre ${previous.period} et ${latest.period} : ${formatNumber(change)} %.`
    );
  }

  return lines.join('\n');
}

function getReportsErrorMessage(error: unknown): string {
  const status = (error as ApiError).response?.status;
  const code = (error as ApiError).code;

  if (code === 'ECONNABORTED' || code === 'ETIMEDOUT') {
    return 'La génération du rapport prend trop de temps. Veuillez réessayer.';
  }

  if (status === 401 || status === 403) {
    return 'Votre session a expiré. Veuillez vous reconnecter.';
  }

  if (!status && error instanceof Error) {
    return error.message;
  }

  if (!status) {
    return 'Impossible de contacter le serveur. Vérifiez que FastAPI est démarré.';
  }

  return 'Impossible de générer le rapport. Veuillez réessayer.';
}

export default function ReportsScreen() {
  const router = useRouter();
  const { logout, token } = useAuth();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  async function handleGenerateReport() {
    if (!token) {
      await logout();
      router.replace('/login');
      return;
    }

    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const [summary, series] = await Promise.all([
        getKpiSummary(token),
        getSalesTimeseries(token),
      ]);

      if (series.length === 0) {
        setReport(null);
        setErrorMessage('Aucune donnée de ventes n’est disponible pour générer un rapport.');
        return;
      }

      const context = buildReportContext(summary, series);
      const nextReport = await generateReport(context, token);
      setReport(nextReport);
    } catch (error) {
      const status = (error as ApiError).response?.status;
      setErrorMessage(getReportsErrorMessage(error));

      if (status === 401 || status === 403) {
        await logout();
        router.replace('/login');
      }
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Pressable accessibilityRole="button" onPress={() => router.replace('/home' as Href)}>
          <Text style={styles.backButton}>← Retour à l’accueil</Text>
        </Pressable>

        <View style={styles.heading}>
          <Text style={styles.title}>Rapports BI</Text>
          <Text style={styles.subtitle}>
            Générez une synthèse des indicateurs Business Intelligence actuels.
          </Text>
        </View>

        {errorMessage ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        {report ? (
          <View style={styles.reportCard}>
            <Text style={styles.reportTitle}>{report.title}</Text>

            <Text style={styles.sectionTitle}>Résumé</Text>
            <Text style={styles.summary}>{report.summary}</Text>

            {report.key_points.length > 0 ? (
              <View style={styles.pointsSection}>
                <Text style={styles.sectionTitle}>Points clés</Text>
                {report.key_points.map((point, index) => (
                  <View key={`${point}-${index}`} style={styles.pointRow}>
                    <Text style={styles.bullet}>•</Text>
                    <Text style={styles.pointText}>{point}</Text>
                  </View>
                ))}
              </View>
            ) : null}
          </View>
        ) : (
          <View style={styles.introCard}>
            <Text style={styles.introText}>
              Le rapport sera généré à partir des KPI et des ventes mensuelles réelles du Dashboard.
            </Text>
          </View>
        )}

        {isGenerating ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator color="#2563EB" />
            <Text style={styles.loadingText}>Génération du rapport en cours...</Text>
          </View>
        ) : null}

        <Pressable
          accessibilityRole="button"
          disabled={isGenerating}
          onPress={() => void handleGenerateReport()}
          style={({ pressed }) => [
            styles.generateButton,
            (pressed || isGenerating) && styles.generateButtonPressed,
          ]}>
          {isGenerating ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.generateButtonText}>
              {report ? 'Actualiser le rapport' : 'Générer la synthèse'}
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: '#F8FAFC', flex: 1 },
  container: { gap: 20, padding: 24, paddingBottom: 40 },
  backButton: { color: '#2563EB', fontSize: 15, fontWeight: '600' },
  heading: { gap: 6 },
  title: { color: '#0F172A', fontSize: 32, fontWeight: '700' },
  subtitle: { color: '#475569', fontSize: 16, lineHeight: 24 },
  introCard: { backgroundColor: '#FFFFFF', borderColor: '#DBE3EF', borderRadius: 12, borderWidth: 1, padding: 18 },
  introText: { color: '#475569', fontSize: 16, lineHeight: 24 },
  reportCard: { backgroundColor: '#FFFFFF', borderColor: '#DBE3EF', borderRadius: 12, borderWidth: 1, gap: 12, padding: 18 },
  reportTitle: { color: '#0F172A', fontSize: 22, fontWeight: '700' },
  sectionTitle: { color: '#1E293B', fontSize: 16, fontWeight: '700', marginTop: 4 },
  summary: { color: '#334155', fontSize: 16, lineHeight: 24 },
  pointsSection: { gap: 8 },
  pointRow: { flexDirection: 'row', gap: 8 },
  bullet: { color: '#2563EB', fontSize: 18, lineHeight: 23 },
  pointText: { color: '#334155', flex: 1, fontSize: 16, lineHeight: 23 },
  errorCard: { backgroundColor: '#FEF2F2', borderColor: '#FECACA', borderRadius: 10, borderWidth: 1, padding: 14 },
  errorText: { color: '#B91C1C', fontSize: 14, lineHeight: 20 },
  loadingRow: { alignItems: 'center', flexDirection: 'row', gap: 10, justifyContent: 'center', padding: 4 },
  loadingText: { color: '#475569', fontSize: 14 },
  generateButton: { alignItems: 'center', backgroundColor: '#2563EB', borderRadius: 10, justifyContent: 'center', minHeight: 52 },
  generateButtonPressed: { opacity: 0.72 },
  generateButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
