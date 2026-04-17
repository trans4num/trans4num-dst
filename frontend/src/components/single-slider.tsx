'use client';

import { DualRangeSlider } from '@/components/ui/dual-range-slider';
import { useState } from 'react';

interface SingleSliderProps {
  value: number;
  onValueChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  label?: (value: number) => number;
  disabled?: boolean;
  showMiddleLine?: boolean;
}

export default function SingleSlider({ value, onValueChange, min, max, step, disabled, showMiddleLine = false }: SingleSliderProps) {
  const [values, setValues] = useState([value]);

  const handleValueChange = (newValues: number[]) => {
    setValues(newValues);
    onValueChange(newValues[0]);
  };

  return (
    <div className={`w-full space-y-5 px-10`}>
      <DualRangeSlider
        value={values}
        onValueChange={handleValueChange}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        showMiddleLine={showMiddleLine}
        variant={disabled ? 'gray' : 'green'} 
      />
    </div>
  );
}
