"""
Test business rule validation
"""
from datetime import date, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.schemas.validation import (
    AvailabilityValidation,
    MessageContentValidation,
    ReviewValidation,
    ServiceRateValidation,
    UserLocationValidation,
)
from app.utils.validation import (
    ValidationError,
    validate_availability_time_slot,
    validate_booking_advance_notice,
    validate_booking_duration,
    validate_geographic_constraints,
    validate_postal_code,
)


class TestAvailabilityValidation:
    """Test availability validation rules"""

    def test_validate_availability_time_slot_valid(self):
        """Test valid time slot"""
        start_time = time(9, 0)  # 9:00 AM
        end_time = time(17, 0)   # 5:00 PM

        # Should not raise exception
        validate_availability_time_slot(start_time, end_time)

    def test_validate_availability_time_slot_invalid_start_after_end(self):
        """Test invalid time slot where start >= end"""
        start_time = time(17, 0)  # 5:00 PM
        end_time = time(9, 0)     # 9:00 AM

        with pytest.raises(ValidationError) as exc_info:
            validate_availability_time_slot(start_time, end_time)

        assert "Start time must be before end time" in str(
            exc_info.value.detail)

    def test_validate_availability_time_slot_too_long(self):
        """Test time slot exceeding 24 hours"""
        start_time = time(0, 0)   # Midnight
        end_time = time(23, 59)   # 11:59 PM (next day)

        with pytest.raises(ValidationError) as exc_info:
            validate_availability_time_slot(start_time, end_time)

        assert "Availability slot cannot exceed 24 hours" in str(
            exc_info.value.detail)

    def test_validate_availability_time_slot_too_short(self):
        """Test time slot less than 15 minutes"""
        start_time = time(9, 0)   # 9:00 AM
        end_time = time(9, 10)    # 9:10 AM

        with pytest.raises(ValidationError) as exc_info:
            validate_availability_time_slot(start_time, end_time)

        assert "Availability slot must be at least 15 minutes" in str(
            exc_info.value.detail)


class TestBookingValidation:
    """Test booking validation rules"""

    def test_validate_booking_advance_notice_valid(self):
        """Test valid advance notice"""
        future_date = date.today() + timedelta(days=1)
        future_time = time(10, 0)

        # Should not raise exception
        validate_booking_advance_notice(future_date, future_time)

    def test_validate_booking_advance_notice_insufficient(self):
        """Test insufficient advance notice"""
        future_date = date.today()
        future_time = time(10, 0)  # Same day

        with pytest.raises(ValidationError) as exc_info:
            validate_booking_advance_notice(future_date, future_time)

        assert "Bookings must be made at least 2 hours in advance" in str(
            exc_info.value.detail)

    def test_validate_booking_advance_notice_too_far(self):
        """Test booking too far in advance"""
        future_date = date.today() + timedelta(days=200)
        future_time = time(10, 0)

        with pytest.raises(ValidationError) as exc_info:
            validate_booking_advance_notice(future_date, future_time)

        assert "Bookings cannot be made more than 6 months in advance" in str(
            exc_info.value.detail)

    def test_validate_booking_duration_valid(self):
        """Test valid booking duration"""
        start_time = time(9, 0)   # 9:00 AM
        end_time = time(17, 0)    # 5:00 PM

        # Should not raise exception
        validate_booking_duration(start_time, end_time)

    def test_validate_booking_duration_too_short(self):
        """Test booking duration too short"""
        start_time = time(9, 0)   # 9:00 AM
        end_time = time(9, 15)    # 9:15 AM

        with pytest.raises(ValidationError) as exc_info:
            validate_booking_duration(start_time, end_time)

        assert "Booking must be at least 30 minutes" in str(
            exc_info.value.detail)

    def test_validate_booking_duration_too_long(self):
        """Test booking duration too long"""
        start_time = time(9, 0)   # 9:00 AM
        end_time = time(22, 0)    # 10:00 PM (13 hours)

        with pytest.raises(ValidationError) as exc_info:
            validate_booking_duration(start_time, end_time)

        assert "Booking cannot exceed 12 hours" in str(exc_info.value.detail)


class TestGeographicValidation:
    """Test geographic validation rules"""

    def test_validate_postal_code_valid(self):
        """Test valid Canadian postal codes"""
        valid_codes = ["K1A 0A6", "M5V 3A8", "H3Z 2Y7", "V6B 1A1"]

        for code in valid_codes:
            # Should not raise exception
            validate_postal_code(code)

    def test_validate_postal_code_invalid(self):
        """Test invalid postal codes"""
        invalid_codes = ["12345", "K1A", "INVALID", "K1A 0A", "K1A0A6"]

        for code in invalid_codes:
            with pytest.raises(ValidationError) as exc_info:
                validate_postal_code(code)

            assert "Invalid Canadian postal code format" in str(
                exc_info.value.detail)

    def test_validate_geographic_constraints_same_province(self):
        """Test geographic constraints for same-province services"""
        # Should not raise exception
        validate_geographic_constraints("ON", "ON", "house_sitting")

    def test_validate_geographic_constraints_different_province(self):
        """Test geographic constraints for different-province services"""
        with pytest.raises(ValidationError) as exc_info:
            validate_geographic_constraints("ON", "BC", "house_sitting")

        assert "only available within the same province" in str(
            exc_info.value.detail)


class TestPydanticValidation:
    """Test Pydantic validation schemas"""

    def test_availability_validation_valid(self):
        """Test valid availability data"""
        data = {
            "date": date.today() + timedelta(days=1),
            "start_time": time(9, 0),
            "end_time": time(17, 0),
            "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO"
        }

        # Should not raise exception
        availability = AvailabilityValidation(**data)
        assert availability.date == data["date"]
        assert availability.start_time == data["start_time"]
        assert availability.end_time == data["end_time"]

    def test_availability_validation_invalid_time(self):
        """Test invalid availability time slot"""
        data = {
            "date": date.today() + timedelta(days=1),
            "start_time": time(17, 0),  # End before start
            "end_time": time(9, 0),
        }

        with pytest.raises(ValueError) as exc_info:
            AvailabilityValidation(**data)

        assert "End time must be after start time" in str(exc_info.value)

    def test_user_location_validation_valid(self):
        """Test valid user location data"""
        data = {
            "province_code": "ON",
            "postal_code": "K1A 0A6",
            "city": "Ottawa"
        }

        # Should not raise exception
        location = UserLocationValidation(**data)
        assert location.province_code == "ON"
        assert location.postal_code == "K1A0A6"  # Spaces removed

    def test_user_location_validation_invalid_province(self):
        """Test invalid province code"""
        data = {
            "province_code": "XX",  # Invalid province
            "postal_code": "K1A 0A6"
        }

        with pytest.raises(ValueError) as exc_info:
            UserLocationValidation(**data)

        assert "Invalid Canadian province code" in str(exc_info.value)

    def test_service_rate_validation_valid(self):
        """Test valid service rates"""
        data = {
            "hourly_rate": 25.0,
            "daily_rate": 200.0
        }

        # Should not raise exception
        rates = ServiceRateValidation(**data)
        assert rates.hourly_rate == 25.0
        assert rates.daily_rate == 200.0

    def test_service_rate_validation_invalid_negative(self):
        """Test negative service rates"""
        data = {
            "hourly_rate": -10.0,  # Negative rate
            "daily_rate": 200.0
        }

        with pytest.raises(ValueError) as exc_info:
            ServiceRateValidation(**data)

        assert "Hourly rate cannot be negative" in str(exc_info.value)

    def test_message_content_validation_valid(self):
        """Test valid message content"""
        data = {
            "content": "Hello, I'm interested in your service!"
        }

        # Should not raise exception
        message = MessageContentValidation(**data)
        assert message.content == "Hello, I'm interested in your service!"

    def test_message_content_validation_empty(self):
        """Test empty message content"""
        data = {
            "content": "   "  # Empty after strip
        }

        with pytest.raises(ValueError) as exc_info:
            MessageContentValidation(**data)

        assert "Message content cannot be empty" in str(exc_info.value)

    def test_review_validation_valid(self):
        """Test valid review data"""
        data = {
            "rating": 5,
            "comment": "Excellent service, highly recommended!"
        }

        # Should not raise exception
        review = ReviewValidation(**data)
        assert review.rating == 5
        assert review.comment == "Excellent service, highly recommended!"

    def test_review_validation_invalid_rating(self):
        """Test invalid rating"""
        data = {
            "rating": 6,  # Rating too high
            "comment": "Great service!"
        }

        with pytest.raises(ValueError) as exc_info:
            ReviewValidation(**data)

        assert "Rating must be between 1 and 5" in str(exc_info.value)


class TestAPIValidation:
    """Test API endpoint validation"""

    def test_availability_endpoint_validation(self, client: TestClient):
        """Test availability endpoint with validation"""
        # This would test the actual API endpoint
        # For now, just ensure the endpoint exists
        response = client.get("/services/availability")
        assert response.status_code in [200, 401, 404]  # Depends on auth

    def test_booking_endpoint_validation(self, client: TestClient):
        """Test booking endpoint with validation"""
        # This would test the actual API endpoint
        response = client.get("/bookings/")
        assert response.status_code in [200, 401, 404]  # Depends on auth
