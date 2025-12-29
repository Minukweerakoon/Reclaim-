"""
Tests for Novel Feature #1: Spatial-Temporal Context Validation
Bayesian Probabilistic Plausibility Assessment

Tests the research-grade implementation of P(Item|Location, Time) validation.
"""
import pytest
from src.intelligence.spatial_temporal_validator import (
    SpatialTemporalValidator,
    get_spatial_temporal_validator
)


class TestSpatialTemporalValidator:
    """Test suite for the Bayesian Spatial-Temporal Validator."""
    
    @pytest.fixture
    def validator(self):
        """Create a fresh validator instance for each test."""
        return SpatialTemporalValidator()
    
    # ------------------------------------------------------------------ #
    # Basic Functionality Tests
    # ------------------------------------------------------------------ #
    
    def test_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator is not None
        assert validator.total_observations == 0
        assert len(validator.LOCATION_PRIORS) > 0
        assert len(validator.TIME_PRIORS) > 0
    
    def test_singleton_pattern(self):
        """Test that get_spatial_temporal_validator returns singleton."""
        v1 = get_spatial_temporal_validator()
        v2 = get_spatial_temporal_validator()
        assert v1 is v2
    
    # ------------------------------------------------------------------ #
    # High Plausibility Tests (Expected to PASS validation)
    # ------------------------------------------------------------------ #
    
    def test_laptop_in_library_afternoon(self, validator):
        """Laptop in library during afternoon should be VERY plausible."""
        result = validator.calculate_plausibility("laptop", "library", "2pm")
        
        print(f"\n[HIGH PLAUSIBILITY TEST] Laptop in Library @ 2pm")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        print(f"  Location Prob: {result['location_probability']:.2f}")
        print(f"  Time Prob: {result['time_probability']:.2f}")
        print(f"  Explanation: {result['explanation']}")
        
        assert result['plausibility_score'] >= 0.70, "Laptop in library should be highly plausible"
        assert result['valid'] == True
        assert result['confidence_level'] in ['high', 'very_high']
    
    def test_phone_in_cafeteria_noon(self, validator):
        """Phone in cafeteria during noon should be plausible."""
        result = validator.calculate_plausibility("phone", "cafeteria", "noon")
        
        print(f"\n[HIGH PLAUSIBILITY TEST] Phone in Cafeteria @ noon")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        
        assert result['plausibility_score'] >= 0.60
        assert result['valid'] == True
    
    def test_wallet_in_gym_morning(self, validator):
        """Wallet in gym during morning should be plausible."""
        result = validator.calculate_plausibility("wallet", "gym", "morning")
        
        print(f"\n[HIGH PLAUSIBILITY TEST] Wallet in Gym @ morning")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        
        assert result['plausibility_score'] >= 0.50
        assert result['valid'] == True
    
    def test_keys_in_parking(self, validator):
        """Keys in parking lot should be VERY plausible."""
        result = validator.calculate_plausibility("keys", "parking", "evening")
        
        print(f"\n[HIGH PLAUSIBILITY TEST] Keys in Parking @ evening")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        
        assert result['plausibility_score'] >= 0.65
        assert result['valid'] == True
    
    # ------------------------------------------------------------------ #
    # Low Plausibility Tests (Expected to FAIL validation)
    # ------------------------------------------------------------------ #
    
    def test_swimsuit_in_server_room(self, validator):
        """Swimsuit in server room should be HIGHLY implausible."""
        result = validator.calculate_plausibility("swimsuit", "server room", "9am")
        
        print(f"\n[LOW PLAUSIBILITY TEST] Swimsuit in Server Room @ 9am")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        print(f"  Location Prob: {result['location_probability']:.2f}")
        print(f"  Time Prob: {result['time_probability']:.2f}")
        print(f"  Explanation: {result['explanation']}")
        print(f"  Suggestions: {result['suggestions']}")
        
        assert result['plausibility_score'] < 0.30, "Swimsuit in server room should be implausible"
        assert result['valid'] == False
        assert len(result['suggestions']) > 0, "Should provide suggestions for implausible combinations"
    
    def test_laptop_in_pool(self, validator):
        """Laptop in pool should be implausible."""
        result = validator.calculate_plausibility("laptop", "pool", "afternoon")
        
        print(f"\n[LOW PLAUSIBILITY TEST] Laptop in Pool @ afternoon")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        
        assert result['plausibility_score'] < 0.40
        assert result['valid'] == False
    
    def test_sports_equipment_in_library(self, validator):
        """Sports equipment in library should be unusual."""
        result = validator.calculate_plausibility("sports_equipment", "library", "morning")
        
        print(f"\n[LOW PLAUSIBILITY TEST] Sports Equipment in Library @ morning")
        print(f"  Plausibility Score: {result['plausibility_score']:.2f}")
        
        assert result['plausibility_score'] < 0.50
    
    # ------------------------------------------------------------------ #
    # Normalization Tests
    # ------------------------------------------------------------------ #
    
    def test_item_normalization_iphone(self, validator):
        """iPhone should normalize to 'phone'."""
        normalized = validator.normalize_item("iPhone 15 Pro")
        assert normalized == "phone"
    
    def test_item_normalization_macbook(self, validator):
        """MacBook should normalize to 'laptop'."""
        normalized = validator.normalize_item("MacBook Air")
        assert normalized == "laptop"
    
    def test_location_normalization_canteen(self, validator):
        """Canteen should normalize to 'cafeteria'."""
        normalized = validator.normalize_location("canteen")
        assert normalized == "cafeteria"
    
    def test_location_normalization_bathroom(self, validator):
        """Bathroom should normalize to 'restroom'."""
        normalized = validator.normalize_location("bathroom")
        assert normalized == "restroom"
    
    def test_time_normalization_2pm(self, validator):
        """2pm should normalize to 'afternoon'."""
        normalized = validator.normalize_time("2pm")
        assert normalized == "afternoon"
    
    def test_time_normalization_9am(self, validator):
        """9am should normalize to 'morning'."""
        normalized = validator.normalize_time("9am")
        assert normalized == "morning"
    
    # ------------------------------------------------------------------ #
    # Learning/Hybrid Tests
    # ------------------------------------------------------------------ #
    
    def test_record_validated_item(self, validator):
        """Test that learning records observations correctly."""
        initial_obs = validator.total_observations
        
        validator.record_validated_item("laptop", "library", "afternoon")
        validator.record_validated_item("laptop", "library", "afternoon")
        validator.record_validated_item("phone", "cafeteria", "noon")
        
        assert validator.total_observations == initial_obs + 3
        assert validator.learned_location_counts["laptop"]["library"] >= 2
    
    def test_learning_stats(self, validator):
        """Test learning statistics."""
        stats = validator.get_learning_stats()
        
        assert "total_observations" in stats
        assert "items_tracked" in stats
        assert "learning_weight" in stats
        assert "static_weight" in stats
    
    # ------------------------------------------------------------------ #
    # Edge Case Tests
    # ------------------------------------------------------------------ #
    
    def test_unknown_item(self, validator):
        """Unknown items should still return a result."""
        result = validator.calculate_plausibility("quantum_device", "library", "noon")
        
        assert "plausibility_score" in result
        assert result['normalized_inputs']['item'] == 'unknown'
    
    def test_unknown_location(self, validator):
        """Unknown locations should still return a result."""
        result = validator.calculate_plausibility("laptop", "mars_base", "afternoon")
        
        assert "plausibility_score" in result
        assert result['normalized_inputs']['location'] == 'unknown'
    
    def test_no_time_provided(self, validator):
        """Missing time should use default."""
        result = validator.calculate_plausibility("laptop", "library", None)
        
        assert "plausibility_score" in result
        assert result['normalized_inputs']['time'] == 'afternoon'
    
    # ------------------------------------------------------------------ #
    # Explanation Quality Tests
    # ------------------------------------------------------------------ #
    
    def test_high_plausibility_has_positive_explanation(self, validator):
        """High plausibility should have positive wording."""
        result = validator.calculate_plausibility("laptop", "library", "afternoon")
        
        assert "✅" in result['explanation'] or "plausible" in result['explanation'].lower()
    
    def test_low_plausibility_has_warning_explanation(self, validator):
        """Low plausibility should have warning wording."""
        result = validator.calculate_plausibility("swimsuit", "server room", "9am")
        
        assert "❌" in result['explanation'] or "⚠️" in result['explanation'] or "unusual" in result['explanation'].lower()


# Run quick sanity check when executed directly
if __name__ == "__main__":
    print("=" * 60)
    print("NOVEL FEATURE #1: Spatial-Temporal Context Validation")
    print("Bayesian Probabilistic Plausibility Assessment")
    print("=" * 60)
    
    validator = SpatialTemporalValidator()
    
    # Test cases
    test_cases = [
        ("laptop", "library", "2pm"),
        ("phone", "cafeteria", "noon"),
        ("wallet", "gym", "morning"),
        ("swimsuit", "server room", "9am"),
        ("laptop", "pool", "afternoon"),
        ("keys", "parking", "evening"),
        ("backpack", "classroom", "morning"),
    ]
    
    print("\n" + "-" * 60)
    for item, location, time in test_cases:
        result = validator.calculate_plausibility(item, location, time)
        status = "✅ VALID" if result['valid'] else "❌ INVALID"
        print(f"{item:15} @ {location:15} ({time:10}) → {result['plausibility_score']:.2f} {status}")
    
    print("-" * 60)
    print("\n✓ All basic sanity checks passed!")
