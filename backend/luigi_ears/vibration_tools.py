import numpy as np
import pandas as pd
from scipy import signal
from typing import Dict, Optional
import os
import re
import hashlib

class VibrationAnalyzer:
    """
    Wrapper for Luigi's vibration analysis tools.
    """
    SAMPLING_FREQUENCY_HZ = int(os.getenv('TEEVRGATI_SAMPLING_FREQUENCY_HZ', '25600'))
    DURATION_SEC = float(os.getenv('TEEVRGATI_DURATION_SEC', '1.0'))
    MIN_SPEED_FREQ_HZ = float(os.getenv('TEEVRGATI_MIN_SPEED_FREQ_HZ', '5.0'))
    RPM_TO_HZ_CONVERSION = float(os.getenv('TEEVRGATI_RPM_TO_HZ_CONVERSION', '60.0'))
    
    # Fault physical frequency factors and amplitude multipliers
    BEARING_DEFECT_FACTOR = float(os.getenv('TEEVRGATI_BEARING_DEFECT_FACTOR', '3.05'))
    BEARING_DEFECT_AMPLITUDE = float(os.getenv('TEEVRGATI_BEARING_DEFECT_AMPLITUDE', '0.5'))
    MISALIGNMENT_FACTOR = float(os.getenv('TEEVRGATI_MISALIGNMENT_FACTOR', '2.0'))
    MISALIGNMENT_AMPLITUDE = float(os.getenv('TEEVRGATI_MISALIGNMENT_AMPLITUDE', '0.3'))
    NOISE_LEVEL = float(os.getenv('TEEVRGATI_NOISE_LEVEL', '0.05'))
    
    # Spectral and envelope thresholds
    PEAK_HEIGHT_THRESHOLD = float(os.getenv('TEEVRGATI_PEAK_HEIGHT_THRESHOLD', '0.01'))
    MAX_PEAKS_RETURNED = int(os.getenv('TEEVRGATI_MAX_PEAKS_RETURNED', '5'))
    MODULATION_RATIO_THRESHOLD = float(os.getenv('TEEVRGATI_MODULATION_RATIO_THRESHOLD', '0.8'))
    
    # ISO 10816-3 limits
    ISO_ZONE_A_LIMIT = float(os.getenv('TEEVRGATI_ISO_ZONE_A_LIMIT', '2.8'))
    ISO_ZONE_B_LIMIT = float(os.getenv('TEEVRGATI_ISO_ZONE_B_LIMIT', '7.1'))
    ISO_ZONE_C_LIMIT = float(os.getenv('TEEVRGATI_ISO_ZONE_C_LIMIT', '11.2'))
    
    # Frequency ranges
    MISALIGNMENT_MIN_FREQ = float(os.getenv('TEEVRGATI_MISALIGNMENT_MIN_FREQ', '55.0'))
    MISALIGNMENT_MAX_FREQ = float(os.getenv('TEEVRGATI_MISALIGNMENT_MAX_FREQ', '65.0'))
    
    def __init__(self, data_dir: str = "backend/data/vibration/"):
        self.data_dir = data_dir
        self._cache = {}
    
    def analyze(self, asset_id: str, csv_path: Optional[str] = None, query: Optional[str] = None) -> Dict:
        """
        Run full vibration analysis on asset data.
        """
        # Load data and extra metrics from CSV datasets
        extra_metrics = {}
        if csv_path:
            df = pd.read_csv(csv_path)
        else:
            # Load real data using the CSV datasets
            data_dict = self._load_real_data(asset_id, query)
            df = data_dict.get('df')
            extra_metrics = data_dict.get('metrics', {})
        
        if df is None:
            return {
                'error': f'No vibration data found for {asset_id}',
                'fault_type': 'Unknown'
            }
        
        # Run FFT
        fft_result = self._run_fft(df)
        
        # Run envelope analysis (bearing fault detection)
        envelope = self._run_envelope_analysis(df)
        
        # Check ISO standards
        iso_check = self._check_iso_standard(df)
        
        # Override fault type or adjust if it's from CSV or specific source
        fault_type = extra_metrics.get('fault_type')
        if not fault_type:
            fault_type = self._diagnose_fault(fft_result, envelope)
        
        # Combine results
        result = {
            'asset_id': asset_id,
            'fft_peaks': fft_result.get('peaks', []),
            'envelope_analysis': envelope,
            'iso_assessment': iso_check,
            'fault_type': fault_type,
            'severity': iso_check.get('severity', 'Unknown'),
            'confidence': 1.0,
            **extra_metrics
        }
        
        return result
    
    def _find_csv(self, filename: str) -> Optional[str]:
        """Find the CSV file in the workspace or parent directories with absolute paths."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        paths_to_try = [
            os.path.join(base_dir, "backend", "data", "vibration", filename),
            os.path.join(os.getcwd(), "backend", "data", "vibration", filename),
            os.path.join(self.data_dir, filename),
            filename
        ]
        for path in paths_to_try:
            if os.path.exists(path):
                return path
        return None

    def _load_real_data(self, asset_id: str, query: Optional[str] = None) -> Dict:
        """
        Load real sensor/predictive maintenance data matching the asset type and query context.
        All datasets share the identical schema after standardization.
        """
        cache_key = (asset_id, query)
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        is_faulty = False
        if query:
            q_lower = query.lower()
            fault_keywords = ['vibrat', 'shak', 'loud', 'fail', 'incident', 'wrong', 'damage', 'broken', 'issue', 'anomaly', 'fault', 'leak', 'hot', 'heat']
            if any(kw in q_lower for kw in fault_keywords):
                is_faulty = True

        asset_lower = asset_id.lower()
        
        # 1. Routing by Asset Class
        if 'pump' in asset_lower or asset_lower.startswith('p-') or asset_lower.startswith('pmp-'):
            filename = "Large_Industrial_Pump_Maintenance_Dataset.csv"
            # Map query to P-1 to P-5
            digits = re.findall(r'\d+', asset_id)
            num = (int(digits[0]) % 5) + 1 if digits else 1
            asset_id_lookup = f"P-{num}"
        elif 'sensor' in asset_lower or re.match(r'^s-?\d+', asset_lower):
            filename = "iot_equipment_monitoring_dataset.csv"
            digits = re.findall(r'\d+', asset_id)
            num = digits[0] if digits else "151"
            asset_id_lookup = f"S{num}"
        elif 'turbine' in asset_lower or asset_lower.startswith('t-') or 'tur-' in asset_lower:
            filename = "equipment_anomaly_data.csv"
            digits = re.findall(r'\d+', asset_id)
            num = (int(digits[0]) % 5) + 1 if digits else 1
            asset_id_lookup = f"TUR-{num}"
        elif 'compressor' in asset_lower or asset_lower.startswith('c-') or 'com-' in asset_lower:
            filename = "equipment_anomaly_data.csv"
            digits = re.findall(r'\d+', asset_id)
            num = (int(digits[0]) % 5) + 1 if digits else 1
            asset_id_lookup = f"COM-{num}"
        else:
            # Fallback to CNC Tool (AI4I dataset)
            filename = "ai4i2020.csv"
            # AI4I asset_id are like L47181, M14860
            asset_id_lookup = asset_id.strip().upper()
            
        csv_path = self._find_csv(filename)
        if not csv_path:
            raise FileNotFoundError(f"Could not locate database file {filename} in {self.data_dir}")
            
        try:
            df = pd.read_csv(csv_path)
            
            # Filter by standardized asset ID
            filtered = df[df['asset_id'].str.upper() == asset_id_lookup.upper()]
            if len(filtered) == 0:
                filtered = df
                
            # Filter by fault status
            if is_faulty:
                sub = filtered[filtered['fault_status'] == 1]
                if len(sub) == 0:
                    sub = filtered
            else:
                sub = filtered[filtered['fault_status'] == 0]
                if len(sub) == 0:
                    sub = filtered
                    
            # Deterministic row selection
            h = int(hashlib.md5((asset_id + str(is_faulty)).encode()).hexdigest(), 16)
            row_idx = h % len(sub)
            row = sub.iloc[row_idx]
            
            # Map standard columns
            vibration_val = float(row['vibration'])
            rpm_val = float(row['rpm'])
            m_flag = int(row['fault_status'])
            f_type = str(row['fault_type'])
            
            metrics = {
                'temperature': float(row['temperature']),
                'pressure': float(row['pressure']) if pd.notnull(row['pressure']) else 0.0,
                'voltage': float(row['voltage']) if pd.notnull(row['voltage']) else 0.0,
                'current': float(row['current']) if pd.notnull(row['current']) else 0.0,
                'rpm': rpm_val if pd.notnull(rpm_val) else 1500.0,
                'torque': float(row['torque']) if pd.notnull(row['torque']) else 0.0,
                'tool_wear': float(row['tool_wear']) if pd.notnull(row['tool_wear']) else 0.0,
                'maintenance_flag': m_flag,
                'vibration_rms': vibration_val,
                'source_dataset': str(row['source_dataset']),
                'fault_type': f_type if f_type != "nan" else "None",
                'Normalized_Temp': float(row['Normalized_Temp']),
                'Normalized_Vibration': float(row['Normalized_Vibration']),
                'Normalized_Pressure': float(row['Normalized_Pressure']),
                'Normalized_Voltage': float(row['Normalized_Voltage']),
                'Normalized_Current': float(row['Normalized_Current']),
                'FFT_Feature1': float(row['FFT_Feature1']),
                'FFT_Feature2': float(row['FFT_Feature2']),
                'anomaly_score': float(row['Anomaly_Score'])
            }
            
            # Set recommendation based on standardized fault type
            recommendation = "Normal parameters"
            if m_flag == 1:
                f_type_lower = f_type.lower()
                if "bearing" in f_type_lower:
                    recommendation = "Inspect and replace bearing inner race within 24 hours."
                elif "power" in f_type_lower or "electrical" in f_type_lower:
                    recommendation = "Check voltage and current parameters immediately."
                elif "heat" in f_type_lower or "dissipation" in f_type_lower:
                    recommendation = "Inspect cooling system and heat dissipation immediately."
                elif "tool" in f_type_lower or "wear" in f_type_lower:
                    recommendation = "Replace milling tool head/bit immediately."
                else:
                    recommendation = "Perform diagnostics and verify sensor calibration."
                    
            metrics['recommendation'] = recommendation
            
            # Generate vibration waveforms using target RMS and RPM
            time_series_df = self._generate_conditioned_vibration(vibration_val, metrics['rpm'], m_flag == 1, asset_id=asset_id)
            ret_val = {'df': time_series_df, 'metrics': metrics}
            self._cache[cache_key] = ret_val
            return ret_val
            
        except Exception as e:
            print(f"[ERROR] Failed to process asset {asset_id} in {filename}: {e}")
            raise e

    def _generate_conditioned_vibration(self, target_rms: float, rpm: float, is_faulty: bool, asset_id: str = "P-1") -> pd.DataFrame:
        """
        Generate a high-frequency vibration signal conditioned on RMS and speed (RPM),
        loading from real_waveform.csv if matches exist.
        """
        fs = self.SAMPLING_FREQUENCY_HZ
        duration = self.DURATION_SEC
        t = np.linspace(0, duration, int(fs * duration))
        
        # Try reading real vibration waveform CSV
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        real_csv_path = os.path.join(base_dir, "backend", "data", "vibration", "real_waveform.csv")
        
        real_signal = None
        if os.path.exists(real_csv_path):
            try:
                # Match asset_id lookup format e.g. "P-1"
                lookup_id = asset_id
                if "pump" in asset_id.lower() or asset_id.startswith("P-"):
                    import re
                    digits = re.findall(r'\d+', asset_id)
                    num = (int(digits[0]) % 5) + 1 if digits else 1
                    lookup_id = f"P-{num}"
                    
                df_real = pd.read_csv(real_csv_path)
                df_filtered = df_real[df_real['asset_id'].str.upper() == lookup_id.upper()]
                if not df_filtered.empty:
                    real_vals = df_filtered['vibration_value'].values
                    # Replicate/tile the values to cover the duration
                    repeats = int(np.ceil((fs * duration) / len(real_vals)))
                    real_signal = np.tile(real_vals, repeats)[:int(fs * duration)]
            except Exception as e:
                print(f"[WARNING] Failed to load real_waveform.csv: {e}")
                
        if real_signal is not None:
            signal_data = real_signal
        else:
            speed_freq = max(self.MIN_SPEED_FREQ_HZ, rpm / self.RPM_TO_HZ_CONVERSION)
            signal_data = np.sin(2 * np.pi * speed_freq * t)
            if is_faulty:
                signal_data += self.BEARING_DEFECT_AMPLITUDE * np.sin(2 * np.pi * (self.BEARING_DEFECT_FACTOR * speed_freq) * t)
                signal_data += self.MISALIGNMENT_AMPLITUDE * np.sin(2 * np.pi * (self.MISALIGNMENT_FACTOR * speed_freq) * t)
        
        # Scale to match target RMS exactly
        current_rms = np.sqrt(np.mean(signal_data ** 2))
        if current_rms > 0:
            signal_data = signal_data * (target_rms / current_rms)
            
        # Add tiny bit of background white noise
        noise = self.NOISE_LEVEL * target_rms * np.random.randn(len(t))
        signal_data += noise
        
        # Final rescaling to ensure exact RMS match
        final_rms = np.sqrt(np.mean(signal_data ** 2))
        if final_rms > 0:
            signal_data = signal_data * (target_rms / final_rms)
            
        return pd.DataFrame({
            'time': t,
            'vibration': signal_data
        })
    def _run_fft(self, df: pd.DataFrame) -> Dict:
        """Run Fast Fourier Transform on vibration data"""
        if 'vibration' not in df.columns:
            return {'peaks': []}
        
        # FFT
    def _run_fft(self, df: pd.DataFrame) -> Dict:
        """Run Fast Fourier Transform on vibration data"""
        if 'vibration' not in df.columns:
            return {'peaks': []}
        
        # FFT
        fs = self.SAMPLING_FREQUENCY_HZ
        f, Pxx = signal.periodogram(df['vibration'].values, fs)
        
        # Find peaks
        peaks = []
        from scipy.signal import find_peaks
        peak_indices, _ = find_peaks(Pxx, height=self.PEAK_HEIGHT_THRESHOLD)
        
        for idx in peak_indices:
            if Pxx[idx] > self.PEAK_HEIGHT_THRESHOLD:
                peaks.append({
                    'frequency': f[idx],
                    'magnitude': float(Pxx[idx])
                })
        
        # Sort by magnitude
        peaks.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return {
            'peaks': peaks[:self.MAX_PEAKS_RETURNED],
            'max_frequency': float(f[np.argmax(Pxx)]),
            'max_magnitude': float(np.max(Pxx))
        }
    
    def _run_envelope_analysis(self, df: pd.DataFrame) -> Dict:
        """Run envelope analysis for bearing fault detection"""
        if 'vibration' not in df.columns:
            return {'fault_detected': False}
        
        # Simple envelope detection (Hilbert transform)
        from scipy.signal import hilbert
        analytic_signal = hilbert(df['vibration'].values)
        amplitude_envelope = np.abs(analytic_signal)
        
        # Check for modulation (bearing fault indicator)
        envelope_std = np.std(amplitude_envelope)
        signal_std = np.std(df['vibration'].values)
        
        modulation_ratio = envelope_std / signal_std if signal_std > 0 else 0
        
        return {
            'fault_detected': modulation_ratio > self.MODULATION_RATIO_THRESHOLD,
            'modulation_ratio': float(modulation_ratio),
            'envelope_energy': float(np.sum(amplitude_envelope))
        }
    
    def _check_iso_standard(self, df: pd.DataFrame) -> Dict:
        """
        Check vibration against ISO 10816-3 standards.
        """
        # Calculate RMS velocity
        if 'vibration' not in df.columns:
            return {'severity': 'Unknown', 'zone': 'Unknown'}
        
        rms = np.sqrt(np.mean(df['vibration'].values ** 2))
        
        # ISO 10816-3 thresholds for medium machines
        # Zone A: Good, Zone B: Satisfactory, Zone C: Alert, Zone D: Critical
        if rms < self.ISO_ZONE_A_LIMIT:
            severity = 'Normal'
            zone = 'A'
        elif rms < self.ISO_ZONE_B_LIMIT:
            severity = 'Warning'
            zone = 'B'
        elif rms < self.ISO_ZONE_C_LIMIT:
            severity = 'Alert'
            zone = 'C'
        else:
            severity = 'Critical'
            zone = 'D'
        
        return {
            'rms_velocity': float(rms),
            'severity': severity,
            'zone': zone,
            'standard': 'ISO 10816-3'
        }
    
    def _diagnose_fault(self, fft_result: Dict, envelope: Dict) -> str:
        """
        Diagnose fault type from FFT and envelope analysis.
        """
        if envelope.get('fault_detected', False):
            return 'Inner Race Bearing Fault (BPI)'
        
        if fft_result.get('peaks') and len(fft_result['peaks']) > 0:
            max_freq = fft_result['peaks'][0]['frequency']
            # Check if peak is at 2x running speed (misalignment)
            if self.MISALIGNMENT_MIN_FREQ < max_freq < self.MISALIGNMENT_MAX_FREQ:
                return 'Misalignment'
        
        return 'No significant fault detected'
