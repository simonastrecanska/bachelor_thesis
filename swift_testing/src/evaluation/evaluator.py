"""
Evaluation Module

This module evaluates the performance of SWIFT message routing models.
"""

import logging
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

logger = logging.getLogger(__name__)

def format_value(value):
    """Convert any value to its proper string representation."""
    if isinstance(value, tuple):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.float64) or isinstance(value, np.float32):
        return float(value)
    return value

class ModelEvaluator:
    """Evaluator for SWIFT message routing models."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the evaluator.
        
        Args:
            config: Evaluation configuration
        """
        self.config = config
        self.metrics = config.get('metrics', ['accuracy', 'precision', 'recall', 'f1'])
        self.output_formats = config.get('output_format', ['csv', 'json'])
        self.plot_config = config.get('plot', {})
        self.cross_validation = config.get('cross_validation', {'enabled': False})
    
    def calculate_metrics(self, 
                          true_labels: List[str], 
                          predicted_labels: List[str],
                          confidences: Optional[List[float]] = None) -> Dict[str, float]:
        """
        Calculate evaluation metrics.
        
        Args:
            true_labels: List of true labels
            predicted_labels: List of predicted labels
            confidences: Optional list of confidence scores
            
        Returns:
            Dictionary of metric names and values
        """
        metrics = {}
        
        if 'accuracy' in self.metrics:
            metrics['accuracy'] = accuracy_score(true_labels, predicted_labels)
        
        if 'precision' in self.metrics:
            metrics['precision'] = precision_score(
                true_labels, predicted_labels, average='weighted', zero_division=0
            )
        
        if 'recall' in self.metrics:
            metrics['recall'] = recall_score(
                true_labels, predicted_labels, average='weighted', zero_division=0
            )
        
        if 'f1' in self.metrics:
            metrics['f1'] = f1_score(
                true_labels, predicted_labels, average='weighted', zero_division=0
            )
        
        if confidences:
            metrics['avg_confidence'] = np.mean(confidences)
        
        return metrics
    
    def generate_confusion_matrix(self, 
                                  true_labels: List[str], 
                                  predicted_labels: List[str],
                                  output_dir: str,
                                  prefix: str = "") -> str:
        """
        Generate confusion matrix and save as plot.
        
        Args:
            true_labels: List of true labels
            predicted_labels: List of predicted labels
            output_dir: Directory to save the plot
            prefix: Optional prefix for the filename
            
        Returns:
            Path to the saved plot
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        unique_labels = sorted(list(set(true_labels + predicted_labels)))
        
        cm = confusion_matrix(true_labels, predicted_labels, labels=unique_labels)
        
        plt.figure(
            figsize=(
                self.plot_config.get('width', 10),
                self.plot_config.get('height', 8)
            )
        )
        
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title('Confusion Matrix')
        plt.colorbar()
        
        tick_marks = np.arange(len(unique_labels))
        plt.xticks(tick_marks, unique_labels, rotation=45)
        plt.yticks(tick_marks, unique_labels)
        
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(j, i, format(cm[i, j], 'd'),
                         ha="center", va="center",
                         color="white" if cm[i, j] > thresh else "black")
        
        plt.tight_layout()
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        filename = f"{prefix}confusion_matrix.{self.plot_config.get('save_format', 'png')}"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=self.plot_config.get('dpi', 300))
        plt.close()
        
        logger.info(f"Confusion matrix saved to {filepath}")
        return filepath
    
    def generate_metrics_plot(self, 
                             metrics: Dict[str, float],
                             output_dir: str,
                             prefix: str = "") -> str:
        """
        Generate metrics plot and save.
        
        Args:
            metrics: Dictionary of metrics
            output_dir: Directory to save the plot
            prefix: Optional prefix for the filename
            
        Returns:
            Path to the saved plot
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plot_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
        
        plt.figure(
            figsize=(
                self.plot_config.get('width', 10),
                self.plot_config.get('height', 6)
            )
        )
        
        plt.bar(plot_metrics.keys(), plot_metrics.values())
        plt.title('Model Performance Metrics')
        plt.ylim(0, 1.1)
        
        for i, (k, v) in enumerate(plot_metrics.items()):
            plt.text(i, v + 0.02, f'{v:.2f}', ha='center')
        
        plt.tight_layout()
        
        filename = f"{prefix}metrics.{self.plot_config.get('save_format', 'png')}"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=self.plot_config.get('dpi', 300))
        plt.close()
        
        logger.info(f"Metrics plot saved to {filepath}")
        return filepath
    
    def save_results(self, 
                    metrics: Dict[str, float],
                    true_labels: List[str],
                    predicted_labels: List[str],
                    confidences: Optional[List[float]] = None,
                    output_dir: str = ".",
                    prefix: str = "") -> Dict[str, str]:
        """
        Save evaluation results in specified formats.
        
        Args:
            metrics: Dictionary of metrics
            true_labels: List of true labels
            predicted_labels: List of predicted labels
            confidences: Optional list of confidence scores
            output_dir: Directory to save results
            prefix: Optional prefix for filenames
            
        Returns:
            Dictionary of output file paths
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_files = {}
        
        metrics = {k: format_value(v) for k, v in metrics.items()}
        
        results_data = {
            'true_label': true_labels,
            'predicted_label': predicted_labels,
            'correct': [t == p for t, p in zip(true_labels, predicted_labels)]
        }
        
        if confidences:
            results_data['confidence'] = confidences
        
        results_df = pd.DataFrame(results_data)
        
        if 'csv' in self.output_formats:
            metrics_file = os.path.join(output_dir, f"{prefix}metrics.csv")
            pd.DataFrame([metrics]).to_csv(metrics_file, index=False)
            output_files['metrics_csv'] = metrics_file
            
            predictions_file = os.path.join(output_dir, f"{prefix}predictions.csv")
            results_df.to_csv(predictions_file, index=False)
            output_files['predictions_csv'] = predictions_file
            
            report = classification_report(true_labels, predicted_labels, output_dict=True)
            report_df = pd.DataFrame(report).transpose()
            report_file = os.path.join(output_dir, f"{prefix}classification_report.csv")
            report_df.to_csv(report_file)
            output_files['report_csv'] = report_file
            
            logger.info(f"Results saved to CSV files in {output_dir}")
        
        if 'json' in self.output_formats:
            json_data = {
                'metrics': metrics,
                'predictions': results_data,
                'classification_report': classification_report(
                    true_labels, predicted_labels, output_dict=True
                )
            }
            
            json_file = os.path.join(output_dir, f"{prefix}results.json")
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            output_files['json'] = json_file
            logger.info(f"Results saved to JSON file: {json_file}")
        
        if 'plot' in self.output_formats:
            cm_file = self.generate_confusion_matrix(
                true_labels, predicted_labels, output_dir, prefix
            )
            output_files['confusion_matrix'] = cm_file
            
            metrics_plot = self.generate_metrics_plot(metrics, output_dir, prefix)
            output_files['metrics_plot'] = metrics_plot
        
        return output_files
    
    def evaluate(self, 
                true_labels: List[str],
                predicted_labels: List[str],
                confidences: Optional[List[float]] = None,
                output_dir: str = ".",
                prefix: str = "") -> Dict[str, Any]:
        """
        Evaluate model performance and save results.
        
        Args:
            true_labels: List of true labels
            predicted_labels: List of predicted labels
            confidences: Optional list of confidence scores
            output_dir: Directory to save results
            prefix: Optional prefix for filenames
            
        Returns:
            Dictionary with metrics and file paths
        """
        metrics = self.calculate_metrics(true_labels, predicted_labels, confidences)
        logger.info(f"Evaluation metrics: {metrics}")
        
        output_files = self.save_results(
            metrics, true_labels, predicted_labels, confidences, output_dir, prefix
        )
        
        return {
            'metrics': metrics,
            'output_files': output_files
        }


def create_evaluator(config: Dict[str, Any]) -> ModelEvaluator:
    """
    Helper function to create an evaluator.
    
    Args:
        config: Evaluation configuration
        
    Returns:
        ModelEvaluator instance
    """
    return ModelEvaluator(config) 