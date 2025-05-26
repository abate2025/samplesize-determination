from dataclasses import dataclass
from typing import Dict, List, Optional
import math
from statsmodels.stats.power import TTestIndPower
import json
import os

@dataclass
class SurveyParameters:
    survey_type: str
    population_size: int
    confidence_level: int = 95
    margin_error: float = 0.05
    avg_cluster_size: int = 20
    icc: Optional[float] = None
    expected_prevalence: float = 0.5
    non_response_rate: float = 0.1
    effect_size: Optional[float] = None  # For power analysis
    alpha: float = 0.05
    power: float = 0.8

class ESSSampleSizeCalculator:
    def __init__(self):
        self.confidence_levels = {90: 1.645, 95: 1.96, 99: 2.576}
        self.load_survey_profiles()
        
    def load_survey_profiles(self):
        """Load survey profiles from JSON file"""
        try:
            with open(os.path.join('assets', 'survey_types.json')) as f:
                self.survey_profiles = json.load(f)
        except:
            # Defaults if file missing
            self.survey_profiles = [
                {
                    'id': 'annual_agri',
                    'name': 'Annual Agriculture Survey',
                    'default_icc': 0.15,
                    'default_cluster_size': 25,
                    'description': 'Crop area and production estimates'
                }
                # ... other survey types
            ]

    def calculate_deff(self, avg_cluster_size: int, icc: float) -> float:
        """Design effect for cluster sampling (1 + (b-1)*icc)"""
        return 1 + (avg_cluster_size - 1) * icc

    def calculate_power(self, effect_size: float, alpha: float, power: float) -> float:
        """Statistical power calculation"""
        analysis = TTestIndPower()
        return analysis.solve_power(
            effect_size=effect_size,
            nobs1=None,
            alpha=alpha,
            power=power
        )

    def calculate_sample(self, params: SurveyParameters) -> Dict:
        """Comprehensive sample size calculation"""
        # Get survey defaults
        profile = next(p for p in self.survey_profiles if p['id'] == params.survey_type)
        icc = params.icc or profile['default_icc']
        b = params.avg_cluster_size or profile['default_cluster_size']
        
        # Key calculations
        deff = self.calculate_deff(b, icc)
        n0 = self._calculate_base_sample(params)
        n_design = n0 * deff
        n_fpc = self._apply_fpc(n_design, params.population_size)
        final_n = n_fpc / (1 - params.non_response_rate)
        
        # Power analysis if effect size provided
        power_sample = None
        if params.effect_size:
            power_sample = self.calculate_power(
                params.effect_size,
                params.alpha,
                params.power
            )

        return {
            'base_sample_size': math.ceil(n0),
            'design_effect': round(deff, 3),
            'icc': round(icc, 3),
            'cluster_size': b,
            'adjusted_sample_size': math.ceil(n_design),
            'final_sample_size': math.ceil(final_n),
            'power_sample_size': math.ceil(power_sample) if power_sample else None,
            'effective_sample_size': math.ceil(n0)
        }

    def _calculate_base_sample(self, params: SurveyParameters) -> float:
        """Base sample size calculation"""
        Z = self.confidence_levels[params.confidence_level]
        return (Z**2 * params.expected_prevalence * (1 - params.expected_prevalence)) / (params.margin_error**2)

    def _apply_fpc(self, n: float, N: int) -> float:
        """Finite population correction"""
        return n / (1 + (n - 1)/N) if N else n

    def get_survey_types(self) -> List[Dict]:
        """Available survey types for UI"""
        return [{
            'id': p['id'],
            'name': p['name'],
            'description': p.get('description', '')
        } for p in self.survey_profiles]