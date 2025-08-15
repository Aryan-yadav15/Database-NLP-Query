'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { Activity, Zap, TrendingUp, DollarSign, Clock, Cpu } from 'lucide-react'

export default function AnimatedTokenTracker({ tokenUsage }) {
  const [isVisible, setIsVisible] = useState(false)
  const [animatedValues, setAnimatedValues] = useState({
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
    llm_calls_count: 0
  })

  // Animation refs
  const containerRef = useRef(null)
  const metricsRef = useRef([])
  const progressRef = useRef(null)
  const sparklesRef = useRef([])

  // Calculate derived metrics
  const totalTokens = (tokenUsage?.input_tokens || 0) + (tokenUsage?.output_tokens || 0)
  const estimatedCost = (totalTokens * 0.000002).toFixed(4) // Example pricing
  const avgTokensPerCall = tokenUsage?.llm_calls_count ? 
    Math.round(totalTokens / tokenUsage.llm_calls_count) : 0

  // Create floating sparkles
  const createSparkles = () => {
    if (!containerRef.current) return

    // Clear existing sparkles
    sparklesRef.current.forEach(sparkle => sparkle?.remove())
    sparklesRef.current = []

    for (let i = 0; i < 8; i++) {
      const sparkle = document.createElement('div')
      sparkle.className = 'absolute w-1 h-1 bg-yellow-400 rounded-full opacity-30 pointer-events-none'
      sparkle.style.left = Math.random() * 100 + '%'
      sparkle.style.top = Math.random() * 100 + '%'
      containerRef.current.appendChild(sparkle)
      sparklesRef.current.push(sparkle)

      gsap.to(sparkle, {
        opacity: 0.7,
        scale: 1.5,
        duration: 1 + Math.random(),
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut"
      })

      gsap.to(sparkle, {
        rotation: 360,
        duration: 4 + Math.random() * 2,
        repeat: -1,
        ease: "none"
      })
    }
  }

  // Animate counter values
  const animateCounters = () => {
    if (!tokenUsage) return

    // Animate input tokens
    gsap.to(animatedValues, {
      input_tokens: tokenUsage.input_tokens || 0,
      duration: 1.5,
      ease: "power2.out",
      onUpdate: () => {
        setAnimatedValues({ ...animatedValues })
      }
    })

    // Animate output tokens with delay
    setTimeout(() => {
      gsap.to(animatedValues, {
        output_tokens: tokenUsage.output_tokens || 0,
        duration: 1.5,
        ease: "power2.out",
        onUpdate: () => {
          setAnimatedValues({ ...animatedValues })
        }
      })
    }, 300)

    // Animate LLM calls
    setTimeout(() => {
      gsap.to(animatedValues, {
        llm_calls_count: tokenUsage.llm_calls_count || 0,
        duration: 1,
        ease: "power2.out",
        onUpdate: () => {
          setAnimatedValues({ ...animatedValues })
        }
      })
    }, 600)
  }

  // Animate progress bar
  const animateProgress = () => {
    if (!progressRef.current || !totalTokens) return

    const percentage = Math.min((totalTokens / 10000) * 100, 100) // Example max of 10k tokens

    gsap.fromTo(progressRef.current,
      { width: '0%' },
      { 
        width: `${percentage}%`, 
        duration: 2,
        ease: "power2.out"
      }
    )
  }

  // Animate metric cards entrance
  const animateMetricsEntrance = () => {
    metricsRef.current.forEach((metric, index) => {
      if (metric) {
        gsap.fromTo(metric,
          { 
            y: 30, 
            opacity: 0, 
            scale: 0.8,
            rotationX: -15
          },
          { 
            y: 0, 
            opacity: 1, 
            scale: 1,
            rotationX: 0,
            duration: 0.6,
            delay: index * 0.1,
            ease: "back.out(1.7)"
          }
        )
      }
    })
  }

  // Hover effects for metric cards
  const addMetricHoverEffects = () => {
    metricsRef.current.forEach(metric => {
      if (!metric) return

      metric.addEventListener('mouseenter', () => {
        gsap.to(metric, {
          scale: 1.05,
          y: -3,
          boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
          duration: 0.3,
          ease: "back.out(1.7)"
        })

        // Icon animation
        const icon = metric.querySelector('.metric-icon')
        if (icon) {
          gsap.to(icon, {
            scale: 1.2,
            rotation: 5,
            duration: 0.3,
            ease: "back.out(1.7)"
          })
        }

        // Value glow effect
        const value = metric.querySelector('.metric-value')
        if (value) {
          gsap.to(value, {
            textShadow: "0 0 10px rgba(59, 130, 246, 0.5)",
            duration: 0.3
          })
        }
      })

      metric.addEventListener('mouseleave', () => {
        gsap.to(metric, {
          scale: 1,
          y: 0,
          boxShadow: "0 0 0px rgba(0,0,0,0)",
          duration: 0.3,
          ease: "power2.out"
        })

        const icon = metric.querySelector('.metric-icon')
        if (icon) {
          gsap.to(icon, {
            scale: 1,
            rotation: 0,
            duration: 0.3,
            ease: "power2.out"
          })
        }

        const value = metric.querySelector('.metric-value')
        if (value) {
          gsap.to(value, {
            textShadow: "0 0 0px rgba(59, 130, 246, 0)",
            duration: 0.3
          })
        }
      })
    })
  }

  // Container entrance animation
  useEffect(() => {
    if (!tokenUsage || !containerRef.current) return

    if (!isVisible) {
      setIsVisible(true)
      
      // Container slide up
      gsap.fromTo(containerRef.current,
        { y: 50, opacity: 0, scale: 0.9 },
        { y: 0, opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.7)" }
      )

      createSparkles()
      
      // Stagger animations
      setTimeout(() => animateMetricsEntrance(), 200)
      setTimeout(() => animateCounters(), 400)
      setTimeout(() => animateProgress(), 600)
      setTimeout(() => addMetricHoverEffects(), 800)
    }
  }, [tokenUsage, isVisible])

  // Update animations when token usage changes
  useEffect(() => {
    if (isVisible && tokenUsage) {
      animateCounters()
      animateProgress()
      
      // Pulse effect on update
      gsap.to(containerRef.current, {
        scale: 1.02,
        duration: 0.2,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut"
      })
    }
  }, [tokenUsage])

  if (!tokenUsage || !isVisible) return null

  const metrics = [
    {
      icon: TrendingUp,
      label: 'Input Tokens',
      value: Math.round(animatedValues.input_tokens),
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200'
    },
    {
      icon: Zap,
      label: 'Output Tokens',
      value: Math.round(animatedValues.output_tokens),
      color: 'text-green-500',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200'
    },
    {
      icon: Activity,
      label: 'Total Tokens',
      value: Math.round(animatedValues.input_tokens + animatedValues.output_tokens),
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200'
    },
    {
      icon: Cpu,
      label: 'LLM Calls',
      value: Math.round(animatedValues.llm_calls_count),
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200'
    }
  ]

  return (
    <div 
      ref={containerRef}
      className="bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-200 p-4 shadow-sm relative overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-600" />
          <h3 className="text-sm font-medium text-gray-900">Token Usage</h3>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>Real-time</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>Usage Progress</span>
          <span>{Math.min((totalTokens / 10000) * 100, 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div 
            ref={progressRef}
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300"
            style={{ width: '0%' }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        {metrics.map((metric, index) => (
          <div
            key={metric.label}
            ref={el => metricsRef.current[index] = el}
            className={`${metric.bgColor} ${metric.borderColor} border rounded-lg p-3 cursor-pointer transition-all duration-200 relative overflow-hidden`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className={`metric-icon ${metric.color} mb-1`}>
                  <metric.icon className="w-4 h-4" />
                </div>
                <div className={`metric-value text-lg font-bold ${metric.color}`}>
                  {metric.value.toLocaleString()}
                </div>
                <div className="text-xs text-gray-600">{metric.label}</div>
              </div>
            </div>
            <div className={`absolute inset-0 ${metric.bgColor} opacity-0 hover:opacity-50 transition-opacity duration-300`} />
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="flex items-center justify-between text-xs text-gray-600 pt-3 border-t border-gray-200">
        <div className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          <span>Est. Cost: ${estimatedCost}</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          <span>Avg: {avgTokensPerCall} tokens/call</span>
        </div>
      </div>
    </div>
  )
}
