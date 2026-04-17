'use client';

import * as React from 'react';
import * as SliderPrimitive from '@radix-ui/react-slider';

import { cn } from '@/lib/utils';

interface DualRangeSliderProps extends React.ComponentProps<typeof SliderPrimitive.Root> {
  labelPosition?: 'top' | 'bottom';
  label?: (value: number | undefined) => React.ReactNode;
  variant?: 'default' | 'green' | 'gray';
  showMiddleLine?: boolean;
}

const DualRangeSlider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  DualRangeSliderProps
>(({ className, label, variant = 'default', showMiddleLine = false, ...props }, ref) => {
  const initialValue = Array.isArray(props.value) ? props.value : [props.min, props.max];
  const middle = props.max !== undefined && props.min !== undefined 
    ? props.min + (props.max - props.min) / 2 
    : undefined;

  return (
    <div className="w-full flex justify-between items-center">
              <span className="text-sm text-muted-foreground pr-2">{props.min}</span>

      <SliderPrimitive.Root
        ref={ref}
        className={cn('relative flex w-full touch-none select-none items-center', className)}
        {...props}
      >
        <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
          <SliderPrimitive.Range className={cn(
            "absolute h-full",
            variant === 'green' ? 'bg-green-400' : 
            variant === 'gray' ? 'bg-gray-400' : 
            'bg-primary'
          )} />
          {showMiddleLine && middle !== undefined && (
            <div 
              className={cn(
                "absolute top-0 bottom-0 w-0.5 -translate-x-1/2",
                variant === 'green' ? 'bg-green-600' : 
                variant === 'gray' ? 'bg-gray-600' : 
                'bg-primary'
              )}
              style={{ left: `${((middle - (props.min ?? 0)) / ((props.max ?? 100) - (props.min ?? 0))) * 100}%` }}
            />
          )}
        </SliderPrimitive.Track>
        {initialValue.map((value, index) => (
          <React.Fragment key={index}>
            <SliderPrimitive.Thumb className={cn(
              "group relative flex  items-center justify-center rounded-full border-2 bg-background transition-all disabled:pointer-events-none disabled:opacity-50  active:h-8 active:w-8",
              variant === 'green' ? 'border-green-400 h-6 w-6 hover:h-8 hover:w-8' : 
              variant === 'gray' ? 'border-gray-400 h- w-2' : 
              'border-primary'
            )}>
              {label && (
                <span className="text-xs transition-all group-hover:text-sm group-active:text-sm">
                  {label(value)}
                </span>
              )}
            </SliderPrimitive.Thumb>
          </React.Fragment>
        ))}
      </SliderPrimitive.Root>
      <span className="text-sm text-muted-foreground pl-2">{props.max}</span>
    </div>
  );
});
DualRangeSlider.displayName = 'DualRangeSlider';

export { DualRangeSlider };
