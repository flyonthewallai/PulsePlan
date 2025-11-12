import React, { useEffect, useState } from 'react'

interface AnimatedThinkingTextProps {
  text?: string
  className?: string
}

export default function AnimatedThinkingText({ 
  text = "Thinking", 
  className = "" 
}: AnimatedThinkingTextProps) {
  const [opacities, setOpacities] = useState<number[]>(
    text.split('').map(() => 0.3)
  )

  useEffect(() => {
    const characters = text.split('')
    let animationId: number
    
    const animate = () => {
      const now = Date.now()
      const newOpacities = characters.map((_, index) => {
        const delay = (characters.length - 1 - index) * 60 // Reverse the delay calculation
        const cycleTime = 2000 // Total cycle time
        const fadeTime = 400 // Fade in/out duration
        
        const timeInCycle = (now + delay) % cycleTime
        
        if (timeInCycle < fadeTime) {
          // Fade in
          return 0.3 + (0.7 * (timeInCycle / fadeTime))
        } else if (timeInCycle < fadeTime * 2) {
          // Fade out
          const fadeOutProgress = (timeInCycle - fadeTime) / fadeTime
          return 1 - (0.7 * fadeOutProgress)
        } else {
          // Dim state
          return 0.3
        }
      })
      
      setOpacities(newOpacities)
      animationId = requestAnimationFrame(animate)
    }
    
    animationId = requestAnimationFrame(animate)
    
    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [text])

  return (
    <div className={`flex flex-wrap ${className}`}>
      {text.split('').map((char, index) => (
        <span
          key={index}
          style={{
            opacity: opacities[index],
            transition: 'opacity 0.1s ease-out'
          }}
        >
          {char}
        </span>
      ))}
    </div>
  )
}
