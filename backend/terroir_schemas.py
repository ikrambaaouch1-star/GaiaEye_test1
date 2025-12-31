"""
GaiaEye Terroir Intelligence Box - Data Schemas
Reference definitions for the multi-dimensional terroir engine.
"""

# 📡 1. SATELLITE DATA REQUIREMENTS
# Strictly defines the bands and processing levels for optical sensors
satellite_data_requirements = {
    'sentinel_2': {
        'bands': ['B2', 'B3', 'B4', 'B8', 'B8A', 'B11', 'B12'],
        'indices': ['NDVI', 'NDWI', 'NDMI', 'LAI', 'FAPAR', 'CAB'],
        'resolution': 10,  # meters
        'collection': 'COPERNICUS/S2_SR_HARMONIZED'
    },
    'prisma': {
        'bands_range': (400, 2500),  # nm
        'num_bands': 239,
        'application': 'mineralogy_detailed'
    },
    'landsat': {
        'archive_start': 1984,
        'collections': ['LANDSAT/LT05/C02/T1_L2', 'LANDSAT/LC08/C02/T1_L2', 'LANDSAT/LC09/C02/T1_L2']
    }
}

# 📡 2. RADAR & LIDAR DATA
# Structure for structural and moisture analysis
radar_lidar_data = {
    'sentinel_1': {
        'modes': ['IW'],
        'polarisations': ['VV', 'VH'],
        'derivatives': ['rugosity', 'moisture_index', 'insar_displacement']
    },
    'gedi': {
        'metrics': ['rh98', 'rh50', 'fhd_normal', 'pai'],
        'interpretation': ['structure_3d', 'biomass_density', 'canopy_height']
    }
}

# 🌡️ 3. CLIMATIC DATA
climatic_data = {
    'gpm_imerg': {
        'parameter': 'precipitation',
        'frequency': '30_min',
        'aggregation': 'daily_cumulative'
    },
    'modis_lst': {
        'parameters': ['LST_Day_1km', 'LST_Night_1km'],
        'derived': ['degree_days', 'thermal_amplitude']
    },
    'modis_et': {
        'parameters': ['ET', 'PET'],
        'derived': ['evapotranspiration_actual', 'water_balance']
    }
}

# 🧪 4. FIELD & SOIL DATA
# Ground-truth variables for fusion
field_soil_data = {
    'physical': {
        'texture': ['sand_percent', 'silt_percent', 'clay_percent'],
        'depth': 'cm',
        'porosity': 'percentage'
    },
    'chemical': {
        'ph_h2o': float,
        'organic_matter': 'percentage',
        'cec': 'meq_100g',  # Cation Exchange Capacity
        'active_limestone': 'percentage'
    }
}

# 🦠 5. BIOLOGICAL DATA
biological_data = {
    'soil_microbiome': {
        'diversity_index': 'shannon_wiener',
        'biomass_microbial': 'mg_c_kg'
    },
    'biodiversity': {
        'fauna_richness': int,
        'flora_richness': int
    }
}

# 🌿 6. PLANT DATA
plant_data = {
    'phenology': ['budbreak', 'flowering', 'veraison', 'harvest'],
    'status': {
        'chlorophyll_content': 'µg_cm2',
        'leaf_water_potential': 'MPa',
        'nitrogen_index': float
    }
}

# 🏆 7. GRAND CRU DATABASE & REFERENCE TERROIRS
# Pre-defined feature vectors for elite reference sites
grand_cru_database = [
    {
        'id': 'pauillac_premier_cru',
        'name': 'Pauillac - Graves Profondes',
        'vector_sample': {
            'clay_content': 15,
            'drainage_score': 95,
            'thermal_amplitude_avg': 12.5,
            'elevation_avg': 25,
            'geology': 'Garonne Gravel'
        }
    },
    {
        'id': 'vosne_romanee_grand_cru',
        'name': 'Vosne-Romanée - Argilo-Calcaire',
        'vector_sample': {
            'clay_content': 35,
            'drainage_score': 85,
            'thermal_amplitude_avg': 14.2,
            'elevation_avg': 280,
            'geology': 'Jurassic Limestone'
        }
    }
]

# 🤖 8. AI INPUT & METRICS
ai_input_variables = {
    'dimension': 250,
    'normalization': 'min_max_scaling',
    'categorical_encoding': 'one_hot'
}

similarity_metrics = {
    'method': 'Weighted Mahalanobis Distance',
    'weights': {
        'soil': 0.4,
        'climate': 0.3,
        'satellite_signals': 0.2,
        'biological': 0.1
    }
}
