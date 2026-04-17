'use client'

import { MapPin } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { type Region } from '@/models/region'

interface RegionSelectProps {
  regions: Region[]
  onRegionChange: (region: Region) => void
  defaultRegionId?: string
}

export function RegionSelect({ regions, onRegionChange, defaultRegionId }: RegionSelectProps) {
  const handleValueChange = (value: string) => {
    const selectedRegion = regions.find(region => region.id === value)
    if (selectedRegion) {
      onRegionChange(selectedRegion)
    }
  }

  return (
    <Select 
      defaultValue={defaultRegionId || regions[0]?.id} 
      onValueChange={handleValueChange}
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a region" />
      </SelectTrigger>
      <SelectContent>
        {regions.map((region) => (
          <SelectItem 
            key={region.id} 
            value={region.id}
          >
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              <span>{region.name}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
