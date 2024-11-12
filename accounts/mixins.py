from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.core.validators import MinValueValidator, MaxValueValidator
import logging

logger = logging.getLogger('location_logger')

class LocationMixin(models.Model):
    """Mixin for models that need location tracking"""
    location = models.PointField(
        srid=4326,  # Using WGS84 coordinate system (standard for GPS)
        null=True,
        blank=True,
        help_text="Geographic location (longitude, latitude)"
    )
    location_accuracy = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Accuracy of location in meters"
    )
    location_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time location was updated"
    )
    address = models.TextField(
        blank=True,
        help_text="Human-readable address"
    )

    class Meta:
        abstract = True

    def update_location(self, latitude, longitude, accuracy=None):
        """Update location with new coordinates"""
        try:
            self.location = Point(float(longitude), float(latitude), srid=4326)
            if accuracy is not None:
                self.location_accuracy = accuracy
            self.save()
            logger.info(f"Location updated to: {self.coordinates} with accuracy {accuracy}")
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Location update failed: {e}")
            return False

    @property
    def coordinates(self):
        """Return tuple of (latitude, longitude)"""
        if self.location:
            return (self.location.y, self.location.x)
        return None