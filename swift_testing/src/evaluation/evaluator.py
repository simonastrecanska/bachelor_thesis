"""
Evaluation Module

This module evaluates the performance of SWIFT message routing models.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from sklearn.calibration import calibration_curve

logger = logging.getLogger(__name__)

def format_value(value: Any) -> Any:
    """
    Convert any value to a JSON-serializable representation.

    Args:
        value: Any type of value that needs formatting for output (JSON, CSV, etc.)

    Returns:
        JSON-serializable representation of the value.
    """
    if isinstance(value, tuple):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.float64, np.float32)):
        return float(value)
    return value


class ModelEvaluator:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the evaluator with a given configuration.
        
        Args:
            config: A dictionary specifying which metrics to compute,
                    what output formats to generate, and how to plot.
        """
        self.config = config
        self.metrics = config.get('metrics', ['accuracy', 'precision', 'recall', 'f1'])
        self.output_formats = config.get('output_format', ['csv', 'json'])
        self.plot_config = config.get('plot', {})

    def calculate_metrics(
        self,
        true_labels: List[str],
        predicted_labels: List[str],
        confidences: Optional[List[float]] = None
    ) -> Dict[str, float]:
        """
        Calculate evaluation metrics for model predictions.

        Args:
            true_labels: A list of ground-truth labels (strings).
            predicted_labels: A list of model-predicted labels (strings).
            confidences: Optional list of float confidence scores for each prediction.

        Returns:
            A dictionary of metric names and values, or an 'error' key if an issue arises.
        """
        if not true_labels or not predicted_labels:
            logger.warning("Empty label lists provided to calculate_metrics.")
            return {"error": "Empty label lists"}

        if len(true_labels) != len(predicted_labels):
            logger.error(f"Label list length mismatch: {len(true_labels)} true vs {len(predicted_labels)} predicted.")
            return {"error": "Label list length mismatch"}

        if confidences and len(confidences) != len(true_labels):
            logger.error(f"Confidence list length ({len(confidences)}) doesn't match labels ({len(true_labels)}).")
            return {"error": "Confidence list length mismatch"}

        metrics = {}
        try:
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

            metrics['correct_count'] = sum(t == p for t, p in zip(true_labels, predicted_labels))
            metrics['total_count'] = len(true_labels)

            if confidences:
                metrics['avg_confidence'] = float(np.mean(confidences))

                correct_indices = [
                    i for i, (t, p) in enumerate(zip(true_labels, predicted_labels)) if t == p
                ]
                if correct_indices:
                    metrics['avg_confidence_correct'] = float(
                        np.mean([confidences[i] for i in correct_indices])
                    )

                incorrect_indices = [
                    i for i, (t, p) in enumerate(zip(true_labels, predicted_labels)) if t != p
                ]
                if incorrect_indices:
                    metrics['avg_confidence_incorrect'] = float(
                        np.mean([confidences[i] for i in incorrect_indices])
                    )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {"error": f"Metric calculation failed: {str(e)}"}

    def generate_confusion_matrix(
        self,
        true_labels: List[str],
        predicted_labels: List[str],
        output_dir: str,
        prefix: str = ""
    ) -> Optional[str]:
        """
        Generate a confusion matrix plot and save it to disk.

        Args:
            true_labels: Ground-truth labels.
            predicted_labels: Predicted labels from the model.
            output_dir: Directory to save the plot.
            prefix: Optional prefix for the output filename.

        Returns:
            The filepath to the saved plot, or None if generation fails.
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            unique_labels = sorted(list(set(true_labels + predicted_labels)))
            if not unique_labels:
                logger.warning("No unique labels found for confusion matrix.")
                return None

            cm = confusion_matrix(true_labels, predicted_labels, labels=unique_labels)

            plt.figure(figsize=(
                self.plot_config.get('width', 10),
                self.plot_config.get('height', 8)
            ))

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
            filepath = str(output_path / filename)
            plt.savefig(filepath, dpi=self.plot_config.get('dpi', 300))
            plt.close()

            logger.info(f"Confusion matrix saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating confusion matrix: {str(e)}")
            return None

    def generate_metrics_plot(
        self,
        metrics: Dict[str, float],
        output_dir: str,
        prefix: str = ""
    ) -> Optional[str]:
        """
        Generate a bar chart of the computed metrics and save to disk.

        Args:
            metrics: A dictionary of metric names to values (floats).
            output_dir: Directory to save the plot.
            prefix: Optional prefix for the output filename.

        Returns:
            The filepath to the saved plot, or None if generation fails.
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            excluded_metrics = ['total_count', 'correct_count', 'error']
            plot_metrics = {
                k: v for k, v in metrics.items()
                if isinstance(v, (int, float)) and k not in excluded_metrics
            }

            if not plot_metrics:
                logger.warning("No numeric metrics available to plot.")
                return None

            plt.figure(figsize=(
                self.plot_config.get('width', 10),
                self.plot_config.get('height', 6)
            ))

            plt.bar(plot_metrics.keys(), plot_metrics.values())
            plt.title('Model Performance Metrics')
            plt.ylim(0, 1.1)

            for i, (k, v) in enumerate(plot_metrics.items()):
                plt.text(i, v + 0.02, f'{v:.3f}', ha='center')

            plt.tight_layout()

            filename = f"{prefix}metrics.{self.plot_config.get('save_format', 'png')}"
            filepath = str(output_path / filename)
            plt.savefig(filepath, dpi=self.plot_config.get('dpi', 300))
            plt.close()

            logger.info(f"Metrics plot saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating metrics plot: {str(e)}")
            return None

    def save_results(
        self,
        metrics: Dict[str, float],
        true_labels: List[str],
        predicted_labels: List[str],
        confidences: Optional[List[float]] = None,
        output_dir: str = ".",
        prefix: str = ""
    ) -> Dict[str, str]:
        """
        Save evaluation results (metrics, predictions, classification report) in multiple formats.

        Args:
            metrics: A dictionary of computed metrics.
            true_labels: Ground-truth labels.
            predicted_labels: Model-predicted labels.
            confidences: Optional list of model confidence scores.
            output_dir: Where to store the outputs.
            prefix: Optional prefix for filename(s).

        Returns:
            A dictionary mapping each output format to the filepath(s) generated.
        """
        output_files = {}
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

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
                try:
                    metrics_file = str(output_path / f"{prefix}metrics.csv")
                    pd.DataFrame([metrics]).to_csv(metrics_file, index=False)
                    output_files['metrics_csv'] = metrics_file

                    predictions_file = str(output_path / f"{prefix}predictions.csv")
                    results_df.to_csv(predictions_file, index=False)
                    output_files['predictions_csv'] = predictions_file

                    report = classification_report(true_labels, predicted_labels, output_dict=True)
                    report_df = pd.DataFrame(report).transpose()
                    report_file = str(output_path / f"{prefix}classification_report.csv")
                    report_df.to_csv(report_file)
                    output_files['report_csv'] = report_file

                    logger.info(f"Results saved to CSV in {output_dir}")

                except Exception as e:
                    logger.error(f"Error saving CSV outputs: {str(e)}")

            if 'json' in self.output_formats:
                try:
                    json_results_data = {
                        'true_label': true_labels,
                        'predicted_label': predicted_labels,
                        'correct': [t == p for t, p in zip(true_labels, predicted_labels)]
                    }
                    if confidences:
                        json_results_data['confidence'] = [float(c) for c in confidences]

                    json_data = {
                        'metrics': metrics,
                        'predictions': json_results_data,
                        'classification_report': classification_report(
                            true_labels, predicted_labels, output_dict=True
                        )
                    }

                    json_file = str(output_path / f"{prefix}results.json")
                    with open(json_file, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    output_files['json'] = json_file

                    logger.info(f"Results saved to JSON file: {json_file}")

                except Exception as e:
                    logger.error(f"Error saving JSON outputs: {str(e)}")

            if 'plot' in self.output_formats:
                cm_file = self.generate_confusion_matrix(true_labels, predicted_labels, output_dir, prefix)
                if cm_file:
                    output_files['confusion_matrix'] = cm_file

                metrics_plot_file = self.generate_metrics_plot(metrics, output_dir, prefix)
                if metrics_plot_file:
                    output_files['metrics_plot'] = metrics_plot_file

            return output_files

        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return {"error": str(e)}

    def evaluate(
        self,
        true_labels: List[str],
        predicted_labels: List[str],
        confidences: Optional[List[float]] = None,
        output_dir: str = ".",
        prefix: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate model performance end-to-end: compute metrics, generate plots, and save outputs.

        Args:
            true_labels: Ground-truth labels
            predicted_labels: Predicted labels from the model
            confidences: Optional list of model confidence scores
            output_dir: Directory for saving results
            prefix: Optional filename prefix for saved files

        Returns:
            A dict with keys:
                - 'metrics': the computed metrics dictionary
                - 'output_files': dict of filepaths to generated outputs
        """
        try:
            metrics = self.calculate_metrics(true_labels, predicted_labels, confidences)
            if "error" in metrics:
                logger.error(f"Evaluation failed: {metrics['error']}")
                return {"error": metrics["error"]}

            logger.info(f"Evaluation metrics: {metrics}")

            output_files = self.save_results(
                metrics, true_labels, predicted_labels, confidences, output_dir, prefix
            )
            return {
                'metrics': metrics,
                'output_files': output_files
            }
        except Exception as e:
            logger.error(f"Error in evaluation: {str(e)}")
            return {"error": str(e)}


def create_evaluator(config: Dict[str, Any]) -> ModelEvaluator:
    """
    Helper function to create a ModelEvaluator with a given config.

    Args:
        config: A dictionary specifying metrics to compute, output formats, and plot options.

    Returns:
        An instance of ModelEvaluator.
    """
    return ModelEvaluator(config)