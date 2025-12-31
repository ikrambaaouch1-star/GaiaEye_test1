from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import ee
import gee_service
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

# Initialize Earth Engine
gee_service.initialize_gee()

@app.route('/')
def home():
    return "Satellite Intelligence Platform API Running. Use POST /api/analyze."

@app.route('/api/ai_status', methods=['GET'])
def ai_status():
    """Check if the AI (Ollama) service is available"""
    import llm_service
    is_available = llm_service.check_llm_availability()
    models = llm_service.get_available_models() if is_available else []
    
    return jsonify({
        "status": "online" if is_available else "offline",
        "model": llm_service.MODEL_NAME,
        "available_models": models,
        "is_fallback_mode": not is_available
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Endpoint to receive coordinates and return Indicator tile URL.
    Expected JSON:
    {
        "north": float, "south": float, "east": float, "west": float,
        "date_start": "YYYY-MM-DD", "date_end": "YYYY-MM-DD",
        "indicator": "NDVI" | "EVI" | "SAVI" | "NDWI" | "MNDWI" | "NDBI" | "LST" | "RAIN" | "SAR" | "ELEVATION" | "SLOPE"
    }
    """
    try:
        data = request.json
        
        # Validation
        required_fields = ['north', 'south', 'east', 'west']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing coordinates. Requires north, south, east, west."}), 400
            
        coords = {
            'north': data['north'],
            'south': data['south'],
            'east': data['east'],
            'west': data['west']
        }
        
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        indicator = data.get('indicator', 'NDVI') # Default to NDVI

        tile_url = gee_service.get_indicator_layer(coords, date_start, date_end, indicator)
        
        return jsonify({
            "success": True,
            "tile_url": tile_url,
            "coords": coords,
            "indicator": indicator,
            "dates": {"start": date_start, "end": date_end}
        })

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/dashboard_stats', methods=['POST'])
def dashboard_stats():
    """
    Agricultural Dashboard endpoint
    Expected JSON:
    {
        "north": float, "south": float, "east": float, "west": float,
        "date_start": "YYYY-MM-DD", "date_end": "YYYY-MM-DD",
        "crop_type": "wheat" | "corn" | "rice" | "soybean" (optional),
        "input_costs": float (optional, in $/hectare)
    }
    """
    try:
        data = request.json
        
        # Validation
        required_fields = ['north', 'south', 'east', 'west']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing coordinates"}), 400
            
        coords = {
            'north': data['north'],
            'south': data['south'],
            'east': data['east'],
            'west': data['west']
        }
        
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        crop_type = data.get('crop_type', 'wheat')
        input_costs = data.get('input_costs', 500)  # Default $500/ha
        
        # Calculate dashboard metrics
        stats = gee_service.calculate_dashboard_metrics(
            coords, date_start, date_end, crop_type, input_costs
        )
        
        return jsonify({
            "success": True,
            "stats": stats,
            "coords": coords,
            "dates": {"start": date_start, "end": date_end}
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/terroir_analysis', methods=['POST'])
def terroir_analysis():
    """
    Comprehensive Terroir Audit: Vector Matching + AI Reasoning
    """
    data = request.json
    if not data or not all(k in data for k in ['north', 'south', 'east', 'west']):
        return jsonify({"success": False, "error": "Missing coordinates"}), 400

    coords = {
        'north': data['north'], 'south': data['south'],
        'east': data['east'], 'west': data['west']
    }

    try:
        # 1. Fetch exhaustive raw data
        raw_data = gee_service.get_exhaustive_terroir_data(coords)
        
        # 2. Generate feature vector and find match
        import terroir_engine
        import llm_service
        parcel_fingerprint = terroir_engine.terroir_engine.create_terroir_fingerprint(raw_data)
        matches = terroir_engine.terroir_engine.find_matching_terroir(parcel_fingerprint)
        gaps = terroir_engine.terroir_engine.detect_critical_gaps(parcel_fingerprint, matches[0]['id'])
        
        # 3. AI Reasoning (Scientific Audit)
        audit_report = llm_service.generate_terroir_audit(raw_data, matches)
        
        return jsonify({
            "success": True,
            "matches": matches,
            "gaps": gaps,
            "audit_report": audit_report,
            "raw_summary": {
                "elevation": raw_data['topography']['elevation'],
                "slope": raw_data['topography']['slope'],
                "ndvi": raw_data['optical']['indices']['NDVI']
            }
        })
    except Exception as e:
        logger.error(f"Terroir analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/raw_data', methods=['POST'])
def raw_data():
    """
    Exhaustive Raw Data & Analytics endpoint.
    Triggered automatically on AOI selection.
    """
    try:
        import gee_service
        import terroir_schemas
        
        data = request.json
        required_fields = ['north', 'south', 'east', 'west']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing coordinates"}), 400
            
        coords = {
            'north': data['north'],
            'south': data['south'],
            'east': data['east'],
            'west': data['west']
        }
        
        # Default dates (last 12 months for seasonal analysis)
        date_end = data.get('date_end', datetime.now().strftime('%Y-%m-%d'))
        date_start = data.get('date_start', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
        
        print(f"Extracting raw data for AOI: {coords}")
        
        # Extract from GEE
        raw_results = gee_service.get_exhaustive_terroir_data(coords, date_start, date_end)
        
        # Merge with supplementary structured data (Soil, Bio, plant)
        # In a real system, these would be fetched from a DB or specific GEE assets
        full_response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "geography": coords,
            "a_optical": raw_results['optical'],
            "b_radar_3d": raw_results['radar_lidar'],
            "c_hyperspectral": raw_results['hyperspectral'],
            "d_climate": raw_results['climatology'],
            "e_topography": raw_results['topography'],
            "f_soil_biology": {**terroir_schemas.field_soil_data, **terroir_schemas.biological_data},
            "g_plant_phenology": terroir_schemas.plant_data
        }
        
        return jsonify(full_response)
        
    except Exception as e:
        print(f"Error extracting raw data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/advanced_analysis', methods=['POST'])
def advanced_analysis():
    """
    Advanced AI Analytics endpoint
    Expected JSON:
    {
        "north": float, "south": float, "east": float, "west": float,
        "date_start": "YYYY-MM-DD", "date_end": "YYYY-MM-DD",
        "historical_dates": [optional list of dates for temporal comparison]
    }
    
    Returns structured JSON with:
    - Composite scores (0-100)
    - Statistical analysis
    - Temporal trends
    - Zone segmentation
    - AI-generated insights
    - Recommendations
    - Alerts
    """
    try:
        import analytics_engine
        import llm_service
        import numpy as np
        from datetime import datetime
        
        data = request.json
        
        # Validation
        required_fields = ['north', 'south', 'east', 'west']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing coordinates"}), 400
            
        coords = {
            'north': data['north'],
            'south': data['south'],
            'east': data['east'],
            'west': data['west']
        }
        
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        
        # Step 1: Get raw GEE data for all indices
        print("Fetching GEE data...")
        roi = ee.Geometry.Rectangle([coords['west'], coords['south'], coords['east'], coords['north']])
        
        # Calculate area
        area_m2 = roi.area().getInfo()
        area_ha = area_m2 / 10000
        
        # Get NDVI statistics
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
               .filterBounds(roi) \
               .filterDate(date_start, date_end) \
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
               .map(gee_service.mask_s2_clouds)
        
        composite = s2.median()
        
        # Calculate indices
        ndvi = composite.normalizedDifference(['B8', 'B4'])
        ndwi = composite.normalizedDifference(['B3', 'B8'])
        evi = composite.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {'NIR': composite.select('B8'), 'RED': composite.select('B4'), 'BLUE': composite.select('B2')}
        )
        savi = composite.expression(
           '((NIR - RED) / (NIR + RED + 0.5)) * 1.5',
           {'NIR': composite.select('B8'), 'RED': composite.select('B4')}
        )
        
        # Get statistics
        ndvi_stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', True).combine(ee.Reducer.minMax(), '', True),
            geometry=roi,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        ndwi_stats = ndwi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        evi_stats = evi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        savi_stats = savi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        # Prepare GEE data for analytics
        gee_data = {
            'ndvi': {
                'mean': ndvi_stats.get('nd_mean', 0.5),
                'std': ndvi_stats.get('nd_stdDev', 0.1),
                'min': ndvi_stats.get('nd_min', 0.0),
                'max': ndvi_stats.get('nd_max', 1.0)
            },
            'ndwi': {
                'mean': ndwi_stats.get('nd', 0.2)
            },
            'evi': {
                'mean': evi_stats.get('constant', 0.4)
            },
            'savi': {
                'mean': savi_stats.get('constant', 0.45)
            },
            'rainfall': 100,  # Placeholder - would fetch from CHIRPS
            'soil_health': 60,  # Placeholder - would calculate from soil proxies
            'pest_risk': 40,
            'weather_risk': 35
        }
        
        # Step 2: Calculate composite scores
        print("Calculating composite scores...")
        scores = analytics_engine.calculate_composite_scores(gee_data)
        
        # Step 3: Perform zone segmentation (if enough data)
        print("Segmenting zones...")
        try:
            # Get NDVI as array for segmentation
            ndvi_array = ndvi.sampleRectangle(region=roi, defaultValue=0).get('nd').getInfo()
            ndvi_np = np.array(ndvi_array)
            
            zones_analysis = analytics_engine.segment_homogeneous_zones(ndvi_np, n_zones=3)
        except:
            zones_analysis = {'zones': [], 'error': 'Segmentation not available for this region'}
        
        # Step 4: Temporal trend analysis (placeholder - would need historical data)
        trend_analysis = {
            'ndvi_trend': 'stable',
            'ndvi_change_percent': 0,
            'water_trend': 'stable',
            'productivity_trend': 'stable'
        }
        
        # Step 5: Generate AI insights and recommendations
        print("Generating AI insights...")
        analysis_data = {
            'scores': scores,
            'trend_analysis': trend_analysis,
            'zones': zones_analysis.get('zones', []),
            'raw_indices': gee_data
        }
        
        # Try LLM, fallback to rule-based
        try:
            ai_insight = llm_service.generate_insights(analysis_data)
            recommendations = llm_service.generate_recommendations(analysis_data)
            detailed_report = llm_service.generate_detailed_report(analysis_data)
        except:
            print("LLM not available, using fallback")
            ai_insight = llm_service.generate_fallback_insight(analysis_data)
            recommendations = llm_service.generate_fallback_recommendations(analysis_data)
            detailed_report = llm_service.generate_fallback_detailed_report(analysis_data)
        
        # Step 6: Detect alerts
        alerts = llm_service.detect_alerts(analysis_data)
        
        # Step 7: Build structured JSON response
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'aoi': {
                'coordinates': coords,
                'area_hectares': round(area_ha, 2)
            },
            'global_score': scores['sustainability'],
            'scores': scores,
            'raw_indices': {
                'ndvi': gee_data['ndvi'],
                'ndwi': gee_data['ndwi'],
                'evi': gee_data['evi'],
                'savi': gee_data['savi']
            },
            'trend_analysis': trend_analysis,
            'zones_analysis': zones_analysis.get('zones', []),
            'alerts': alerts,
            'recommendations': recommendations,
            'ai_insight': ai_insight,
            'detailed_report': detailed_report,
            'dashboard_config': {
                'maps_to_display': ['vegetation_health', 'water_stress', 'risk'],
                'charts_to_display': ['ndvi_temporal', 'productivity_comparison'],
                'highlight_zones': [z['zone_id'] for z in zones_analysis.get('zones', [])[:2]]
            }
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        print(f"Error in advanced analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500


if __name__ == '__main__':
    app.run(debug=True)
