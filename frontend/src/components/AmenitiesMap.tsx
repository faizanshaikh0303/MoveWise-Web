import { useEffect, useRef, useState } from 'react';

interface Amenity {
  name: string;
  lat: number;
  lng: number;
  type: string;
}

interface AmenitiesMapProps {
  centerLat: number;
  centerLng: number;
  amenitiesByType: { [key: string]: Amenity[] };
  radius?: number; // in meters
}

const AmenitiesMap = ({ centerLat, centerLng, amenitiesByType, radius = 3219 }: AmenitiesMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const circleRef = useRef<any>(null);
  
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Amenity type colors
  const amenityColors: { [key: string]: string } = {
    'gyms': '#FF6B6B',
    'parks': '#4ECDC4',
    'restaurants': '#FFD93D',
    'cafes': '#95E1D3',
    'bars': '#F38181',
    'movies': '#AA96DA',
    'shopping': '#FCBAD3',
    'libraries': '#6C5CE7',
    'grocery stores': '#00B894',
    'pharmacies': '#FDCB6E',
    'hospitals': '#E17055',
  };

  useEffect(() => {
    // Load Google Maps script
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);

      script.onload = () => {
        setIsLoaded(true);
      };
    } else {
      setIsLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!isLoaded || !mapRef.current || !window.google) return;

    // Initialize map
    const map = new window.google.maps.Map(mapRef.current, {
      center: { lat: centerLat, lng: centerLng },
      zoom: 13,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
    });
    googleMapRef.current = map;

    // Add center marker
    new window.google.maps.Marker({
      position: { lat: centerLat, lng: centerLng },
      map: map,
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE,
        scale: 10,
        fillColor: '#4F46E5',
        fillOpacity: 1,
        strokeColor: '#FFFFFF',
        strokeWeight: 3,
      },
      title: 'Destination Location',
    });

    // Add radius circle
    circleRef.current = new window.google.maps.Circle({
      map: map,
      center: { lat: centerLat, lng: centerLng },
      radius: radius,
      fillColor: '#4F46E5',
      fillOpacity: 0.1,
      strokeColor: '#4F46E5',
      strokeOpacity: 0.3,
      strokeWeight: 2,
    });

  }, [isLoaded, centerLat, centerLng, radius]);

  useEffect(() => {
    if (!googleMapRef.current || !window.google) return;

    const google = window.google; // Store reference after type check

    // Clear existing markers
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    // If no type selected, show all
    const typesToShow = selectedType ? [selectedType] : Object.keys(amenitiesByType);

    typesToShow.forEach(type => {
      const amenities = amenitiesByType[type] || [];
      const color = amenityColors[type] || '#666666';

      amenities.forEach(amenity => {
        const marker = new google.maps.Marker({
          position: { lat: amenity.lat, lng: amenity.lng },
          map: googleMapRef.current,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: color,
            fillOpacity: 0.8,
            strokeColor: '#FFFFFF',
            strokeWeight: 2,
          },
          title: amenity.name,
        });

        // Add info window
        const infoWindow = new google.maps.InfoWindow({
          content: `<div style="padding: 8px;">
            <h3 style="font-weight: bold; margin: 0 0 4px 0;">${amenity.name}</h3>
            <p style="margin: 0; color: #666; font-size: 14px;">${type}</p>
          </div>`,
        });

        marker.addListener('click', () => {
          infoWindow.open(googleMapRef.current, marker);
        });

        markersRef.current.push(marker);
      });
    });

  }, [selectedType, amenitiesByType]);

  const amenityTypes = Object.keys(amenitiesByType);
  const totalAmenities = Object.values(amenitiesByType).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="space-y-4">
      {/* Map */}
      <div 
        ref={mapRef} 
        className="w-full h-[500px] rounded-xl overflow-hidden border-2 border-gray-200"
      />

      {/* Filter Buttons */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-gray-900">Filter by Amenity Type</h4>
          {selectedType && (
            <button
              onClick={() => setSelectedType(null)}
              className="text-sm text-primary hover:text-primary-dark"
            >
              Show All ({totalAmenities})
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {amenityTypes.map(type => {
            const count = amenitiesByType[type]?.length || 0;
            const color = amenityColors[type] || '#666666';
            const isSelected = selectedType === type;

            return (
              <button
                key={type}
                onClick={() => setSelectedType(isSelected ? null : type)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  isSelected
                    ? 'bg-primary text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="capitalize">{type}</span>
                <span className={`${isSelected ? 'text-white/80' : 'text-gray-500'}`}>
                  ({count})
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-blue-900">
            <p className="font-semibold mb-1">Interactive Map Guide:</p>
            <ul className="space-y-1 text-blue-800">
              <li>• <span className="inline-block w-3 h-3 rounded-full bg-primary mr-1" /> = Your destination location</li>
              <li>• Circle shows 2-mile search radius</li>
              <li>• Click colored dots to see amenity details</li>
              <li>• Click amenity type buttons to filter markers</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AmenitiesMap;
