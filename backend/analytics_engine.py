"""
GaiaEye Advanced Analytics Engine

This module provides intelligent analysis on top of Google Earth Engine data.
It calculates composite scores, detects trends, and performs spatial analysis.

Key Features:
- Composite scoring (0-100 normalized)
- Statistical analysis (mean, std, anomalies)
- Temporal trend detection
- Zone segmentation using clustering
"""

import numpy as np
from scipy import stats
from sklearn.cluster import KMeans
from typing import Dict, List, Tuple
import datetime

# ==========================================
# COMPOSITE SCORE CALCULATORS
# ==========================================

def calculate_composite_scores(gee_data: dict) -> dict:
    """
    Calculate normalized 0-100 composite scores from GEE indices
    
    Args:
        gee_data: Dictionary containing raw GEE indices (NDVI, NDWI, EVI, etc.)
        
    Returns:
        Dictionary with all composite scores
    """
    # Extract raw indices
    ndvi = gee_data.get('ndvi', {})
    ndwi = gee_data.get('ndwi', {})
    evi = gee_data.get('evi', {})
    savi = gee_data.get('savi', {})
    
    # Get mean values (fallback to defaults if missing)
    ndvi_mean = ndvi.get('mean', 0.5)
    ndwi_mean = ndwi.get('mean', 0.2)
    evi_mean = evi.get('mean', 0.4)
    savi_mean = savi.get('mean', 0.45)
    
    # 1. Vegetation Health Score (0-100)
    vhs = calculate_vegetation_health_score(ndvi_mean, evi_mean, savi_mean)
    
    # 2. Water Stress Score (0-100) - Higher = More stress
    wss = calculate_water_stress_score(ndwi_mean, gee_data.get('rainfall', 0))
    
    # 3. Productivity Score (0-100)
    ps = calculate_productivity_score(vhs, wss, gee_data.get('soil_health', 50))
    
    # 4. Environmental Risk Score (0-100)
    ers = calculate_environmental_risk_score(
        wss, 
        gee_data.get('pest_risk', 30),
        gee_data.get('weather_risk', 40)
    )
    
    # 5. Global Sustainability Score (0-100)
    gss = calculate_global_sustainability_score(vhs, ps, ers)
    
    return {
        'vegetation_health': round(vhs, 1),
        'water_stress': round(wss, 1),
        'productivity': round(ps, 1),
        'environmental_risk': round(ers, 1),
        'sustainability': round(gss, 1)
    }

def calculate_vegetation_health_score(ndvi: float, evi: float, savi: float) -> float:
    """
    Vegetation Health Score = (NDVI × 0.5) + (EVI × 0.3) + (SAVI × 0.2)
    Normalized to 0-100 scale
    """
    # Normalize indices to 0-1 range (assuming typical ranges)
    ndvi_norm = normalize_value(ndvi, -0.2, 0.9)  # NDVI typical range
    evi_norm = normalize_value(evi, -0.2, 0.8)    # EVI typical range
    savi_norm = normalize_value(savi, -0.2, 0.8)  # SAVI typical range
    
    # Weighted combination
    vhs = (ndvi_norm * 0.5) + (evi_norm * 0.3) + (savi_norm * 0.2)
    
    return vhs * 100

def calculate_water_stress_score(ndwi: float, rainfall: float) -> float:
    """
    Water Stress Score = 100 - (NDWI × 0.6 + Rainfall × 0.4)
    Higher score = More stress
    """
    # Normalize NDWI (-1 to 1 range)
    ndwi_norm = normalize_value(ndwi, -0.5, 0.5)
    
    # Normalize rainfall (0-500mm typical range)
    rainfall_norm = normalize_value(rainfall, 0, 500)
    
    # Calculate water availability (0-1)
    water_availability = (ndwi_norm * 0.6) + (rainfall_norm * 0.4)
    
    # Invert to get stress (high availability = low stress)
    stress = 1.0 - water_availability
    
    return stress * 100

def calculate_productivity_score(vhs: float, wss: float, soil_health: float) -> float:
    """
    Productivity Score = (VHS × 0.6) + ((100 - WSS) × 0.3) + (Soil × 0.1)
    """
    water_availability = 100 - wss  # Invert stress to availability
    
    ps = (vhs * 0.6) + (water_availability * 0.3) + (soil_health * 0.1)
    
    return min(100, max(0, ps))

def calculate_environmental_risk_score(wss: float, pest_risk: float, weather_risk: float) -> float:
    """
    Environmental Risk Score = (WSS × 0.4) + (Pest × 0.3) + (Weather × 0.3)
    """
    ers = (wss * 0.4) + (pest_risk * 0.3) + (weather_risk * 0.3)
    
    return min(100, max(0, ers))

def calculate_global_sustainability_score(vhs: float, ps: float, ers: float) -> float:
    """
    Global Sustainability Score = (VHS × 0.35) + (PS × 0.35) + ((100 - ERS) × 0.30)
    """
    environmental_health = 100 - ers  # Invert risk to health
    
    gss = (vhs * 0.35) + (ps * 0.35) + (environmental_health * 0.30)
    
    return min(100, max(0, gss))

# ==========================================
# STATISTICAL ANALYSIS
# ==========================================

def analyze_statistics(values: np.ndarray) -> dict:
    """
    Calculate comprehensive statistics for a dataset
    
    Returns:
        Dictionary with mean, median, std, min, max, percentiles
    """
    if len(values) == 0:
        return {
            'mean': 0, 'median': 0, 'std': 0,
            'min': 0, 'max': 0, 'p25': 0, 'p75': 0
        }
    
    return {
        'mean': float(np.mean(values)),
        'median': float(np.median(values)),
        'std': float(np.std(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'p25': float(np.percentile(values, 25)),
        'p75': float(np.percentile(values, 75))
    }

def detect_spatial_anomalies(values: np.ndarray, threshold: float = 2.0) -> dict:
    """
    Detect outliers using z-score method
    
    Args:
        values: Array of values (e.g., NDVI pixels)
        threshold: Z-score threshold (default 2.0 = 95% confidence)
        
    Returns:
        Dictionary with anomaly statistics
    """
    if len(values) < 3:
        return {'anomaly_count': 0, 'anomaly_percent': 0, 'anomalies': []}
    
    z_scores = np.abs(stats.zscore(values))
    anomalies = values[z_scores > threshold]
    
    return {
        'anomaly_count': len(anomalies),
        'anomaly_percent': (len(anomalies) / len(values)) * 100,
        'anomaly_threshold': threshold,
        'anomalies': anomalies.tolist()[:10]  # Return first 10 for inspection
    }

# ==========================================
# TEMPORAL ANALYSIS
# ==========================================

def analyze_temporal_trends(historical_data: List[dict]) -> dict:
    """
    Analyze trends over time
    
    Args:
        historical_data: List of {date, value} dictionaries
        
    Returns:
        Trend analysis with direction and change percentage
    """
    if len(historical_data) < 2:
        return {
            'trend': 'insufficient_data',
            'change_percent': 0,
            'slope': 0
        }
    
    # Sort by date
    sorted_data = sorted(historical_data, key=lambda x: x['date'])
    
    # Extract values
    values = np.array([d['value'] for d in sorted_data])
    x = np.arange(len(values))
    
    # Calculate linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
    
    # Determine trend direction
    if abs(slope) < 0.01:  # Threshold for "stable"
        trend = 'stable'
    elif slope > 0:
        trend = 'increasing'
    else:
        trend = 'decreasing'
    
    # Calculate percent change
    if values[0] != 0:
        change_percent = ((values[-1] - values[0]) / abs(values[0])) * 100
    else:
        change_percent = 0
    
    return {
        'trend': trend,
        'change_percent': round(change_percent, 2),
        'slope': round(slope, 4),
        'r_squared': round(r_value ** 2, 3),
        'confidence': 'high' if abs(r_value) > 0.7 else 'moderate' if abs(r_value) > 0.4 else 'low'
    }

def compare_periods(current: dict, previous: dict) -> dict:
    """
    Compare two time periods
    
    Returns:
        Comparison metrics
    """
    changes = {}
    
    for key in current.keys():
        if key in previous and isinstance(current[key], (int, float)):
            curr_val = current[key]
            prev_val = previous[key]
            
            if prev_val != 0:
                percent_change = ((curr_val - prev_val) / abs(prev_val)) * 100
            else:
                percent_change = 0
            
            changes[key] = {
                'current': curr_val,
                'previous': prev_val,
                'change': curr_val - prev_val,
                'change_percent': round(percent_change, 2),
                'direction': 'up' if curr_val > prev_val else 'down' if curr_val < prev_val else 'stable'
            }
    
    return changes

# ==========================================
# ZONE SEGMENTATION
# ==========================================

def segment_homogeneous_zones(ndvi_array: np.ndarray, n_zones: int = 3) -> dict:
    """
    Segment area into homogeneous zones using K-means clustering
    
    Args:
        ndvi_array: 2D array of NDVI values
        n_zones: Number of zones to create (default 3)
        
    Returns:
        Zone analysis with statistics per zone
    """
    # Flatten array for clustering
    flat_values = ndvi_array.flatten().reshape(-1, 1)
    
    # Remove NaN values
    valid_mask = ~np.isnan(flat_values.flatten())
    valid_values = flat_values[valid_mask]
    
    if len(valid_values) < n_zones:
        return {'zones': [], 'error': 'Insufficient data for segmentation'}
    
    # Perform K-means clustering
    kmeans = KMeans(n_clusters=n_zones, random_state=42, n_init=10)
    labels = kmeans.fit_predict(valid_values)
    
    # Analyze each zone
    zones = []
    for i in range(n_zones):
        zone_values = valid_values[labels == i]
        zone_percent = (len(zone_values) / len(valid_values)) * 100
        
        # Classify health based on mean NDVI
        mean_ndvi = float(np.mean(zone_values))
        health_status = classify_health(mean_ndvi)
        risk_level = classify_risk(mean_ndvi)
        
        zones.append({
            'zone_id': i + 1,
            'area_percent': round(zone_percent, 1),
            'avg_ndvi': round(mean_ndvi, 3),
            'std_ndvi': round(float(np.std(zone_values)), 3),
            'health_status': health_status,
            'risk_level': risk_level,
            'pixel_count': len(zone_values)
        })
    
    # Sort zones by health (best to worst)
    zones.sort(key=lambda x: x['avg_ndvi'], reverse=True)
    
    return {
        'zones': zones,
        'n_zones': n_zones,
        'total_pixels': len(valid_values)
    }

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Normalize value to 0-1 range"""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    return max(0, min(1, normalized))

def classify_health(ndvi: float) -> str:
    """Classify vegetation health based on NDVI"""
    if ndvi > 0.7:
        return 'Excellent'
    elif ndvi > 0.5:
        return 'Good'
    elif ndvi > 0.3:
        return 'Moderate'
    else:
        return 'Poor'

def classify_risk(ndvi: float) -> str:
    """Classify risk level based on NDVI"""
    if ndvi > 0.6:
        return 'Low'
    elif ndvi > 0.4:
        return 'Medium'
    else:
        return 'High'

def get_score_interpretation(score: float) -> str:
    """Get human-readable interpretation of a 0-100 score"""
    if score >= 80:
        return 'Excellent'
    elif score >= 60:
        return 'Good'
    elif score >= 40:
        return 'Moderate'
    elif score >= 20:
        return 'Poor'
    else:
        return 'Critical'
