# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import D
# from django.contrib.gis.db.models.functions import Distance
# import geocoder
# import logging

# logger = logging.getLogger(__name__)



# class LocationService:
#     """Service class for handling location-related operations"""
    
#     @staticmethod
#     def get_coordinates_from_ip(ip_address):
#         """Get approximate coordinates from IP address"""
#         try:
#             g = geocoder.ip(ip_address)
#             if g.ok:
#                 return {
#                     'latitude': g.lat,
#                     'longitude': g.lng,
#                     'accuracy': 5000,  # IP geolocation is typically accurate to city level
#                     'source': 'ip'
#                 }
#         except Exception as e:
#             logger.error(f"IP geolocation failed: {e}")
#         return None
    
#     @staticmethod
#     def get_address_from_coordinates(latitude, longitude):
#         """Reverse geocode coordinates to get address"""
#         try:
#             location = geocoder.osm([latitude, longitude], method='reverse')
#             if location.ok:
#                 return location.address
#         except Exception as e:
#             logger.error(f"Reverse geocoding failed: {e}")
#         return None
    
#     @staticmethod
#     def find_nearby_users(point, radius_km, user_queryset):
#         """Find users within specified radius of a point"""
#         return user_queryset.filter(
#             location__distance_lte=(point, D(km=radius_km))
#         ).annotate(
#             distance=Distance('location', point)
#         ).order_by('distance')