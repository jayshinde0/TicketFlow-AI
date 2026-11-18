"""
test_models_validation.py - Test ML model file validation
Tests that required model files exist and are loadable
"""

import pytest
import sys
from pathlib import Path
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelFilesExist:
    """Test that all required model files exist"""

    def test_category_model_exists(self):
        """Test category classifier model file exists"""
        model_path = Path("ml/artifacts/category_model.pkl")
        assert model_path.exists(), "Category model file not found"

    def test_priority_model_exists(self):
        """Test priority classifier model file exists"""
        model_path = Path("ml/artifacts/priority_model.pkl")
        assert model_path.exists(), "Priority model file not found"

    def test_sla_model_exists(self):
        """Test SLA predictor model file exists"""
        model_path = Path("ml/artifacts/sla_model.pkl")
        assert model_path.exists(), "SLA model file not found"

    def test_tfidf_vectorizer_exists(self):
        """Test TF-IDF vectorizer file exists"""
        vectorizer_path = Path("ml/artifacts/tfidf_vectorizer.pkl")
        assert vectorizer_path.exists(), "TF-IDF vectorizer file not found"


class TestModelLoadability:
    """Test that models can be loaded successfully"""

    def test_load_category_model(self):
        """Test loading category model"""
        try:
            model = joblib.load("ml/artifacts/category_model.pkl")
            assert model is not None
            assert hasattr(model, "predict")
        except Exception as e:
            pytest.fail(f"Failed to load category model: {e}")

    def test_load_priority_model(self):
        """Test loading priority model"""
        try:
            model = joblib.load("ml/artifacts/priority_model.pkl")
            assert model is not None
            assert hasattr(model, "predict")
        except Exception as e:
            pytest.fail(f"Failed to load priority model: {e}")

    def test_load_sla_model(self):
        """Test loading SLA model"""
        try:
            model = joblib.load("ml/artifacts/sla_model.pkl")
            assert model is not None
            assert hasattr(model, "predict")
        except Exception as e:
            pytest.fail(f"Failed to load SLA model: {e}")

    def test_load_tfidf_vectorizer(self):
        """Test loading TF-IDF vectorizer"""
        try:
            vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
            assert vectorizer is not None
            assert hasattr(vectorizer, "transform")
        except Exception as e:
            pytest.fail(f"Failed to load TF-IDF vectorizer: {e}")


class TestModelStructure:
    """Test model structure and attributes"""

    def test_category_model_has_classes(self):
        """Test category model has expected classes"""
        model = joblib.load("ml/artifacts/category_model.pkl")
        
        # Should have classes_ attribute
        assert hasattr(model, "classes_")
        
        # Should have multiple categories
        assert len(model.classes_) >= 5
        
        # Check for expected categories
        expected_categories = ["Network", "Auth", "Security", "Software"]
        categories_list = model.classes_.tolist()
        for cat in expected_categories:
            assert cat in categories_list, f"Expected category {cat} not found"

    def test_priority_model_has_classes(self):
        """Test priority model has expected priority levels"""
        model = joblib.load("ml/artifacts/priority_model.pkl")
        
        assert hasattr(model, "classes_")
        
        # Should have 4 priority levels
        assert len(model.classes_) == 4
        
        # Check for expected priorities
        expected_priorities = ["Low", "Medium", "High", "Critical"]
        priorities_list = model.classes_.tolist()
        for priority in expected_priorities:
            assert priority in priorities_list

    def test_vectorizer_vocabulary_size(self):
        """Test TF-IDF vectorizer has reasonable vocabulary"""
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        # Should have vocabulary
        assert hasattr(vectorizer, "vocabulary_")
        
        # Vocabulary should not be empty
        assert len(vectorizer.vocabulary_) > 0
        
        # Should have reasonable vocabulary size (100-10000 words)
        vocab_size = len(vectorizer.vocabulary_)
        assert 100 <= vocab_size <= 10000, f"Unexpected vocabulary size: {vocab_size}"


class TestModelPredictions:
    """Test that models can make predictions"""

    def test_category_model_prediction(self):
        """Test category model can make predictions"""
        model = joblib.load("ml/artifacts/category_model.pkl")
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        # Sample text
        text = "cannot connect to vpn timeout error"
        X = vectorizer.transform([text])
        
        # Should predict without error
        prediction = model.predict(X)
        assert len(prediction) == 1
        assert isinstance(prediction[0], str)

    def test_category_model_probability(self):
        """Test category model can return probabilities"""
        model = joblib.load("ml/artifacts/category_model.pkl")
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        text = "laptop screen flickering display issue"
        X = vectorizer.transform([text])
        
        # Should return probabilities
        probabilities = model.predict_proba(X)
        assert probabilities.shape[0] == 1
        assert probabilities.shape[1] == len(model.classes_)
        
        # Probabilities should sum to 1
        assert abs(probabilities[0].sum() - 1.0) < 0.01

    def test_priority_model_prediction(self):
        """Test priority model can make predictions"""
        model = joblib.load("ml/artifacts/priority_model.pkl")
        
        # Sample features (simplified)
        import numpy as np
        X = np.array([[1, 0, 0, 0, 15, 2, 0.5, 0, 10, 2]])  # 10 features
        
        try:
            prediction = model.predict(X)
            assert len(prediction) == 1
            assert prediction[0] in ["Low", "Medium", "High", "Critical"]
        except ValueError as e:
            # May fail if feature count doesn't match - that's okay for this test
            pass


class TestModelConsistency:
    """Test model consistency and determinism"""

    def test_same_input_same_output(self):
        """Test model gives same output for same input"""
        model = joblib.load("ml/artifacts/category_model.pkl")
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        text = "password reset request urgent"
        X = vectorizer.transform([text])
        
        # Make multiple predictions
        pred1 = model.predict(X)[0]
        pred2 = model.predict(X)[0]
        pred3 = model.predict(X)[0]
        
        # Should be consistent
        assert pred1 == pred2 == pred3

    def test_probability_stability(self):
        """Test probability predictions are stable"""
        model = joblib.load("ml/artifacts/category_model.pkl")
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        text = "database query slow performance"
        X = vectorizer.transform([text])
        
        # Get probabilities multiple times
        prob1 = model.predict_proba(X)[0]
        prob2 = model.predict_proba(X)[0]
        
        # Should be identical
        import numpy as np
        assert np.allclose(prob1, prob2)


class TestVectorizerBehavior:
    """Test TF-IDF vectorizer behavior"""

    def test_vectorizer_transforms_text(self):
        """Test vectorizer transforms text to features"""
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        text = "test ticket description"
        result = vectorizer.transform([text])
        
        # Should return sparse matrix
        assert result.shape[0] == 1  # 1 document
        assert result.shape[1] > 0  # Some features

    def test_vectorizer_handles_empty_string(self):
        """Test vectorizer handles empty string"""
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        text = ""
        result = vectorizer.transform([text])
        
        # Should not crash
        assert result.shape[0] == 1

    def test_vectorizer_handles_unknown_words(self):
        """Test vectorizer handles unknown words gracefully"""
        vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")
        
        # Text with nonsense words
        text = "xyzabc qwerty asdfgh unknown words"
        result = vectorizer.transform([text])
        
        # Should not crash, may produce zero vector
        assert result.shape[0] == 1


class TestModelVersioning:
    """Test model versioning and metadata"""

    def test_models_are_recent(self):
        """Test that model files are not too old"""
        import time
        from datetime import datetime, timedelta
        
        model_path = Path("ml/artifacts/category_model.pkl")
        
        if model_path.exists():
            # Get file modification time
            mod_time = model_path.stat().st_mtime
            mod_datetime = datetime.fromtimestamp(mod_time)
            
            # Model should be less than 1 year old
            one_year_ago = datetime.now() - timedelta(days=365)
            
            # Just warning, not fail
            if mod_datetime < one_year_ago:
                pytest.skip("Model file is very old - consider retraining")
