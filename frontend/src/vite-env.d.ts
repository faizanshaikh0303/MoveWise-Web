/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_GOOGLE_MAPS_API_KEY: string
  // add more env variables types here as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Google Maps types
declare global {
  interface Window {
    google?: {
      maps: {
        Map: any;
        Marker: any;
        Circle: any;
        InfoWindow: any;
        LatLngBounds: any;
        SymbolPath: any;
        event: any;
        places: {
          Autocomplete: any;
        };
      };
    };
  }
}

export {};