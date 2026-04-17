export type Region = {
  id: string;
  name: string;
  initialViewState: {
    latitude: number;
    longitude: number;
    zoom: number;
  };
  fields: GeoJSON.FeatureCollection<
    GeoJSON.Polygon,
    {
      id: string;
      name: string;
    }
  >;
};
