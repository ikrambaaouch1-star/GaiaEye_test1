# Documentation Technique : GaiaEye - Plateforme d'Intelligence Satellitaire

## 🌍 Présentation du Projet
**GaiaEye** est une plateforme avancée de surveillance et d'analyse géospatiale. Elle combine la puissance de **Google Earth Engine (GEE)** pour le traitement massif de données satellite avec l'intelligence artificielle locale (**Ollama**) pour fournir des analyses prédictives et des recommandations agronomiques précises.

---

## 🏗️ Architecture Globale
Le projet suit une architecture client-serveur moderne :
*   **Frontend** : Interface utilisateur réactive basée sur Leaflet.js pour la cartographie.
*   **Backend** : Serveur Flask (Python) agissant comme passerelle entre l'utilisateur, Google Earth Engine et les services d'IA.

---

## 💻 Composants Frontend (`/frontend`)

### 1. `index.html`
Structure de l'application. Elle comprend :
*   Un conteneur de carte plein écran.
*   Une barre latérale de navigation pour sélectionner les indicateurs (Végétation, Eau, Urbain, Climat, Terrain, Radar).
*   Des panneaux de contrôle pour le temps (curseur temporel).
*   Deux tableaux de bord interactifs : **Tableau de Bord Agricole** et **Analyses IA Avancées**.

### 2. `style.css`
Design premium utilisant :
*   Un thème sombre élégant avec **glassmorphism** (effets de flou translucide).
*   Des animations fluides pour les transitions de menus et les indicateurs de chargement.
*   Une mise en page entièrement responsive.

### 3. `app.js` (Logique Métier & Flux)
*   **Pipeline de Données** : Gère le cycle de vie d'une requête, de l'événement de dessin (`L.Draw.Event.CREATED`) à l'obtention de l'ID de carte GEE.
*   **Visualisation Dynamique** : Met à jour les couches de tuiles (`L.tileLayer`) sans recharger la page, offrant une expérience fluide.
*   **Orchestration des Tableaux de Bord** : 
    *   **Dashboard Agricole** : Agrégation de données statistiques pour le rendement et la finance.
    *   **Advanced AI Dashboard** : Communication avec la couche de raisonnement IA pour afficher les rapports complexes et les alertes.

---

## 🔥 Focus : Vision AI Layer (Couche d'Intelligence)

La **Vision AI Layer** de GaiaEye n'est pas une simple analyse d'image ; c'est un système de vision assistée par ordinateur multi-niveaux qui transforme les rayonnements électromagnétiques en connaissances exploitables.

### 1. Vision Multi-Spectrale (Le "Regard" Satellite)
Contrairement à l'œil humain limité au RVB, GaiaEye "voit" dans des spectres invisibles :
*   **Proche Infrarouge (NIR)** : Utilisé pour détecter la structure cellulaire des plantes (vitalité).
*   **Infrarouge à Ondes Courtes (SWIR)** : Permet de voir à travers la brume et de mesurer l'humidité du sol.
*   **Radar (SAR)** : Pénètre les nuages pour détecter l'eau de surface et les structures physiques même en pleine tempête.

### 2. Analytical AI (Traitement du Signal)
C'est ici que les pixels deviennent des chiffres. L'algorithme applique des formules de biophysique :
*   **Extraction de Caractéristiques** : Transformation des bandes spectrales en indices (NDVI, NDWI, etc.).
*   **Spatial Intelligence (Segmentation K-Means)** : L'IA regroupe dynamiquement les pixels similaires pour identifier des zones de gestion différenciées (ZAE). Elle distingue automatiquement un secteur sain d'un secteur stressé sans intervention humaine.

### 3. Cognitive AI Layer (LLM Reasoning)
C'est le "cerveau" qui interprète la vision. Il utilise **Ollama + Qwen 2.5** pour :
*   **Synthèse Narrative** : Lire les milliers de points de données et les transformer en un rapport structuré.
*   **Détection d'Alertes Prioritaires** : Analyser les dépassements de seuils (ex: Stress Hydrique > 70%) et les traduire en urgences opérationnelles.
*   **Recommandations Contextuelles** : L'IA ne dit pas juste "NDVI bas", elle dit "Appliquez une irrigation de 10mm sous 24h pour sauver la récolte".

---

## 🔬 Logique Scientifique et Algorithmique

### 1. Masquage Nuageux et Précision
Pour garantir la fiabilité des données Sentinel-2, nous utilisons la bande **QA60** :
*   Les pixels identifiés comme "opaque clouds" ou "cirrus" sont systématiquement filtrés.
*   Cela permet d'extraire des statistiques uniquement sur le sol nu ou la végétation réelle, évitant les fausses baisses de vitalité dues aux nuages.

### 2. Détection d'Anomalies Spatiales (Z-Score)
Le moteur d'analyse utilise la méthode statistique du **Z-Score** pour identifier les "pixels suspects" :
*   Tout point s'écartant de plus de 2 écarts-types de la moyenne locale est marqué comme anomalie.
*   Cela permet de détecter précocement des micro-foyers de maladies ou des pannes d'irrigation très localisées.

### 3. Modélisation de la Biomasse (Proxy LAI)
Le LAI (Leaf Area Index) est estimé par une transformation semi-empirique des indices de réflectance. Cela permet d'estimer le volume total de feuilles par mètre carré, une donnée cruciale pour le calcul du rendement final.

---

## 🎨 Philosophie de Design (UI/UX)
Le design de GaiaEye repose sur trois piliers :
*   **Immersion** : Utilisation du mode sombre pour faire ressortir les couleurs vives des cartes thermiques et végétales.
*   **Glassmorphism** : Utilisation d'effets de flou et de transparence (`backdrop-filter: blur`) pour les panneaux d'information, permettant de garder un œil sur la carte même pendant la lecture des rapports.
*   **Hiérarchie Cognitive** : Les informations sont classées par urgence via des codes couleurs universels (Vert: Santé, Jaune: Alerte, Rouge: Critique).

---

## 🛡️ Sécurité et Confidentialité
*   **Local-First AI** : Le choix d'**Ollama** garantit que les données d'analyse (coordonnées, statistiques privées) ne quittent jamais votre infrastructure locale pour être traitées par un cloud tiers.
*   **Authentification API** : Utilisation des jetons OIDC de Google pour sécuriser l'accès aux données satellite via des rôles de service (`Service Accounts`).

---

## ⚙️ Détail des Services Backend

### 1. `app.py` (Point d'entrée)
Le cœur du système qui expose les API REST :
*   `/api/analyze` : Retourne l'URL des tuiles GEE pour un indicateur spécifique.
*   `/api/dashboard_stats` : Fournit les métriques agricoles (rendement, coûts, risques).
*   `/api/advanced_analysis` : Orchestre l'analyse complète (Scores + Segmentation + IA).
*   `/api/ai_status` : Vérifie la disponibilité du service Ollama.

### 2. `gee_service.py` (Moteur de Données & Calculs)
*   **Initialisation** : Connexion sécurisée via `ee.Initialize()`.
*   **Générateur de Couches** : Fonction `get_indicator_layer` qui sélectionne dynamiquement le satellite approprié (Sentinel, MODIS, etc.).
*   **Moteur d'Analyse Spatiale** : Utilise `reduceRegion()` sur les serveurs Google pour extraire des statistiques (moyenne, min/max) sur des millions de pixels en quelques secondes.

### 3. `analytics_engine.py` (Intelligence Statistique)
*   **Moteur de Scores** : Algorithme propriétaire qui pondère les indices (ex: Santé = 50% NDVI + 30% EVI + 20% SAVI).
*   **Clustering Spatial** : Implémentation de `sklearn.cluster.KMeans` pour la segmentation automatique du terrain.
*   **Normalisation** : Transformation des données physiques brutes en scores de 0 à 100 compréhensibles par l'utilisateur.

### 4. `llm_service.py` (Couche de Raisonnement GenAI)
*   **Prompt Engineering** : Templates sophistiqués envoyés à Ollama pour guider le raisonnement vers une expertise agronomique.
*   **Analyse de Tendances** : L'IA compare les données actuelles aux données historiques pour détecter des signes de dégradation précoce.
*   **Multilingue** : Génération native de rapports détaillés en français technique.

---

## 🔄 Interactions et Flux de Données

1.  **Saisie Utilisateur** : L'utilisateur dessine un rectangle sur la carte et sélectionne un indicateur (ex: NDVI).
2.  **Requête GEE** : Le frontend envoie les coordonnées au backend. `gee_service.py` demande à Google Earth Engine de calculer l'indice sur les serveurs Google.
3.  **Visualisation** : GEE génère un `mapid`. Le serveur Flask retourne une URL de tuile au format `{z}/{x}/{y}`. Leaflet affiche alors la couche satellite colorée sur la carte.
4.  **Analyse Approfondie** : 
    *   L'utilisateur clique sur "Lancer l'Analyse IA".
    *   `gee_service` extrait les statistiques spatiales.
    *   `analytics_engine` génère les scores et les zones.
    *   `llm_service` rédige le rapport textuel.
5.  **Restitution** : Le frontend affiche le rapport complet, les graphiques de scores et les alertes détectées.

---

## 🛠️ Utilitaires Racine

### 1. `authenticate.bat`
Un script automatisé pour simplifier le processus d'authentification **Google Earth Engine**.
*   Il lance la commande Python `ee.Authenticate()`.
*   Il guide l'utilisateur pour l'obtention et le collage du jeton d'accès nécessaire à l'utilisation des serveurs Google.

### 2. `requirements.txt`
Liste les dépendances Python essentielles :
*   `flask` & `flask-cors` : Serveur web et gestion des politiques d'accès.
*   `earthengine-api` : Bibliothèque officielle pour interagir avec GEE.
*   *Note: `numpy`, `scipy` et `scikit-learn` sont également nécessaires pour le moteur d'analyse.*

---

## 🚀 Installation et Démarrage Rapide

1.  **Installation des dépendances** :
    ```bash
    pip install flask flask-cors earthengine-api numpy scipy scikit-learn requests
    ```
2.  **Authentification GEE** :
    Exécutez `authenticate.bat` et suivez les instructions.
3.  **Lancement du serveur** :
    ```bash
    python backend/app.py
    ```
4.  **Accès à l'interface** :
    Ouvrez `frontend/index.html` dans un navigateur moderne (ou accédez via `http://127.0.0.1:5000` si configuré pour servir le statique).

---

## ❓ Dépannage (Troubleshooting)

| Problème | Cause Probable | Solution |
| :--- | :--- | :--- |
| **Erreur d'Initialisation GEE** | Jeton d'authentification expiré ou absent. | Lancer `authenticate.bat` et coller le nouveau jeton. |
| **IA en mode Fallback** | Ollama n'est pas lancé ou modèle manquant. | Lancer Ollama et taper `ollama run qwen2.5:7b`. |
| **Carte Blanche/Vide** | Coordonnées invalides ou zone sans images S2. | Vérifier la date sélectionnée (certaines zones ont des passages satellite moins fréquents). |
| **Lenteur d'Analyse** | Trop grande surface (ROI) sélectionnée. | Dessiner des rectangles plus petits pour des calculs plus rapides. |

---

*Documentation mise à jour le 31 Décembre 2025.*

---

## 🛠️ Stack Technique
*   **Langages** : Python 3.10+, JavaScript (ES6+), HTML5, CSS3.
*   **Frameworks Web** : Flask (Backend), Vanilla JS (Frontend).
*   **Bibliothèques Clés** :
    *   **Cartographie** : Leaflet.js, Leaflet-Draw.
    **Traitement de données** : Google Earth Engine API, NumPy, SciPy, Scikit-learn.
    *   **IA** : Ollama (Qwen2.5-7B/14B).
    *   **Utilitaires** : Requests (API), Flask-CORS.

---

## ⚙️ Configuration Requise
*   **Python** : `pip install -r requirements.txt` (flask, flask-cors, earthengine-api, numpy, scipy, scikit-learn).
*   **Google Earth Engine** : Un compte actif et un projet configuré dans `gee_service.py`.
*   **Ollama (Optionnel pour l'IA)** : Doit être installé et exécuter le modèle spécifié.
