"use client"

import { Card, CardContent } from "@/components/ui/card"
import { useState, useRef, useEffect } from "react"

interface Tab {
  key: string
  displayValue: string
}

interface TabNavigationProps {
  tabs: Tab[]
  onTabChange?: (index: number) => void
  initialIndex?: number
}

export function TabNavigation({ tabs, onTabChange, initialIndex }: TabNavigationProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const [activeIndex, setActiveIndex] = useState(initialIndex ?? 0)
  const [hoverStyle, setHoverStyle] = useState({})
  const [activeStyle, setActiveStyle] = useState({ left: "0px", width: "0px" })
  const tabRefs = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    if (hoveredIndex !== null) {
      const hoveredElement = tabRefs.current[hoveredIndex]
      if (hoveredElement) {
        const { offsetLeft, offsetWidth } = hoveredElement
        setHoverStyle({
          left: `${offsetLeft}px`,
          width: `${offsetWidth}px`,
        })
      }
    }
  }, [hoveredIndex])

  useEffect(() => {
    const activeElement = tabRefs.current[activeIndex]
    if (activeElement) {
      const { offsetLeft, offsetWidth } = activeElement
      setActiveStyle({
        left: `${offsetLeft}px`,
        width: `${offsetWidth}px`,
      })
    }
  }, [activeIndex])

  useEffect(() => {
    requestAnimationFrame(() => {
      const firstElement = tabRefs.current[0]
      if (firstElement) {
        const { offsetLeft, offsetWidth } = firstElement
        setActiveStyle({
          left: `${offsetLeft}px`,
          width: `${offsetWidth}px`,
        })
      }
    })
  }, [])

  const handleTabClick = (index: number) => {
    setActiveIndex(index)
    onTabChange?.(index)
  }

  return (
    <Card className="border-none shadow-none relative flex items-center justify-center">
      <CardContent className="p-0">
        <div className="relative">
          {/* Hover Highlight */}
          <div
            className="absolute h-[30px] transition-all duration-300 ease-out bg-[#0e0f1114] rounded-[6px] flex items-center"
            style={{
              ...hoverStyle,
              opacity: hoveredIndex !== null ? 1 : 0,
            }}
          />

          {/* Active Indicator */}
          <div
            className="absolute bottom-[-6px] h-[2px] bg-[#0e0f11] transition-all duration-300 ease-out"
            style={activeStyle}
          />

          {/* Tabs */}
          <div className="relative flex space-x-[6px] items-center">
            {tabs.map((tab, index) => (
              <div
                key={tab.key}
                ref={(el) => { tabRefs.current[index] = el; void 0; }}
                 className={`px-3 py-2 cursor-pointer transition-colors duration-300 h-[30px] ${
                  index === activeIndex ? "text-[#0e0e10]" : "text-[#0e0f1199]"
                }`}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                onClick={() => handleTabClick(index)}
              >
                <div className="text-sm font-[var(--www-mattmannucci-me-geist-regular-font-family)] leading-5 whitespace-nowrap flex items-center justify-center h-full">
                  {tab.displayValue}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}