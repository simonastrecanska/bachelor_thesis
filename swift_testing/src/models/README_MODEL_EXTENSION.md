# Extending the SWIFT Message Routing Model

This document provides guidance on how to extend the bare-bones routing model for SWIFT messages.

## Overview

The `BareBonesRouter` in `routing_model.py` is designed as a starting point for implementing your own SWIFT message routing models. It provides a minimal working implementation that:

1. Recognizes message block codes (like `:20:`, `:50K:`, etc.)
2. Builds simple pattern-based rules during training
3. Makes basic predictions with confidence scores
4. Has clear TODOs where you should add your custom logic

## How to Extend the Model

### 1. Model Initialization

In the `__init__` method, you can add your custom model components:

```python
def __init__(self, config: Dict[str, Any]):
    super().__init__(config)
    # ... existing code ...
    
    # TODO: Initialize your custom model components here.
    self.classifier = None  # Add your ML model here
    self.embeddings = {}    # Add embeddings for messages
    self.features = []      # Define important features
```

### 2. Feature Extraction

You may want to enhance feature extraction to capture more patterns in SWIFT messages:

```python
def extract_custom_features(self, message: str) -> Dict[str, Any]:
    """Extract custom features from a message."""
    features = {}
    
    # Example: Detect currency codes
    currency_match = re.search(r'[A-Z]{3}[\d,.]+', message)
    if currency_match:
        features['has_currency'] = True
        features['currency_value'] = currency_match.group(0)
    
    # Add more feature extraction logic
    
    return features
```

### 3. Training Implementation

Enhance the training method to use more sophisticated algorithms:

```python
def train(self, messages: List[str], labels: List[str]) -> Dict[str, float]:
    # ... existing code ...
    
    # TODO: Add your custom training logic here
    # 1. Extract features from messages
    X = self.extract_features(messages)
    y = np.array(labels)
    
    # 2. Train a classifier on these features
    from sklearn.ensemble import RandomForestClassifier
    self.classifier = RandomForestClassifier(n_estimators=100)
    self.classifier.fit(X, y)
    
    # 3. Calculate and return training metrics
    from sklearn.metrics import accuracy_score
    y_pred = self.classifier.predict(X)
    return {
        "accuracy": accuracy_score(y, y_pred),
        # Add more metrics...
    }
```

### 4. Prediction Implementation

Enhance the prediction method to use your trained model:

```python
def predict(self, message: str) -> Tuple[str, float]:
    # ... existing code ...
    
    # TODO: Implement your custom prediction logic here
    # 1. Extract features from the input message
    X = self.extract_features([message])
    
    # 2. Apply your trained model to predict the label
    if self.classifier is not None:
        predicted_label = self.classifier.predict(X)[0]
        
        # 3. Calculate a confidence score
        confidence = np.max(self.classifier.predict_proba(X)[0])
        return predicted_label, confidence
    
    # ... existing fallback logic ...
```

## Advanced Extensions

### Adding Deep Learning

If you want to use deep learning:

```python
def __init__(self, config: Dict[str, Any]):
    # ... existing code ...
    
    # Import deep learning libraries inside the method to make them optional
    try:
        import tensorflow as tf
        self.use_deep_learning = True
        self.model = tf.keras.Sequential([
            # Define your model architecture
        ])
    except ImportError:
        logger.warning("TensorFlow not available, falling back to rule-based approach")
        self.use_deep_learning = False
```

### Adding NLP Processing

For more advanced text processing:

```python
def preprocess(self, message: str) -> str:
    processed = super().preprocess(message)
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(processed)
        
        # Extract entities, parts of speech, etc.
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        # Use these for feature extraction
        
    except ImportError:
        logger.warning("spaCy not available, using basic preprocessing only")
    
    return processed
```

## Testing Your Extended Model

After implementing your extensions:

1. Update the `config.yaml` file to specify your model type
2. Run the testing framework to evaluate your model:

```bash
python -m swift_testing.src.run_test --config swift_testing/config/config.yaml --name "My Extended Model Test" --train
```

## Common Patterns in SWIFT Messages

To help with your implementation, here are some common patterns to look for:

- `:20:` - Reference number
- `:23B:` - Bank operation code
- `:32A:` - Value date, currency, amount
- `:50K:` - Ordering customer
- `:59:` - Beneficiary
- `:70:` - Remittance information

Good luck with your implementation! 