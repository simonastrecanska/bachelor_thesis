"""
Routing Model Module

This module provides a simple implementation of a SWIFT message routing model.
"""

import re
import logging
import pickle
import os
import random
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.base import BaseEstimator

logger = logging.getLogger(__name__)


class SwiftMessageRouter:
    """Base class for SWIFT message routing models."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the routing model.
        
        Args:
            config: Model configuration
        """
        self.config = config
        self.version = config.get('version', '1.0.0')
        self.threshold = config.get('prediction_threshold', 0.5)
        self.model = None
        self.vectorizer = None
    
    def preprocess(self, message: str) -> str:
        """
        Preprocess a SWIFT message.
        
        Args:
            message: Raw message text
            
        Returns:
            Preprocessed message text
        """
        processed = re.sub(r'\s+', ' ', message.strip())
        processed = processed.upper()
        return processed
    
    def extract_features(self, messages: List[str]) -> np.ndarray:
        """
        Extract features from messages.
        
        Args:
            messages: List of message texts
            
        Returns:
            Feature matrix
        """
        if self.vectorizer is None:
            feature_config = self.config.get('feature_extraction', {})
            vectorizer_type = feature_config.get('vectorizer', 'tfidf')
            max_features = feature_config.get('max_features', 1000)
            ngram_range = feature_config.get('ngram_range', (1, 3))
            
            if isinstance(ngram_range, list) and len(ngram_range) == 2:
                ngram_range = tuple(ngram_range)
            
            if vectorizer_type == 'tfidf':
                self.vectorizer = TfidfVectorizer(
                    max_features=max_features,
                    ngram_range=ngram_range,
                    analyzer='char_wb'
                )
            else:
                self.vectorizer = CountVectorizer(
                    max_features=max_features,
                    ngram_range=ngram_range,
                    analyzer='char_wb'
                )
        
        processed_messages = [self.preprocess(msg) for msg in messages]
        
        if not hasattr(self.vectorizer, 'vocabulary_'):
            return self.vectorizer.fit_transform(processed_messages)
        
        return self.vectorizer.transform(processed_messages)
    
    def train(self, messages: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Train the routing model.
        
        Args:
            messages: List of message texts
            labels: List of corresponding labels
            
        Returns:
            Dictionary of training metrics
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def predict(self, message: str) -> Tuple[str, float]:
        """
        Predict the routing for a message.
        
        Args:
            message: Message text
            
        Returns:
            Tuple of (predicted label, confidence score)
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def evaluate(self, messages: List[str], true_labels: List[str]) -> Dict[str, float]:
        """
        Evaluate the model on test data.
        
        Args:
            messages: List of message texts
            true_labels: List of true labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        predictions = []
        confidences = []
        
        for message in messages:
            label, confidence = self.predict(message)
            predictions.append(label)
            confidences.append(confidence)
        
        metrics = {
            'accuracy': accuracy_score(true_labels, predictions),
            'precision': precision_score(true_labels, predictions, average='weighted'),
            'recall': recall_score(true_labels, predictions, average='weighted'),
            'f1': f1_score(true_labels, predictions, average='weighted')
        }
        
        return metrics
    
    def save(self, filepath: str) -> None:
        """
        Save the model to disk.
        
        Args:
            filepath: Path to save the model
        """
        model_data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'version': self.version,
            'threshold': self.threshold,
            'config': self.config
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'SwiftMessageRouter':
        """
        Load a model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded model instance
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        instance = cls(model_data['config'])
        instance.model = model_data['model']
        instance.vectorizer = model_data['vectorizer']
        instance.version = model_data['version']
        instance.threshold = model_data['threshold']
        
        logger.info(f"Model loaded from {filepath}")
        return instance


class RandomForestRouter(SwiftMessageRouter):
    """Random Forest implementation of the SWIFT message router."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Random Forest router.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        model_params = self.config.get('model_params', {})
        n_estimators = model_params.get('n_estimators', 100)
        max_depth = model_params.get('max_depth', 10)
        random_state = model_params.get('random_state', 42)
        
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )
    
    def train(self, messages: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Train the Random Forest model.
        
        Args:
            messages: List of message texts
            labels: List of corresponding labels
            
        Returns:
            Dictionary of training metrics
        """
        X = self.extract_features(messages)
        y = np.array(labels)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        val_predictions = self.model.predict(X_val)
        
        metrics = {
            'accuracy': accuracy_score(y_val, val_predictions),
            'precision': precision_score(y_val, val_predictions, average='weighted'),
            'recall': recall_score(y_val, val_predictions, average='weighted'),
            'f1': f1_score(y_val, val_predictions, average='weighted')
        }
        
        logger.info(f"Model trained with validation metrics: {metrics}")
        return metrics
    
    def predict(self, message: str) -> Tuple[str, float]:
        """
        Predict the routing for a message.
        
        Args:
            message: Message text
            
        Returns:
            Tuple of (predicted label, confidence score)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        processed = self.preprocess(message)
        X = self.extract_features([processed])
        
        proba = self.model.predict_proba(X)[0]
        
        class_idx = np.argmax(proba)
        confidence = proba[class_idx]
        predicted_label = self.model.classes_[class_idx]
        
        return predicted_label, float(confidence)


class SVMRouter(SwiftMessageRouter):
    """SVM implementation of the SWIFT message router."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SVM router.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        model_params = self.config.get('model_params', {})
        C = model_params.get('C', 1.0)
        kernel = model_params.get('kernel', 'linear')
        probability = True 
        random_state = model_params.get('random_state', 42)
        
        self.model = SVC(
            C=C,
            kernel=kernel,
            probability=probability,
            random_state=random_state
        )
    
    def train(self, messages: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Train the SVM model.
        
        Args:
            messages: List of message texts
            labels: List of corresponding labels
            
        Returns:
            Dictionary of training metrics
        """
        X = self.extract_features(messages)
        y = np.array(labels)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        val_predictions = self.model.predict(X_val)
        
        metrics = {
            'accuracy': accuracy_score(y_val, val_predictions),
            'precision': precision_score(y_val, val_predictions, average='weighted'),
            'recall': recall_score(y_val, val_predictions, average='weighted'),
            'f1': f1_score(y_val, val_predictions, average='weighted')
        }
        
        logger.info(f"Model trained with validation metrics: {metrics}")
        return metrics
    
    def predict(self, message: str) -> Tuple[str, float]:
        """
        Predict the routing for a message.
        
        Args:
            message: Message text
            
        Returns:
            Tuple of (predicted label, confidence score)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        processed = self.preprocess(message)
        X = self.extract_features([processed])
        
        proba = self.model.predict_proba(X)[0]
        
        class_idx = np.argmax(proba)
        confidence = proba[class_idx]
        predicted_label = self.model.classes_[class_idx]
        
        return predicted_label, float(confidence)


class NaiveBayesRouter(SwiftMessageRouter):
    """Naive Bayes implementation of the SWIFT message router."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Naive Bayes router.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        model_params = self.config.get('model_params', {})
        alpha = model_params.get('alpha', 1.0)
        
        self.model = MultinomialNB(alpha=alpha)
    
    def train(self, messages: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Train the Naive Bayes model.
        
        Args:
            messages: List of message texts
            labels: List of corresponding labels
            
        Returns:
            Dictionary of training metrics
        """
        X = self.extract_features(messages)
        y = np.array(labels)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        val_predictions = self.model.predict(X_val)
        
        metrics = {
            'accuracy': accuracy_score(y_val, val_predictions),
            'precision': precision_score(y_val, val_predictions, average='weighted'),
            'recall': recall_score(y_val, val_predictions, average='weighted'),
            'f1': f1_score(y_val, val_predictions, average='weighted')
        }
        
        logger.info(f"Model trained with validation metrics: {metrics}")
        return metrics
    
    def predict(self, message: str) -> Tuple[str, float]:
        """
        Predict the routing for a message.
        
        Args:
            message: Message text
            
        Returns:
            Tuple of (predicted label, confidence score)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        processed = self.preprocess(message)
        X = self.extract_features([processed])
        
        proba = self.model.predict_proba(X)[0]
        
        class_idx = np.argmax(proba)
        confidence = proba[class_idx]
        predicted_label = self.model.classes_[class_idx]
        
        return predicted_label, float(confidence)


class RuleBasedRouter(SwiftMessageRouter):
    """
    Rule-based implementation of the SWIFT message router.
    
    This is a simple rule-based model for demonstration purposes,
    using pattern matching instead of ML.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the rule-based router.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        self.rules = [
            {
                'pattern': r':23B:CRED',
                'label': 'Customer Transfer'
            },
            {
                'pattern': r':58A:|:58D:|Financial Institution',
                'label': 'Financial Institution Transfer'
            },
            {
                'pattern': r'Documentary Credit|Letter of Credit|:27:|:40A:',
                'label': 'Documentary Credit'
            },
            {
                'pattern': r'Fixed Loan|Deposit|:22A:NEWT',
                'label': 'Fixed Loan/Deposit'
            },
            {
                'pattern': r'Statement|:60F:|:62F:',
                'label': 'Statement'
            }
        ]
    
    def train(self, messages: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Train method for rule-based router (not used, but implemented for interface compatibility).
        
        Args:
            messages: List of message texts
            labels: List of corresponding labels
            
        Returns:
            Empty metrics dictionary
        """
        logger.info("Rule-based router doesn't require training")
        return {}
    
    def predict(self, message: str) -> Tuple[str, float]:
        """
        Predict the routing for a message using rules.
        
        Args:
            message: Message text
            
        Returns:
            Tuple of (predicted label, confidence score)
        """
        processed = self.preprocess(message)
        
        matched_rules = []
        
        for rule in self.rules:
            if re.search(rule['pattern'], processed, re.IGNORECASE):
                matched_rules.append(rule)
        
        if matched_rules:
            label = matched_rules[0]['label']
            confidence = 1.0
            return label, confidence
        else:
            return "Unknown", 0.0


def create_router(config: Dict[str, Any]) -> SwiftMessageRouter:
    """
    Factory function to create router based on config.
    
    Args:
        config: Model configuration
        
    Returns:
        SwiftMessageRouter instance
    """
    model_type = config.get('model_type', 'random_forest').lower()
    
    if model_type == 'random_forest':
        return RandomForestRouter(config)
    elif model_type == 'svm':
        return SVMRouter(config)
    elif model_type == 'naive_bayes':
        return NaiveBayesRouter(config)
    elif model_type == 'rule_based':
        return RuleBasedRouter(config)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def load_router(filepath: str) -> SwiftMessageRouter:
    """
    Load a router from a saved file.
    
    Args:
        filepath: Path to the saved model
        
    Returns:
        SwiftMessageRouter instance
    """
    with open(filepath, 'rb') as f:
        model_data = pickle.load(f)
    
    config = model_data.get('config', {})
    model_type = config.get('model_type', 'random_forest').lower()
    
    if model_type == 'random_forest':
        router = RandomForestRouter(config)
    elif model_type == 'svm':
        router = SVMRouter(config)
    elif model_type == 'naive_bayes':
        router = NaiveBayesRouter(config)
    elif model_type == 'rule_based':
        router = RuleBasedRouter(config)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    router.model = model_data.get('model')
    router.vectorizer = model_data.get('vectorizer')
    router.version = model_data.get('version', '1.0.0')
    router.threshold = model_data.get('threshold', 0.5)
    
    return router 