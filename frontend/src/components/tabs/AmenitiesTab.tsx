import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  MapPin, 
  Coffee, 
  ShoppingBag, 
  Film, 
  Dumbbell,
  UtensilsCrossed,
  Heart,
  Building,
  Store,
  GraduationCap
} from 'lucide-react';
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';

// Define marker type
interface MarkerType {
  id: string;
  category: string;
  name: string;
  address?: string;
  lat: number;
  lng: number;
  color: string;
}

const AmenitiesTab = ({ data }: any) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedMarker, setSelectedMarker] = useState<MarkerType | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);

  const destinationLat = data?.destination_lat || 0;
  const destinationLng = data?.destination_lng || 0;
  
  const currentAmenities: Record<string, number> = data?.current_amenities || {};
  const destinationAmenities: Record<string, number> = data?.destination_amenities || {};
  const destinationLocations: Record<string, any[]> = data?.destination_locations || {};

  // Category icon mapping
  const categoryIcons: Record<string, any> = {
    'grocery stores': { icon: Store, color: '#10b981', markerColor: '#10b981' },
    'cafes': { icon: Coffee, color: '#8b5cf6', markerColor: '#8b5cf6' },
    'bars': { icon: Coffee, color: '#ef4444', markerColor: '#ef4444' },
    'shopping malls': { icon: ShoppingBag, color: '#3b82f6', markerColor: '#3b82f6' },
    'movie theaters': { icon: Film, color: '#f59e0b', markerColor: '#f59e0b' },
    'gyms': { icon: Dumbbell, color: '#ec4899', markerColor: '#ec4899' },
    'restaurants': { icon: UtensilsCrossed, color: '#f97316', markerColor: '#f97316' },
    'hospitals': { icon: Heart, color: '#ef4444', markerColor: '#ef4444' },
    'pharmacies': { icon: Building, color: '#06b6d4', markerColor: '#06b6d4' },
    'parks': { icon: MapPin, color: '#22c55e', markerColor: '#22c55e' },
    'schools': { icon: GraduationCap, color: '#6366f1', markerColor: '#6366f1' }
  };

  // Get all markers for the map - with proper typing
  const allMarkers: MarkerType[] = [];
  Object.entries(destinationLocations).forEach(([category, places]) => {
    if (!places || !Array.isArray(places)) return;
    
    places.forEach((place: any, idx: number) => {
      if (selectedCategory === 'all' || selectedCategory === category) {
        allMarkers.push({
          id: `${category}-${idx}`,
          category,
          name: place.name,
          address: place.address,
          lat: place.lat,
          lng: place.lng,
          color: categoryIcons[category]?.markerColor || '#gray'
        });
      }
    });
  });

  const mapContainerStyle = {
    width: '100%',
    height: '600px',
    borderRadius: '12px'
  };

  const center = {
    lat: destinationLat,
    lng: destinationLng
  };

  const mapOptions = {
    disableDefaultUI: false,
    zoomControl: true,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: true
  };

  // Calculate bounds to show all markers
  useEffect(() => {
    if (map && allMarkers.length > 0 && window.google) {
      const bounds = new window.google.maps.LatLngBounds();
      allMarkers.forEach(marker => {
        bounds.extend({ lat: marker.lat, lng: marker.lng });
      });
      // Add center point
      bounds.extend(center);
      map.fitBounds(bounds);
    }
  }, [map, allMarkers.length, selectedCategory]);

  const totalCurrent: number = Object.values(currentAmenities).reduce((a: number, b: number) => a + b, 0);
  const totalDestination: number = Object.values(destinationAmenities).reduce((a: number, b: number) => a + b, 0);
  const percentChange: number = totalCurrent > 0 ? parseFloat((((totalDestination - totalCurrent) / totalCurrent) * 100).toFixed(1)) : 0;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Total Amenities</span>
            <MapPin className="h-5 w-5 text-blue-500" />
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {totalDestination}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            within 1 mile
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Change</span>
          </div>
          <div className={`text-4xl font-bold ${
            percentChange > 0 ? 'text-green-600' : percentChange < 0 ? 'text-red-600' : 'text-gray-900'
          }`}>
            {percentChange > 0 ? '+' : ''}{percentChange}%
          </div>
          <div className="mt-2 text-sm text-gray-600">
            vs current location
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Categories</span>
          </div>
          <div className="text-4xl font-bold text-gray-900">
            {Object.keys(destinationAmenities).length}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            types of places
          </div>
        </motion.div>
      </div>

      {/* Category Filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl p-4 shadow-sm border border-gray-200"
      >
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedCategory === 'all'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({totalDestination})
          </button>
          {Object.entries(destinationAmenities).map(([category, count]: [string, number]) => {
            const categoryInfo = categoryIcons[category];
            const Icon = categoryInfo?.icon || MapPin;
            
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 ${
                  selectedCategory === category
                    ? 'text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                style={{
                  backgroundColor: selectedCategory === category ? categoryInfo?.color : undefined
                }}
              >
                <Icon className="h-4 w-4" />
                <span>{category} ({count})</span>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Map */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          Amenities Map
          {selectedCategory !== 'all' && (
            <span className="text-sm font-normal text-gray-600 ml-2">
              - {selectedCategory}
            </span>
          )}
        </h3>
        
        <LoadScript googleMapsApiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={center}
            zoom={14}
            options={mapOptions}
            onLoad={(mapInstance) => setMap(mapInstance)}
          >
            {/* Destination marker (home icon) */}
            <Marker
              position={center}
              icon={{
                path: window.google?.maps?.SymbolPath?.CIRCLE,
                scale: 10,
                fillColor: '#3b82f6',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 3
              }}
              title="Your new location"
            />

            {/* Amenity markers */}
            {allMarkers.map((marker) => (
              <Marker
                key={marker.id}
                position={{ lat: marker.lat, lng: marker.lng }}
                onClick={() => setSelectedMarker(marker)}
                icon={{
                  path: window.google?.maps?.SymbolPath?.CIRCLE,
                  scale: 6,
                  fillColor: marker.color,
                  fillOpacity: 0.8,
                  strokeColor: '#ffffff',
                  strokeWeight: 2
                }}
              />
            ))}

            {/* Info window */}
            {selectedMarker && (
              <InfoWindow
                position={{ lat: selectedMarker.lat, lng: selectedMarker.lng }}
                onCloseClick={() => setSelectedMarker(null)}
              >
                <div className="p-2">
                  <h4 className="font-semibold text-gray-900">{selectedMarker.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{selectedMarker.address}</p>
                  <p className="text-xs text-gray-500 mt-1 capitalize">{selectedMarker.category}</p>
                </div>
              </InfoWindow>
            )}
          </GoogleMap>
        </LoadScript>
      </motion.div>

      {/* Comparison Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-bold text-gray-900 mb-4">Location Comparison</h3>
        <div className="grid grid-cols-2 gap-6">
          {/* Current Location */}
          <div>
            <h4 className="text-sm font-semibold text-gray-600 mb-3">Current Location</h4>
            <div className="space-y-2">
              {Object.entries(currentAmenities).map(([category, count]: [string, number]) => {
                const categoryInfo = categoryIcons[category];
                const Icon = categoryInfo?.icon || MapPin;
                
                return (
                  <div key={category} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Icon className="h-4 w-4" style={{ color: categoryInfo?.color }} />
                      <span className="text-sm text-gray-700 capitalize">{category}</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{count}</span>
                  </div>
                );
              })}
              <div className="flex items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-200 mt-3">
                <span className="text-sm font-semibold text-blue-900">Total</span>
                <span className="text-sm font-bold text-blue-900">{totalCurrent}</span>
              </div>
            </div>
          </div>

          {/* Destination Location */}
          <div>
            <h4 className="text-sm font-semibold text-gray-600 mb-3">New Location</h4>
            <div className="space-y-2">
              {Object.entries(destinationAmenities).map(([category, count]: [string, number]) => {
                const categoryInfo = categoryIcons[category];
                const Icon = categoryInfo?.icon || MapPin;
                const currentCount: number = currentAmenities[category] || 0;
                const diff: number = count - currentCount;
                
                return (
                  <div key={category} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Icon className="h-4 w-4" style={{ color: categoryInfo?.color }} />
                      <span className="text-sm text-gray-700 capitalize">{category}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-semibold text-gray-900">{count}</span>
                      {diff !== 0 && (
                        <span className={`text-xs font-medium ${
                          diff > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          ({diff > 0 ? '+' : ''}{diff})
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
              <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg border border-green-200 mt-3">
                <span className="text-sm font-semibold text-green-900">Total</span>
                <span className="text-sm font-bold text-green-900">{totalDestination}</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-blue-50 border-blue-200 rounded-xl p-6 border-2"
      >
        <p className="text-gray-700">{data?.comparison_text}</p>
      </motion.div>
    </div>
  );
};

export default AmenitiesTab;
