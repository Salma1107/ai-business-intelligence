const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL;

if (!configuredApiUrl) {
  throw new Error(
    "L'URL de l'API est manquante. Créez un fichier .env à partir de .env.example et définissez EXPO_PUBLIC_API_URL."
  );
}

/** URL FastAPI sans slash final, partagée par tous les appels réseau. */
export const API_BASE_URL = configuredApiUrl.replace(/\/+$/, '');
