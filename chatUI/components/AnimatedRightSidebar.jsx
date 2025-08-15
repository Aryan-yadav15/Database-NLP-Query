'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { 
  Activity, 
  Database, 
  Server, 
  Zap, 
  MessageSquare, 
  ChevronDown, 
  ChevronRight,
  Brain,
  Layers,
  Upload,
  Search,
  TrendingUp,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  Wifi,
  WifiOff
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

export default function AnimatedRightSidebar({ tokenUsage, processingSteps = [], activeTools = [] }) {
  const [activeSection, setActiveSection] = useState('system')
  const [expandedSections, setExpandedSections] = useState({
    tokenUsage: true,
    systemStatus: true,
    collections: false,
    capabilities: false,
    streaming: false,
    database: true,
    llm: false,
    vectorstore: false,
    upload: false
  })

  // Refs for animations
  const containerRef = useRef(null)
  const headerRef = useRef(null)
  const sectionsRef = useRef([])
  const metricsRef = useRef([])
  const particlesRef = useRef(null)
  const pulseRef = useRef(null)

  // Enhanced system metrics with animation states
  const [systemMetrics, setSystemMetrics] = useState({
    tokenUsage: {
      totalTokens: 15420,
      promptTokens: 8320,
      responseTokens: 7100,
      llmCalls: 23,
      avgResponseTime: 1.2,
      costEstimate: 0.42,
      isAnimating: false
    },
    collections: {
      dqRules: 847,
      conversations: 156,
      queryCache: 89,
      schemaEmbeddings: 42
    },
    systemHealth: {
      chromaDB: 'healthy',
      postgresql: 'healthy',
      ollama: 'pending',
      fastAPI: 'healthy',
      gemini: 'healthy'
    },
    streamingStatus: {
      activeStreams: 0,
      lastUpdate: new Date(),
      processingQueue: [],
      totalQueries: 234,
      avgProcessingTime: 2.3
    },
    aiCapabilities: {
      sqlGeneration: { status: 'active', usage: 89 },
      dqRuleMatching: { status: 'active', usage: 67 },
      schemaAnalysis: { status: 'active', usage: 23 },
      conversationalAI: { status: 'active', usage: 156 },
      pdfUpload: { status: 'planned', usage: 0 },
      nomicEmbeddings: { status: 'migrating', usage: 0 }
    }
  })

  // Animation helper functions
  const animateCardEntrance = (element, delay = 0) => {
    gsap.fromTo(element, 
      { 
        y: 50, 
        opacity: 0, 
        scale: 0.8,
        rotationX: -15
      },
      { 
        y: 0, 
        opacity: 1, 
        scale: 1,
        rotationX: 0,
        duration: 0.8,
        delay,
        ease: "back.out(1.7)"
      }
    )
  }

  const animateNumberCounter = (element, startValue, endValue, duration = 2) => {
    const obj = { value: startValue }
    gsap.to(obj, {
      value: endValue,
      duration,
      ease: "power2.out",
      onUpdate: () => {
        element.textContent = Math.round(obj.value).toLocaleString()
      }
    })
  }

  const createMagneticEffect = (element) => {
    element.addEventListener('mouseenter', (e) => {
      gsap.to(element, {
        scale: 1.05,
        duration: 0.3,
        ease: "power2.out"
      })
      
      // Add glow effect
      gsap.to(element, {
        boxShadow: "0 0 20px rgba(59, 130, 246, 0.5)",
        duration: 0.3
      })
    })

    element.addEventListener('mouseleave', () => {
      gsap.to(element, {
        scale: 1,
        boxShadow: "0 0 0px rgba(59, 130, 246, 0)",
        duration: 0.3,
        ease: "power2.out"
      })
    })

    element.addEventListener('mousemove', (e) => {
      const rect = element.getBoundingClientRect()
      const x = e.clientX - rect.left - rect.width / 2
      const y = e.clientY - rect.top - rect.height / 2
      
      gsap.to(element, {
        x: x * 0.1,
        y: y * 0.1,
        duration: 0.3,
        ease: "power2.out"
      })
    })
  }

  const createFloatingParticles = () => {
    const particles = []
    for (let i = 0; i < 20; i++) {
      const particle = document.createElement('div')
      particle.className = 'absolute w-1 h-1 bg-blue-400 rounded-full opacity-20'
      particle.style.left = Math.random() * 100 + '%'
      particle.style.top = Math.random() * 100 + '%'
      particlesRef.current?.appendChild(particle)
      particles.push(particle)

      // Animate particles
      gsap.to(particle, {
        y: `-=${Math.random() * 100 + 50}`,
        x: `+=${Math.random() * 60 - 30}`,
        opacity: 0,
        duration: Math.random() * 3 + 2,
        repeat: -1,
        ease: "power1.out"
      })
    }
  }

  const animateStatusPulse = (status) => {
    const colors = {
      healthy: '#10b981',
      warning: '#f59e0b',
      pending: '#3b82f6',
      error: '#ef4444'
    }
    
    if (pulseRef.current) {
      gsap.to(pulseRef.current, {
        backgroundColor: colors[status] || colors.pending,
        scale: 1.2,
        duration: 0.5,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut"
      })
    }
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => {
      const newState = { ...prev, [section]: !prev[section] }
      
      // Animate expansion/collapse
      const sectionElement = sectionsRef.current.find(el => el?.dataset?.section === section)
      if (sectionElement) {
        const content = sectionElement.querySelector('.section-content')
        if (content) {
          if (newState[section]) {
            gsap.fromTo(content,
              { height: 0, opacity: 0 },
              { height: 'auto', opacity: 1, duration: 0.5, ease: "power2.out" }
            )
          } else {
            gsap.to(content, {
              height: 0,
              opacity: 0,
              duration: 0.3,
              ease: "power2.in"
            })
          }
        }
      }
      
      return newState
    })
  }

  const getStatusIcon = (status) => {
    const iconProps = { className: "w-3 h-3" }
    
    switch (status) {
      case 'healthy':
        return <CheckCircle2 {...iconProps} className="w-3 h-3 text-green-400" />
      case 'warning':
        return <AlertTriangle {...iconProps} className="w-3 h-3 text-yellow-400" />
      case 'pending':
        return <Loader2 {...iconProps} className="w-3 h-3 text-blue-400 animate-spin" />
      case 'error':
        return <XCircle {...iconProps} className="w-3 h-3 text-red-400" />
      default:
        return <Wifi {...iconProps} className="w-3 h-3 text-gray-400" />
    }
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  // Initialize animations on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    const tl = gsap.timeline()
    
    // Header entrance animation
    tl.fromTo(headerRef.current,
      { y: -50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8, ease: "back.out(1.7)" }
    )

    // Staggered section animations
    sectionsRef.current.forEach((section, index) => {
      if (section) {
        animateCardEntrance(section, index * 0.1)
      }
    })

    // Create floating particles
    createFloatingParticles()

    // Add magnetic effects to interactive elements
    const buttons = containerRef.current?.querySelectorAll('button')
    buttons?.forEach(button => createMagneticEffect(button))

    // Animate metrics counters
    metricsRef.current.forEach(metric => {
      if (metric) {
        const value = parseInt(metric.textContent.replace(/[^\d]/g, ''))
        if (value) {
          animateNumberCounter(metric, 0, value, 1.5)
        }
      }
    })

    return () => {
      gsap.killTweensOf([headerRef.current, ...sectionsRef.current, ...metricsRef.current])
    }
  }, [])

  // Update system metrics with real data from props
  useEffect(() => {
    if (tokenUsage) {
      setSystemMetrics(prev => ({
        ...prev,
        tokenUsage: {
          ...prev.tokenUsage,
          ...tokenUsage,
          isAnimating: true
        }
      }))

      // Animate token usage update
      setTimeout(() => {
        setSystemMetrics(prev => ({
          ...prev,
          tokenUsage: { ...prev.tokenUsage, isAnimating: false }
        }))
      }, 1000)
    }
  }, [tokenUsage])

  // Simulate real-time updates for demo
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        streamingStatus: {
          ...prev.streamingStatus,
          lastUpdate: new Date(),
          totalQueries: prev.streamingStatus.totalQueries + Math.floor(Math.random() * 3)
        }
      }))

      // Animate status pulse
      animateStatusPulse('healthy')
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-gradient-to-b from-gray-900 to-gray-800 relative overflow-hidden">
      {/* Floating Particles Background */}
      <div ref={particlesRef} className="absolute inset-0 pointer-events-none" />
      
      {/* Animated Header */}
      <div ref={headerRef} className="p-4 border-b border-gray-700 bg-gradient-to-r from-gray-800 to-gray-700">
        <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          <div ref={pulseRef} className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          Brain LLM Monitor
        </h2>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={activeSection === 'system' ? 'default' : 'ghost'}
            onClick={() => setActiveSection('system')}
            className="text-xs h-7 transition-all duration-300 hover:scale-105"
          >
            <Activity className="w-3 h-3 mr-1" />
            System
          </Button>
          <Button
            size="sm"
            variant={activeSection === 'data' ? 'default' : 'ghost'}
            onClick={() => setActiveSection('data')}
            className="text-xs h-7 transition-all duration-300 hover:scale-105"
          >
            <Database className="w-3 h-3 mr-1" />
            Data
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {/* Token Usage Section */}
          <div 
            ref={el => sectionsRef.current[0] = el}
            data-section="tokenUsage"
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg hover:shadow-blue-500/20 transition-all duration-300"
          >
            <button
              onClick={() => toggleSection('tokenUsage')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/50 transition-all duration-300 rounded-t-lg group"
            >
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform duration-300" />
                <span className="text-sm font-medium text-white">Token Usage</span>
                {systemMetrics.tokenUsage.isAnimating && (
                  <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
                )}
              </div>
              {expandedSections.tokenUsage ? 
                <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" />
              }
            </button>
            {expandedSections.tokenUsage && (
              <div className="section-content px-3 pb-3 space-y-3">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gradient-to-r from-gray-700 to-gray-600 rounded p-2 hover:scale-105 transition-transform duration-300">
                    <div className="text-gray-400">Total Tokens</div>
                    <div ref={el => metricsRef.current[0] = el} className="text-white font-medium text-lg">
                      {formatNumber(systemMetrics.tokenUsage.totalTokens)}
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-gray-700 to-gray-600 rounded p-2 hover:scale-105 transition-transform duration-300">
                    <div className="text-gray-400">LLM Calls</div>
                    <div ref={el => metricsRef.current[1] = el} className="text-white font-medium text-lg">
                      {systemMetrics.tokenUsage.llmCalls}
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-blue-800 to-blue-700 rounded p-2 hover:scale-105 transition-transform duration-300">
                    <div className="text-blue-200">Prompt</div>
                    <div ref={el => metricsRef.current[2] = el} className="text-blue-400 font-medium text-lg">
                      {formatNumber(systemMetrics.tokenUsage.promptTokens)}
                    </div>
                  </div>
                  <div className="bg-gradient-to-r from-green-800 to-green-700 rounded p-2 hover:scale-105 transition-transform duration-300">
                    <div className="text-green-200">Response</div>
                    <div ref={el => metricsRef.current[3] = el} className="text-green-400 font-medium text-lg">
                      {formatNumber(systemMetrics.tokenUsage.responseTokens)}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gradient-to-r from-yellow-800 to-yellow-700 rounded p-2 hover:scale-105 transition-transform duration-300">
                    <div className="text-yellow-200">Avg Time</div>
                    <div className="text-yellow-400 font-medium text-lg">{systemMetrics.tokenUsage.avgResponseTime}s</div>
                  </div>
                  <div className="bg-gradient-to-r from-purple-800 to-purple-700 rounded p-2 hover:scale-105 transition-transform duration-300">
                    <div className="text-purple-200">Est. Cost</div>
                    <div className="text-purple-400 font-medium text-lg">${systemMetrics.tokenUsage.costEstimate}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* System Health Section */}
          <div 
            ref={el => sectionsRef.current[1] = el}
            data-section="systemStatus"
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg hover:shadow-green-500/20 transition-all duration-300"
          >
            <button
              onClick={() => toggleSection('systemStatus')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/50 transition-all duration-300 rounded-t-lg group"
            >
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-green-400 group-hover:scale-110 transition-transform duration-300" />
                <span className="text-sm font-medium text-white">System Health</span>
              </div>
              {expandedSections.systemStatus ? 
                <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" />
              }
            </button>
            {expandedSections.systemStatus && (
              <div className="section-content px-3 pb-3 space-y-2">
                {Object.entries(systemMetrics.systemHealth).map(([service, status], index) => (
                  <div key={service} className="flex items-center justify-between hover:bg-gray-700/30 rounded p-2 transition-all duration-300">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(status)}
                      <span className="text-xs text-gray-300 capitalize">{service.replace(/([A-Z])/g, ' $1')}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded transition-all duration-300 ${
                      status === 'healthy' ? 'bg-green-500/20 text-green-400' :
                      status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                      status === 'pending' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Additional sections with similar animations... */}
          {/* Vector Collections */}
          <div 
            ref={el => sectionsRef.current[2] = el}
            data-section="collections"
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg hover:shadow-purple-500/20 transition-all duration-300"
          >
            <button
              onClick={() => toggleSection('collections')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/50 transition-all duration-300 rounded-t-lg group"
            >
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform duration-300" />
                <span className="text-sm font-medium text-white">Vector Collections</span>
              </div>
              {expandedSections.collections ? 
                <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" />
              }
            </button>
            {expandedSections.collections && (
              <div className="section-content px-3 pb-3 space-y-2">
                {Object.entries(systemMetrics.collections).map(([key, value], index) => (
                  <div key={key} className="flex items-center justify-between hover:bg-gray-700/30 rounded p-2 transition-all duration-300">
                    <span className="text-xs text-gray-300 capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                    <span className="text-xs text-white font-medium">{formatNumber(value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* System Actions with enhanced animations */}
          <div 
            ref={el => sectionsRef.current[3] = el}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 p-3 shadow-lg"
          >
            <h3 className="text-sm font-medium text-white mb-3">System Actions</h3>
            <div className="space-y-2">
              {[
                { icon: Upload, text: "Upload DQ Rules (Soon)", color: "text-blue-400" },
                { icon: Search, text: "Search Collections", color: "text-green-400" },
                { icon: TrendingUp, text: "View Analytics", color: "text-yellow-400" },
                { icon: FileText, text: "Export Logs", color: "text-purple-400" }
              ].map((action, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white h-7 hover:scale-105 transition-all duration-300 hover:bg-gray-700/50"
                >
                  <action.icon className={`w-3 h-3 mr-2 ${action.color}`} />
                  {action.text}
                </Button>
              ))}
            </div>
          </div>

          {/* Enhanced Footer */}
          <div className="text-center text-xs text-gray-500 space-y-1 pt-2">
            <div className="font-medium text-gray-400">Brain LLM v2.0</div>
            <div>FastAPI + ChromaDB + Gemini</div>
            <div className="flex items-center justify-center gap-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>System Operational</span>
            </div>
            <div className="text-gray-600">
              LangChain • PostgreSQL • Ollama
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  )
}
