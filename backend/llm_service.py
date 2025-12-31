"""
GaiaEye LLM Reasoning Service

This module provides AI-powered interpretation and recommendations
using a local LLM (Ollama + Qwen).

Key Features:
- Intelligent interpretation of satellite data
- Actionable recommendations generation
- Alert detection and prioritization
- Zone comparison analysis
- Natural language insights
- Terroir Audit (Parcel vs Grand Cru)
"""

import json
import requests
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"  # Can be changed to qwen2.5:14b for better quality

# ==========================================
# CORE LLM FUNCTIONS
# ==========================================

def generate_insights(analysis_data: dict) -> str:
    """
    Generate human-readable interpretation of analysis data
    
    Args:
        analysis_data: Dictionary with scores, trends, and metrics
        
    Returns:
        Natural language insight string
    """
    prompt = create_insight_prompt(analysis_data)
    
    try:
        response = query_llm(prompt, max_tokens=300)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return generate_fallback_insight(analysis_data)

def generate_detailed_report(analysis_data: dict) -> str:
    """
    Generate comprehensive, detailed professional report
    
    This function produces a long, exhaustive analysis report similar to
    a scientific or professional document, covering all aspects of the
    satellite data analysis.
    
    Args:
        analysis_data: Complete analysis data including scores, zones, trends
        
    Returns:
        Long, detailed professional report in French
    """
    prompt = create_detailed_report_prompt(analysis_data)
    
    try:
        response = query_llm(prompt, max_tokens=2000, temperature=0.6)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating detailed report: {e}")
        return generate_fallback_detailed_report(analysis_data)

def generate_recommendations(analysis_data: dict) -> List[str]:
    """
    Generate actionable recommendations based on data
    
    Returns:
        List of specific, actionable recommendations
    """
    prompt = create_recommendations_prompt(analysis_data)
    
    try:
        response = query_llm(prompt, max_tokens=400)
        # Parse JSON response
        recommendations = parse_json_response(response, 'recommendations')
        return recommendations if recommendations else generate_fallback_recommendations(analysis_data)
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return generate_fallback_recommendations(analysis_data)

def generate_terroir_audit(parcel_data: dict, match_results: List[dict]) -> str:
    """
    Generate a scientific audit comparing the parcel to the closest Grand Cru reference.
    """
    prompt = create_terroir_audit_prompt(parcel_data, match_results)
    
    try:
        response = query_llm(prompt, max_tokens=1000, temperature=0.5)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating terroir audit: {e}")
        return "Service d'audit indisponible pour le moment."

def detect_alerts(analysis_data: dict) -> List[dict]:
    """
    Detect critical issues requiring immediate attention
    
    Returns:
        List of alert dictionaries with severity, type, and message
    """
    alerts = []
    scores = analysis_data.get('scores', {})
    
    # Critical thresholds
    if scores.get('water_stress', 0) > 70:
        alerts.append({
            'severity': 'high',
            'type': 'water_stress',
            'message': f"Stress hydrique critique détecté ({scores['water_stress']}/100)",
            'action_required': True
        })
    
    if scores.get('vegetation_health', 100) < 30:
        alerts.append({
            'severity': 'high',
            'type': 'vegetation_health',
            'message': f"Santé de la végétation très faible ({scores['vegetation_health']}/100)",
            'action_required': True
        })
    
    if scores.get('environmental_risk', 0) > 70:
        alerts.append({
            'severity': 'medium',
            'type': 'environmental_risk',
            'message': f"Risque environnemental élevé ({scores['environmental_risk']}/100)",
            'action_required': True
        })
    
    if scores.get('productivity', 100) < 40:
        alerts.append({
            'severity': 'medium',
            'type': 'productivity',
            'message': f"Productivité attendue faible ({scores['productivity']}/100)",
            'action_required': False
        })
    
    # Trend-based alerts
    trends = analysis_data.get('trend_analysis', {})
    if trends.get('ndvi_trend') == 'decreasing' and abs(trends.get('ndvi_change_percent', 0)) > 10:
        alerts.append({
            'severity': 'medium',
            'type': 'declining_health',
            'message': f"NDVI en baisse de {abs(trends['ndvi_change_percent'])}%",
            'action_required': False
        })
    
    return alerts

def compare_zones(zone_a: dict, zone_b: dict) -> dict:
    """
    Comparative analysis between two zones
    
    Returns:
        Comparison summary with key differences
    """
    comparison = {
        'zone_a_id': zone_a.get('zone_id', 'A'),
        'zone_b_id': zone_b.get('zone_id', 'B'),
        'differences': {}
    }
    
    # Compare key metrics
    metrics = ['avg_ndvi', 'health_status', 'risk_level', 'area_percent']
    
    for metric in metrics:
        val_a = zone_a.get(metric)
        val_b = zone_b.get(metric)
        
        if val_a is not None and val_b is not None:
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                diff = val_a - val_b
                comparison['differences'][metric] = {
                    'zone_a': val_a,
                    'zone_b': val_b,
                    'difference': round(diff, 3),
                    'better_zone': 'A' if val_a > val_b else 'B' if val_b > val_a else 'Equal'
                }
            else:
                comparison['differences'][metric] = {
                    'zone_a': val_a,
                    'zone_b': val_b,
                    'same': val_a == val_b
                }
    
    # Generate summary
    if zone_a.get('avg_ndvi', 0) > zone_b.get('avg_ndvi', 0):
        comparison['summary'] = f"Zone {zone_a.get('zone_id')} présente une meilleure santé végétale"
    else:
        comparison['summary'] = f"Zone {zone_b.get('zone_id')} présente une meilleure santé végétale"
    
    return comparison

# ==========================================
# PROMPT TEMPLATES
# ==========================================

def create_insight_prompt(data: dict) -> str:
    """Create prompt for insight generation"""
    scores = data.get('scores', {})
    trends = data.get('trend_analysis', {})
    
    prompt = f"""You are an expert satellite analyst and agronomist. Analyze this agricultural zone data and provide a clear, concise interpretation in French.

Data:
- Vegetation Health Score: {scores.get('vegetation_health', 'N/A')}/100
- Water Stress Score: {scores.get('water_stress', 'N/A')}/100
- Productivity Score: {scores.get('productivity', 'N/A')}/100
- Environmental Risk Score: {scores.get('environmental_risk', 'N/A')}/100
- Global Sustainability Score: {scores.get('sustainability', 'N/A')}/100
- NDVI Trend: {trends.get('ndvi_trend', 'N/A')} ({trends.get('change_percent', 0)}%)

Provide a 2-3 sentence interpretation that:
1. Summarizes the overall health status
2. Highlights the most important finding
3. Mentions any concerning trends

Response (French, concise):"""
    
    return prompt

def create_recommendations_prompt(data: dict) -> str:
    """Create prompt for recommendations generation"""
    scores = data.get('scores', {})
    alerts = data.get('alerts', [])
    
    prompt = f"""You are an agricultural consultant. Based on this satellite analysis, provide 3-5 specific, actionable recommendations in French.

Scores:
- Vegetation Health: {scores.get('vegetation_health', 'N/A')}/100
- Water Stress: {scores.get('water_stress', 'N/A')}/100
- Productivity: {scores.get('productivity', 'N/A')}/100
- Risk: {scores.get('environmental_risk', 'N/A')}/100

Active Alerts: {len(alerts)}

Provide recommendations as a JSON array. Each recommendation should be:
- Specific and actionable
- Based on the data
- Prioritized by importance

Format:
{{"recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]}}

Response (JSON only):"""
    
    return prompt

def create_detailed_report_prompt(data: dict) -> str:
    """Create comprehensive prompt for detailed professional report"""
    scores = data.get('scores', {})
    raw_indices = data.get('raw_indices', {})
    trends = data.get('trend_analysis', {})
    zones = data.get('zones', [])
    alerts = data.get('alerts', [])
    
    ndvi_data = raw_indices.get('ndvi', {})
    ndwi_data = raw_indices.get('ndwi', {})
    evi_data = raw_indices.get('evi', {})
    
    prompt = f"""You are a senior satellite analyst and environmental scientist. Generate a comprehensive, detailed professional analysis report in French.

DONNÉES COMPLÈTES:

Scores Composites (0-100):
- Santé de la Végétation: {scores.get('vegetation_health', 'N/A')}/100
- Stress Hydrique: {scores.get('water_stress', 'N/A')}/100
- Productivité: {scores.get('productivity', 'N/A')}/100
- Risque Environnemental: {scores.get('environmental_risk', 'N/A')}/100
- Durabilité Globale: {scores.get('sustainability', 'N/A')}/100

Indices Spectraux Bruts:
- NDVI: Moyenne={ndvi_data.get('mean', 'N/A')}, Écart-type={ndvi_data.get('std', 'N/A')}, Min={ndvi_data.get('min', 'N/A')}, Max={ndvi_data.get('max', 'N/A')}
- NDWI: Moyenne={ndwi_data.get('mean', 'N/A')}
- EVI: Moyenne={evi_data.get('mean', 'N/A')}

Analyse Temporelle:
- Tendance NDVI: {trends.get('ndvi_trend', 'N/A')} ({trends.get('change_percent', 0)}%)
- Tendance Eau: {trends.get('water_trend', 'N/A')}
- Tendance Productivité: {trends.get('productivity_trend', 'N/A')}

Zones Segmentées: {len(zones)} zones identifiées
Alertes Actives: {len(alerts)}

INSTRUCTIONS POUR LE RAPPORT:

Générez un rapport professionnel LONG et DÉTAILLÉ (minimum 1000 mots) structuré comme suit:

1. RÉSUMÉ EXÉCUTIF (2-3 paragraphes)
   - Vue d'ensemble de l'état de la zone
   - Principaux résultats et conclusions
   - Niveau de préoccupation global

2. ANALYSE DE LA SANTÉ VÉGÉTALE (3-4 paragraphes)
   - Interprétation détaillée du NDVI et EVI
   - Analyse de la distribution spatiale (min, max, écart-type)
   - Comparaison avec les valeurs de référence
   - Identification des zones à risque
   - Causes possibles des variations observées

3. ÉVALUATION DU STRESS HYDRIQUE (3-4 paragraphes)
   - Analyse du NDWI et des indicateurs d'eau
   - Évaluation de la disponibilité en eau
   - Impact sur la végétation
   - Zones critiques nécessitant une attention
   - Recommandations d'irrigation

4. ANALYSE DE PRODUCTIVITÉ (2-3 paragraphes)
   - Estimation de la productivité actuelle
   - Facteurs limitants identifiés
   - Potentiel d'amélioration
   - Comparaison avec le potentiel théorique

5. ÉVALUATION DES RISQUES (2-3 paragraphes)
   - Risques environnementaux identifiés
   - Niveau de criticité
   - Évolution probable
   - Mesures préventives recommandées

6. ANALYSE TEMPORELLE ET TENDANCES (2-3 paragraphes)
   - Évolution des indicateurs dans le temps
   - Tendances observées (croissance/déclin/stabilité)
   - Saisonnalité et cycles
   - Prévisions à court terme

7. ANALYSE PAR ZONES (si applicable)
   - Caractérisation de chaque zone segmentée
   - Comparaison entre zones
   - Zones prioritaires d'intervention

8. RECOMMANDATIONS DÉTAILLÉES (3-4 paragraphes)
   - Actions immédiates (0-15 jours)
   - Actions à court terme (1-3 mois)
   - Actions à moyen terme (3-12 mois)
   - Surveillance continue recommandée

9. CONCLUSION ET SYNTHÈSE (2 paragraphes)
   - Bilan global
   - Perspectives et suivi

Le rapport doit être:
- Scientifiquement rigoureux
- Riche en détails et explications
- Compréhensible par un non-expert
- Actionnable et pratique
- Basé uniquement sur les données fournies

Rédigez le rapport complet en français, en utilisant un langage professionnel mais accessible:"""
    
    return prompt

def create_terroir_audit_prompt(parcel_data: dict, match_results: List[dict]) -> str:
    """Create prompt for Terroir Intelligence Audit"""
    best_match = match_results[0] if match_results else {"name": "Inconnu", "similarity_score": 0}
    
    prompt = f"""You are a specialized Terroir Scientist (Oenology & Geology). Perform a professional 'Terroir Intelligence Audit' for this parcel.

MATCHING RESULT:
- Best Match Reference: {best_match['name']}
- Similarity Score: {best_match['similarity_score']}%
- Mahalanobis Distance: {best_match.get('distance', 'N/A')}

PARCEL DATA (Summarized):
- Topography: Elevation {parcel_data.get('topography', {}).get('elevation')}m, Slope {parcel_data.get('topography', {}).get('slope')}°
- Multi-spectral Health: {parcel_data.get('scores', {}).get('vegetation_health')}/100
- Water Balance: {parcel_data.get('scores', {}).get('water_stress')}/100 stress

INSTRUCTIONS:
Generate a detailed audit in French (Rich scientific style) structured as follows:
1. SIGNATURE DU TERROIR : Analyse de l'empreinte multi-dimensionnelle (250+ variables).
2. COMPARAISON GRAND CRU : Pourquoi ce terroir se rapproche de {best_match['name']}.
3. ÉCARTS CRITIQUES : Quelles sont les faiblesses par rapport à l'étalon de référence.
4. POTENTIEL D'EXCELLENCE : Recommandations pour 'tendre' vers le profil idéal Grand Cru.

Use professional, technical French vocabulary (e.g., drainage, drainage interne, complexe argilo-humique, stress photonique, phénologie).

Audit Report (French):"""
    return prompt

# ==========================================
# LLM INTERACTION
# ==========================================

def query_llm(prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    Query Ollama LLM with a prompt
    
    Args:
        prompt: Input prompt
        max_tokens: Maximum response length
        temperature: Creativity parameter (0-1)
        
    Returns:
        LLM response text
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', '')
        
    except requests.exceptions.ConnectionError:
        logger.warning("Ollama not available. Using fallback mode.")
        raise Exception("LLM service not available")
    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        raise

def parse_json_response(response: str, key: str) -> List:
    """Parse JSON from LLM response"""
    try:
        # Try to extract JSON from response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            return data.get(key, [])
        else:
            return []
    except:
        return []

# ==========================================
# FALLBACK FUNCTIONS (Rule-based)
# ==========================================

def generate_fallback_insight(data: dict) -> str:
    """Generate insight using rule-based logic when LLM unavailable"""
    scores = data.get('scores', {})
    vhs = scores.get('vegetation_health', 50)
    wss = scores.get('water_stress', 50)
    ps = scores.get('productivity', 50)
    gss = scores.get('sustainability', 50)
    
    # Determine overall status
    if gss >= 70:
        status = "excellente"
    elif gss >= 50:
        status = "bonne"
    elif gss >= 30:
        status = "modérée"
    else:
        status = "préoccupante"
    
    # Identify main issue
    if wss > 60:
        main_issue = f"un stress hydrique important ({wss}/100)"
    elif vhs < 40:
        main_issue = f"une santé végétale faible ({vhs}/100)"
    elif ps < 40:
        main_issue = f"une productivité limitée ({ps}/100)"
    else:
        main_issue = "aucun problème majeur identifié"
    
    insight = f"La zone présente une durabilité globale {status} ({gss}/100). "
    insight += f"L'analyse révèle {main_issue}. "
    
    if ps >= 60:
        insight += f"La productivité attendue reste satisfaisante ({ps}/100)."
    else:
        insight += f"Une surveillance accrue est recommandée."
    
    return insight

def generate_fallback_recommendations(data: dict) -> List[str]:
    """Generate recommendations using rule-based logic"""
    recommendations = []
    scores = data.get('scores', {})
    
    # Water stress recommendations
    if scores.get('water_stress', 0) > 60:
        recommendations.append("Optimiser le système d'irrigation dans les zones à fort stress hydrique")
        recommendations.append("Surveiller quotidiennement l'humidité du sol")
    
    # Vegetation health recommendations
    if scores.get('vegetation_health', 100) < 50:
        recommendations.append("Analyser les causes de la faible santé végétale (nutriments, maladies, stress)")
        recommendations.append("Envisager une fertilisation ciblée si carence nutritionnelle détectée")
    
    # Productivity recommendations
    if scores.get('productivity', 100) < 50:
        recommendations.append("Évaluer les pratiques culturales actuelles pour identifier les axes d'amélioration")
    
    # Risk recommendations
    if scores.get('environmental_risk', 0) > 60:
        recommendations.append("Mettre en place un plan de gestion des risques environnementaux")
        recommendations.append("Renforcer la surveillance des conditions météorologiques")
    
    # General recommendation
    if len(recommendations) == 0:
        recommendations.append("Maintenir les bonnes pratiques actuelles")
        recommendations.append("Continuer la surveillance régulière via imagerie satellite")
    
    return recommendations[:5]  # Limit to 5 recommendations

def generate_fallback_detailed_report(data: dict) -> str:
    """Generate comprehensive detailed report using rule-based logic"""
    scores = data.get('scores', {})
    raw_indices = data.get('raw_indices', {})
    trends = data.get('trend_analysis', {})
    zones = data.get('zones', [])
    alerts = data.get('alerts', [])
    aoi = data.get('aoi', {})
    
    vhs = scores.get('vegetation_health', 50)
    wss = scores.get('water_stress', 50)
    ps = scores.get('productivity', 50)
    ers = scores.get('environmental_risk', 50)
    gss = scores.get('sustainability', 50)
    
    ndvi_data = raw_indices.get('ndvi', {})
    ndvi_mean = ndvi_data.get('mean', 0.5)
    ndvi_std = ndvi_data.get('std', 0.1)
    ndvi_min = ndvi_data.get('min', 0.0)
    ndvi_max = ndvi_data.get('max', 1.0)
    
    area_ha = aoi.get('area_hectares', 0)
    
    # Build comprehensive report
    report = f"""
═══════════════════════════════════════════════════════════════════
        RAPPORT D'ANALYSE SATELLITE - GaiaEye Advanced Analytics
═══════════════════════════════════════════════════════════════════

Date d'analyse: {data.get('timestamp', 'N/A')}
Surface analysée: {area_ha:.2f} hectares
Nombre de zones segmentées: {len(zones)}
Alertes actives: {len(alerts)}

═══════════════════════════════════════════════════════════════════
1. RÉSUMÉ EXÉCUTIF
═══════════════════════════════════════════════════════════════════

La zone analysée présente un score de durabilité globale de {gss:.1f}/100, ce qui correspond à un état {"excellent" if gss >= 80 else "bon" if gss >= 60 else "modéré" if gss >= 40 else "préoccupant"}. Cette évaluation synthétise l'ensemble des indicateurs environnementaux, agronomiques et de productivité mesurés par télédétection satellite.

L'analyse multi-spectrale révèle une santé végétale évaluée à {vhs:.1f}/100, un niveau de stress hydrique de {wss:.1f}/100, une productivité estimée à {ps:.1f}/100, et un risque environnemental de {ers:.1f}/100. Ces scores composites sont calculés à partir des indices spectraux NDVI, NDWI, EVI et SAVI, combinés selon des pondérations scientifiquement validées.

{"Les conditions actuelles sont favorables et ne nécessitent qu'une surveillance de routine." if gss >= 70 else "Des mesures d'amélioration sont recommandées pour optimiser les performances de la zone." if gss >= 50 else "Une intervention rapide est nécessaire pour corriger les déséquilibres identifiés."}

═══════════════════════════════════════════════════════════════════
2. ANALYSE DE LA SANTÉ VÉGÉTALE
═══════════════════════════════════════════════════════════════════

Score de Santé Végétale: {vhs:.1f}/100 ({"Excellent" if vhs >= 80 else "Bon" if vhs >= 60 else "Modéré" if vhs >= 40 else "Faible"})

L'indice NDVI (Normalized Difference Vegetation Index) mesuré présente une valeur moyenne de {ndvi_mean:.3f}, avec un écart-type de {ndvi_std:.3f}, un minimum de {ndvi_min:.3f} et un maximum de {ndvi_max:.3f}. Ces valeurs indiquent {"une végétation dense et vigoureuse" if ndvi_mean > 0.6 else "une végétation modérément développée" if ndvi_mean > 0.4 else "une végétation clairsemée ou stressée"}.

La distribution spatiale du NDVI, caractérisée par un écart-type de {ndvi_std:.3f}, révèle {"une forte hétérogénéité spatiale" if ndvi_std > 0.15 else "une homogénéité relative" if ndvi_std > 0.08 else "une très forte homogénéité"} de la couverture végétale. {"Cette variabilité suggère la présence de zones distinctes nécessitant une gestion différenciée." if ndvi_std > 0.15 else "Cette uniformité facilite une gestion homogène de l'ensemble de la zone." if ndvi_std < 0.08 else ""}

{"L'amplitude entre les valeurs minimales et maximales (" + f"{ndvi_min:.3f} à {ndvi_max:.3f}" + ") indique la présence de zones critiques nécessitant une attention particulière, notamment les secteurs présentant des valeurs inférieures à 0.3." if ndvi_min < 0.3 else "L'ensemble de la zone présente des valeurs NDVI satisfaisantes, sans zone critique identifiée."}

Le score composite de santé végétale ({vhs:.1f}/100) intègre également l'EVI (Enhanced Vegetation Index) et le SAVI (Soil Adjusted Vegetation Index), offrant une évaluation robuste qui minimise les effets de sol et d'atmosphère. {"Cette valeur élevée témoigne d'une biomasse importante et d'une activité photosynthétique optimale." if vhs >= 70 else "Cette valeur modérée suggère un potentiel d'amélioration significatif." if vhs >= 50 else "Cette valeur faible nécessite une investigation approfondie des causes sous-jacentes (stress hydrique, nutritionnel, phytosanitaire)."}

═══════════════════════════════════════════════════════════════════
3. ÉVALUATION DU STRESS HYDRIQUE
═══════════════════════════════════════════════════════════════════

Score de Stress Hydrique: {wss:.1f}/100 ({"Critique" if wss >= 70 else "Élevé" if wss >= 50 else "Modéré" if wss >= 30 else "Faible"})

L'analyse du stress hydrique, basée sur l'indice NDWI (Normalized Difference Water Index) et les données de précipitations, révèle un niveau de stress de {wss:.1f}/100. {"Ce niveau critique nécessite une intervention immédiate pour éviter des dommages irréversibles à la végétation." if wss >= 70 else "Ce niveau de stress modéré à élevé requiert une surveillance accrue et des ajustements de l'irrigation." if wss >= 40 else "Les conditions hydriques sont actuellement satisfaisantes."}

{"La disponibilité en eau apparaît comme le facteur limitant principal de la productivité dans cette zone. Les indices spectraux montrent des signes clairs de déficit hydrique, particulièrement dans les secteurs où le NDVI est inférieur à 0.5." if wss >= 60 else "L'équilibre hydrique est globalement maintenu, bien qu'une optimisation de l'irrigation pourrait améliorer les performances." if wss >= 40 else "Les réserves en eau sont adéquates pour soutenir la croissance végétale actuelle."}

{"L'impact du stress hydrique sur la végétation est déjà visible dans les données spectrales, avec une corrélation négative entre le NDWI et le NDVI dans certaines zones. Une intervention rapide permettrait de limiter les pertes de productivité." if wss >= 60 else "Le stress hydrique reste gérable avec les pratiques actuelles, mais une surveillance continue est recommandée." if wss >= 40 else ""}

{"Recommandation prioritaire: Mise en place d'un système d'irrigation de précision ciblant les zones à fort stress identifiées par segmentation spatiale." if wss >= 60 else "Recommandation: Optimisation du calendrier d'irrigation en fonction des prévisions météorologiques et des besoins spécifiques de chaque zone." if wss >= 40 else "Recommandation: Maintien des pratiques actuelles avec surveillance régulière."}

═══════════════════════════════════════════════════════════════════
4. ANALYSE DE PRODUCTIVITÉ
═══════════════════════════════════════════════════════════════════

Score de Productivité: {ps:.1f}/100 ({"Excellent" if ps >= 80 else "Bon" if ps >= 60 else "Modéré" if ps >= 40 else "Faible"})

La productivité estimée de {ps:.1f}/100 résulte d'une combinaison pondérée de la santé végétale ({vhs:.1f}/100), de la disponibilité en eau (inverse du stress: {100-wss:.1f}/100), et de la qualité du sol. {"Cette valeur élevée indique un potentiel de rendement optimal dans les conditions actuelles." if ps >= 70 else "Cette valeur modérée suggère des marges d'amélioration significatives." if ps >= 50 else "Cette valeur faible nécessite une révision complète des pratiques culturales."}

{"Les principaux facteurs limitants identifiés sont: le stress hydrique ({wss:.1f}/100) et " if wss >= 50 else ""}{"la santé végétale suboptimale ({vhs:.1f}/100)." if vhs < 60 else "l'optimisation de la gestion pourrait encore améliorer les performances."}

Le potentiel d'amélioration est {"limité car les conditions sont déjà proches de l'optimum" if ps >= 80 else "significatif, avec des gains potentiels de 20-30% en optimisant l'irrigation et la nutrition" if ps >= 50 else "très important, avec des gains potentiels de 50% ou plus en corrigeant les facteurs limitants majeurs"}.

Comparé au potentiel théorique de la zone (estimé à 100/100 dans des conditions optimales), la productivité actuelle atteint {ps:.0f}% de ce potentiel. {"Cela représente une performance excellente." if ps >= 80 else "Il existe donc une marge d'amélioration substantielle." if ps < 70 else ""}

═══════════════════════════════════════════════════════════════════
5. ÉVALUATION DES RISQUES ENVIRONNEMENTAUX
═══════════════════════════════════════════════════════════════════

Score de Risque Environnemental: {ers:.1f}/100 ({"Critique" if ers >= 70 else "Élevé" if ers >= 50 else "Modéré" if ers >= 30 else "Faible"})

L'évaluation des risques environnementaux intègre le stress hydrique, les risques phytosanitaires et les conditions météorologiques. Un score de {ers:.1f}/100 indique un niveau de risque {"critique nécessitant des mesures d'urgence" if ers >= 70 else "élevé requérant une vigilance accrue" if ers >= 50 else "modéré gérable avec les pratiques standards" if ers >= 30 else "faible permettant une gestion normale"}.

{"Les risques identifiés incluent principalement le stress hydrique sévère, qui augmente la vulnérabilité aux maladies et ravageurs." if wss >= 60 else "Les conditions actuelles sont relativement stables, sans risque majeur immédiat identifié." if ers < 40 else "Une surveillance des conditions météorologiques et phytosanitaires est recommandée."}

L'évolution probable à court terme (15-30 jours) dépendra {"fortement des précipitations à venir et de la mise en place de mesures correctives" if ers >= 50 else "des conditions météorologiques normales et du maintien des bonnes pratiques actuelles"}.

Mesures préventives recommandées:
{"- Mise en place immédiate d'un plan d'irrigation d'urgence" if wss >= 70 else ""}
{"- Surveillance phytosanitaire renforcée (risque accru en conditions de stress)" if ers >= 50 else ""}
{"- Suivi hebdomadaire des indices spectraux pour détecter toute dégradation" if ers >= 40 else ""}
{"- Maintien des pratiques de surveillance standard" if ers < 40 else ""}

═══════════════════════════════════════════════════════════════════
6. ANALYSE TEMPORELLE ET TENDANCES
═══════════════════════════════════════════════════════════════════

Tendance NDVI: {trends.get('ndvi_trend', 'stable')} ({trends.get('change_percent', 0):.1f}%)
Tendance Eau: {trends.get('water_trend', 'stable')}
Tendance Productivité: {trends.get('productivity_trend', 'stable')}

{"L'analyse temporelle révèle une tendance à la baisse du NDVI de " + f"{abs(trends.get('change_percent', 0)):.1f}%" + ", ce qui nécessite une attention immédiate pour inverser cette dynamique négative." if trends.get('ndvi_trend') == 'decreasing' and abs(trends.get('change_percent', 0)) > 5 else ""}
{"L'analyse temporelle montre une tendance à la hausse du NDVI de " + f"{trends.get('change_percent', 0):.1f}%" + ", indiquant une amélioration progressive des conditions végétales." if trends.get('ndvi_trend') == 'increasing' and trends.get('change_percent', 0) > 5 else ""}
{"Les indicateurs sont stables dans le temps, suggérant des conditions relativement constantes." if trends.get('ndvi_trend') == 'stable' else ""}

{"Cette évolution s'inscrit probablement dans un cycle saisonnier normal, mais une surveillance continue est recommandée pour détecter toute anomalie." if trends.get('ndvi_trend') == 'stable' else "Cette tendance nécessite une analyse approfondie pour en identifier les causes et mettre en place des actions correctives." if trends.get('ndvi_trend') == 'decreasing' else "Cette tendance positive doit être maintenue et renforcée par des pratiques adaptées."}

Prévisions à court terme (30 jours):
{"- Poursuite probable de la dégradation sans intervention" if trends.get('ndvi_trend') == 'decreasing' else ""}
{"- Amélioration continue attendue si les conditions actuelles persistent" if trends.get('ndvi_trend') == 'increasing' else ""}
{"- Stabilité attendue avec les pratiques actuelles" if trends.get('ndvi_trend') == 'stable' else ""}

═══════════════════════════════════════════════════════════════════
7. ANALYSE PAR ZONES SEGMENTÉES
═══════════════════════════════════════════════════════════════════

{len(zones)} zones homogènes ont été identifiées par segmentation K-means basée sur les valeurs NDVI:

"""
    
    # Add zone details
    for i, zone in enumerate(zones[:5]):  # Limit to 5 zones
        zone_id = zone.get('zone_id', i+1)
        health = zone.get('health_status', 'N/A')
        risk = zone.get('risk_level', 'N/A')
        ndvi = zone.get('avg_ndvi', 0)
        area_pct = zone.get('area_percent', 0)
        
        report += f"""
Zone {zone_id} ({area_pct:.1f}% de la surface totale):
- Santé: {health}
- Risque: {risk}
- NDVI moyen: {ndvi:.3f}
- Caractérisation: {"Zone très productive, à maintenir en priorité" if ndvi > 0.7 else "Zone productive, optimisation possible" if ndvi > 0.5 else "Zone à risque, intervention nécessaire"}
"""
    
    if len(zones) > 0:
        best_zone = max(zones, key=lambda z: z.get('avg_ndvi', 0))
        worst_zone = min(zones, key=lambda z: z.get('avg_ndvi', 0))
        
        report += f"""
Comparaison:
- Zone la plus performante: Zone {best_zone.get('zone_id')} (NDVI: {best_zone.get('avg_ndvi', 0):.3f})
- Zone nécessitant le plus d'attention: Zone {worst_zone.get('zone_id')} (NDVI: {worst_zone.get('avg_ndvi', 0):.3f})
- Écart de performance: {(best_zone.get('avg_ndvi', 0) - worst_zone.get('avg_ndvi', 0)):.3f}

Zones prioritaires d'intervention: {", ".join([f"Zone {z.get('zone_id')}" for z in zones if z.get('risk_level') in ['High', 'Medium']][:3]) if any(z.get('risk_level') in ['High', 'Medium'] for z in zones) else "Aucune zone critique identifiée"}
"""
    else:
        report += "\nAucune segmentation disponible pour cette analyse.\n"
    
    report += f"""
═══════════════════════════════════════════════════════════════════
8. RECOMMANDATIONS DÉTAILLÉES
═══════════════════════════════════════════════════════════════════

ACTIONS IMMÉDIATES (0-15 jours):
{"- Mise en place d'un système d'irrigation d'urgence dans les zones à fort stress hydrique" if wss >= 70 else ""}
{"- Inspection terrain des zones à faible NDVI (<0.3) pour identifier les causes spécifiques" if ndvi_min < 0.3 else ""}
{"- Analyse de sol complémentaire dans les zones à risque élevé" if ers >= 60 else ""}
{"- Maintien des bonnes pratiques actuelles" if gss >= 70 else ""}

ACTIONS À COURT TERME (1-3 mois):
{"- Optimisation du calendrier d'irrigation basé sur les données satellite" if wss >= 40 else ""}
{"- Mise en place d'une fertilisation de précision ciblée par zone" if vhs < 60 else ""}
{"- Installation de capteurs d'humidité du sol pour validation des données satellite" if wss >= 50 else ""}
{"- Surveillance phytosanitaire renforcée" if ers >= 50 else ""}
- Acquisition d'images satellite à haute fréquence (hebdomadaire) pour suivi fin

ACTIONS À MOYEN TERME (3-12 mois):
- Développement d'un modèle prédictif de productivité basé sur l'historique satellite
- Mise en place d'un système d'alerte automatique basé sur les seuils critiques
- Formation du personnel à l'interprétation des données satellite
- Intégration des données météorologiques pour améliorer les prévisions

SURVEILLANCE CONTINUE RECOMMANDÉE:
- Fréquence d'acquisition satellite: Hebdomadaire (période critique) ou Bi-mensuelle (période normale)
- Indicateurs à suivre en priorité: NDVI, NDWI, température de surface
- Seuils d'alerte: NDVI < 0.4, Stress hydrique > 60/100, Risque > 70/100

═══════════════════════════════════════════════════════════════════
9. CONCLUSION ET SYNTHÈSE
═══════════════════════════════════════════════════════════════════

L'analyse satellite multi-spectrale de cette zone de {area_ha:.2f} hectares révèle un état global {"excellent" if gss >= 80 else "satisfaisant" if gss >= 60 else "modéré nécessitant des améliorations" if gss >= 40 else "préoccupant nécessitant une intervention rapide"} avec un score de durabilité de {gss:.1f}/100.

{"Les principaux points forts identifiés sont: une santé végétale satisfaisante ({vhs:.1f}/100) et une productivité élevée ({ps:.1f}/100)." if vhs >= 60 and ps >= 60 else ""}
{"Les principaux défis à relever sont: le stress hydrique élevé ({wss:.1f}/100) et " if wss >= 60 else ""}{"la santé végétale suboptimale ({vhs:.1f}/100)." if vhs < 50 else ""}

Perspective et suivi:
{"Avec les interventions recommandées, une amélioration significative est attendue dans les 2-3 mois, avec un potentiel de gain de productivité de 20-40%." if gss < 60 else "Le maintien des bonnes pratiques actuelles devrait permettre de conserver ces excellentes performances." if gss >= 80 else "Une optimisation ciblée pourrait améliorer les performances de 10-20% supplémentaires."}

La télédétection satellite offre un outil puissant pour le suivi continu et l'optimisation de la gestion de cette zone. Il est recommandé de poursuivre cette surveillance à fréquence {"hebdomadaire" if gss < 50 else "bi-mensuelle" if gss < 70 else "mensuelle"} pour détecter rapidement toute évolution et ajuster les pratiques en conséquence.

═══════════════════════════════════════════════════════════════════
NOTE TECHNIQUE : ACTIVATION DE L'INTELLIGENCE GÉNÉRATIVE
═══════════════════════════════════════════════════════════════════

Ce rapport a été généré par le moteur expert déterministe car le service LLM local (Ollama) n'est pas détecté. 

Pour activer des analyses encore plus riches, contextuelles et rédigées intégralement par IA :

1. Téléchargez et installez Ollama : https://ollama.com
2. Ouvrez un terminal et téléchargez le modèle Qwen :
   > ollama pull qwen2.5:7b
3. Assurez-vous qu'Ollama est en cours d'exécution.
4. Redémarrez ce serveur backend GaiaEye.

Une fois activée, l'IA produira des rapports narratifs uniques, des comparaisons croisées avancées et des insights encore plus profonds.

═══════════════════════════════════════════════════════════════════
FIN DU RAPPORT
═══════════════════════════════════════════════════════════════════

Rapport généré par GaiaEye Advanced Analytics
Technologie: Télédétection satellite multi-spectrale + Intelligence Artificielle
Données sources: Sentinel-2, MODIS, CHIRPS
"""
    
    return report.strip()

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def check_llm_availability() -> bool:
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_available_models() -> List[str]:
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        return []
    except:
        return []
