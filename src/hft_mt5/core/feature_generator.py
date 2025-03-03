import numpy as np
import pandas as pd
from typing import Dict, List
from .data_types import TickBuffer

class FeatureGenerator:
    """Generates features from tick data for signal generation."""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
    
    def calculate_features(self, tick_buffer: TickBuffer) -> Dict[str, float]:
        """Calculate features from recent ticks."""
        try:
            # Get recent ticks as DataFrame
            df = tick_buffer.to_dataframe(self.window_size)
            if len(df) < self.window_size or not all(col in df.columns for col in ['time', 'bid', 'ask', 'volume', 'mid_price']):
                return {}
                
            features = {}
            
            # Price features
            features['spread'] = df['ask'].iloc[-1] - df['bid'].iloc[-1]
            features['mid_price'] = (df['ask'].iloc[-1] + df['bid'].iloc[-1]) / 2
            features['price_change'] = features['mid_price'] - (df['ask'].iloc[0] + df['bid'].iloc[0]) / 2
            
            # Volatility features
            features['volatility'] = df['mid_price'].std()
            features['price_range'] = df['ask'].max() - df['bid'].min()
            
            # Volume features
            features['volume_sum'] = df['volume'].sum()
            # Use pd.Timedelta to handle time differences safely
            time_diff = pd.to_numeric(df['time'].iloc[-1] - df['time'].iloc[0])
            features['volume_intensity'] = features['volume_sum'] / time_diff if time_diff > 0 else 0
            
            # Microstructure features
            features['bid_strength'] = (df['bid'].diff() > 0).sum() / len(df)
            features['ask_strength'] = (df['ask'].diff() > 0).sum() / len(df)
            
            return features
            
        except (KeyError, IndexError, ZeroDivisionError) as e:
            return {} 