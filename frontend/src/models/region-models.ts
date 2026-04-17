export type RegionModels = {
  models: Array<{
    goal: {
      name: string;
      description: string;
      type: string;
      configuration: Array<{
        name: string;
        enabled: boolean;
        value: number;
        range: [number | null, number | null];
        unit: string;
      }>;
    };
    constraints: Array<{
      name: string;
      enabled: boolean;
      value: number;
      range: [number | null, number | null];
      unit: string;
    }>;
  }>;
};
