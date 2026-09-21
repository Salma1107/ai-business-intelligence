# Démonstration locale — AI Agent for Business Intelligence

Ce guide permet de présenter l'application sur un téléphone avec **Expo Go**.
La démonstration fonctionne entièrement sur le PC : FastAPI, PostgreSQL,
Ollama et le modèle Forecast restent locaux. Le téléphone et le PC doivent
être connectés au même réseau Wi-Fi.

> Ne partagez jamais `backend/.env` ou `mobile/.env`. Ces fichiers contiennent
> votre configuration locale et sont exclus de Git.

## 1. Vérifier l'adresse IPv4 du PC

Dans PowerShell, lancez :

```powershell
ipconfig
```

Dans la section de votre adaptateur Wi-Fi actif, repérez la ligne
`Adresse IPv4`. Elle ressemble à `192.168.x.x`.

Conservez cette adresse pour les étapes suivantes. N'utilisez pas
`127.0.0.1` : cette adresse désigne le téléphone lui-même lorsqu'Expo Go
l'exécute.

## 2. Configurer l'URL de l'API mobile

Depuis le dossier `mobile`, créez le fichier privé seulement s'il n'existe
pas encore :

```powershell
Copy-Item .env.example .env
```

Ouvrez ensuite `mobile/.env` et remplacez la valeur par l'adresse IPv4
trouvée à l'étape précédente :

```env
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
```

Enregistrez le fichier. Si vous le modifiez plus tard, arrêtez et relancez
Expo afin qu'il recharge la variable.

## 3. Vérifier Ollama

Dans un premier terminal PowerShell :

```powershell
cd "C:\Users\Salma SAMIEDDINE\Downloads\AI_BI\AI_BI"
ollama list
```

La liste doit contenir `llama3.1`. Si la commande répond que le service est
déjà en cours d'utilisation sur le port `11434`, c'est normal : ne lancez pas
un second `ollama serve`.

## 4. Démarrer FastAPI

Dans ce même terminal :

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Laissez ce terminal ouvert pendant la démo. Le démarrage attendu comprend :

```text
Uvicorn running on http://0.0.0.0:8000
Application startup complete.
```

Pour une démonstration stable, n'utilisez pas `--reload` : il n'est utile que
pendant le développement.

## 5. Vérifier FastAPI depuis le téléphone

Sur le téléphone, connecté au même Wi-Fi, ouvrez dans le navigateur :

```text
http://192.168.x.x:8000/docs
```

Remplacez `192.168.x.x` par l'adresse IPv4 du PC. La page Swagger doit
s'afficher. Si elle ne s'affiche pas, vérifiez d'abord le Wi-Fi et le pare-feu
Windows (réseau privé, port TCP 8000).

## 6. Démarrer Expo en mode LAN

Dans un deuxième terminal PowerShell :

```powershell
cd "C:\Users\Salma SAMIEDDINE\Downloads\AI_BI\AI_BI\mobile"
npm.cmd run start -- --lan
```

Attendez l'affichage du QR code. Installez Expo Go depuis le magasin
d'applications si nécessaire, puis scannez le QR code depuis Expo Go.

## 7. Parcours de validation de la démo

Dans Expo Go, effectuez successivement :

1. **Login** avec un compte existant ou créez-en un via **Register**.
2. **Home** : vérifiez les accès Assistant BI, Dashboard BI et Rapports.
3. **Dashboard BI** : vérifiez les KPI, la courbe, puis utilisez
   **Actualiser**.
4. **Rapports BI** : vérifiez qu'une synthèse est affichée et que le bouton
   d'actualisation fonctionne.
5. **Assistant BI** : envoyez une question simple, par exemple :
   `Quel est le total des ventes ?`.
6. **Logout** : vérifiez le retour vers Login et l'absence d'accès à Home.

Le Chat peut prendre jusqu'à 130 secondes sur CPU lorsque Ollama génère une
requête SQL ou un rapport. Gardez FastAPI et Ollama actifs durant toute cette
attente.

## Dépannage rapide

- **Impossible de contacter le serveur** : contrôlez l'adresse dans
  `mobile/.env`, redémarrez Expo, puis ouvrez `/docs` depuis le téléphone.
- **`/docs` inaccessible sur le téléphone** : autorisez Python/Uvicorn sur un
  réseau privé dans le pare-feu Windows ou ajoutez une règle entrante TCP sur
  le port 8000.
- **Ollama est lent** : le PC exécute `llama3.1` sur CPU ; attendez la réponse
  et évitez d'envoyer plusieurs questions simultanément.
- **L'adresse IPv4 a changé** : mettez à jour `mobile/.env`, puis redémarrez
  Expo avec la commande de l'étape 6.
