import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { TextPlugin } from 'gsap/TextPlugin'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import {
  Activity,
  Zap,
  Database,
  FileText,
  Brain,
  Clock,
  Server,
  Layers,
  ChevronDown,
  ChevronRight,
  Upload,
  Search,
  CheckCircle,
  AlertCircle,
  Info,
  TrendingUp,
  Users,
  MessageSquare,
  CheckCircle2
} from 'lucide-react'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger, TextPlugin)
}

export default function RightSidebar({ tokenUsage, processingSteps, activeTools }) {
  const [activeSection, setActiveSection] = useState('system')
  const [expandedSections, setExpandedSections] = useState({
    tokenUsage: true,
    systemStatus: true,
    collections: false,
    capabilities: false,
    streaming: false,
    database: true, // Keep database true if you want it expanded by default in data section
    llm: false,
    vectorstore: false,
    upload: false
  })

  // 🎨 Animation refs
  const containerRef = useRef(null)
  const headerRef = useRef(null)
  const sectionsRef = useRef([])
  const metricsRef = useRef([])
  const particlesRef = useRef(null)
  const auroraRef = useRef(null)
  const magneticRefs = useRef([])
  const glitchRef = useRef(null)
  const liquidProgressRef = useRef(null)

  // Merge real token usage data with mock system data
  const [systemMetrics, setSystemMetrics] = useState({
    tokenUsage: {
      totalTokens: 15420,
      promptTokens: 8320,
      responseTokens: 7100,
      llmCalls: 23,
      avgResponseTime: 1.2,
      costEstimate: 0.42
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

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  // 🌟 ENTRANCE ANIMATIONS
  const animateEntrance = () => {
    if (!containerRef.current) return

    const tl = gsap.timeline()

    // Staggered slide-in with elastic bounce
    tl.fromTo(containerRef.current,
      {
        x: 400,
        opacity: 0,
        skewY: 5,
        scale: 0.8
      },
      {
        x: 0,
        opacity: 1,
        skewY: 0,
        scale: 1,
        duration: 1.2,
        ease: "elastic.out(1, 0.8)"
      }
    )

    // Animate header with morphing effect
    .fromTo(headerRef.current,
      { y: -50, opacity: 0, rotationX: -90 },
      { y: 0, opacity: 1, rotationX: 0, duration: 0.8, ease: "back.out(1.7)" },
      "-=0.6"
    )

    // Stagger sections with wave effect
    .fromTo(sectionsRef.current,
      {
        y: 100,
        opacity: 0,
        scale: 0.5,
        rotationY: 45
      },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        rotationY: 0,
        duration: 0.6,
        stagger: {
          amount: 0.8,
          from: "start",
          ease: "power2.out"
        }
      },
      "-=0.4"
    )
  }

  // ⚡ MAGNETIC HOVER EFFECTS
  const createMagneticEffect = (element) => {
    if (!element) return

    const handleMouseMove = (e) => {
      const rect = element.getBoundingClientRect()
      const x = e.clientX - rect.left - rect.width / 2
      const y = e.clientY - rect.top - rect.height / 2

      gsap.to(element, {
        x: x * 0.3,
        y: y * 0.3,
        rotation: x * 0.1,
        duration: 0.3,
        ease: "power2.out"
      })
    }

    const handleMouseLeave = () => {
      gsap.to(element, {
        x: 0,
        y: 0,
        rotation: 0,
        duration: 0.5,
        ease: "elastic.out(1, 0.3)"
      })
    }

    element.addEventListener('mousemove', handleMouseMove)
    element.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      element.removeEventListener('mousemove', handleMouseMove)
      element.removeEventListener('mouseleave', handleMouseLeave)
    }
  }

  // ✨ FLOATING PARTICLES SYSTEM
  const createFloatingParticles = () => {
    if (!particlesRef.current) return

    const particleCount = 25
    const particles = []

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div')
      particle.className = `absolute w-1 h-1 rounded-full opacity-20 pointer-events-none`
      particle.style.background = `hsl(${200 + Math.random() * 160}, 70%, 60%)`

      particlesRef.current.appendChild(particle)
      particles.push(particle)

      // Random initial position
      gsap.set(particle, {
        x: Math.random() * 400,
        y: Math.random() * 800,
        scale: Math.random() * 0.5 + 0.5
      })

      // Floating animation
      gsap.to(particle, {
        y: `+=${Math.random() * 200 - 100}`,
        x: `+=${Math.random() * 100 - 50}`,
        rotation: Math.random() * 360,
        duration: Math.random() * 10 + 5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      })

      // Twinkling effect
      gsap.to(particle, {
        opacity: Math.random() * 0.3 + 0.1,
        scale: Math.random() * 0.8 + 0.4,
        duration: Math.random() * 3 + 1,
        repeat: -1,
        yoyo: true,
        ease: "power2.inOut"
      })
    }

    return particles
  }

  // 🌈 AURORA BACKGROUND EFFECT
  const createAuroraEffect = () => {
    if (!auroraRef.current) return

    const auroras = []
    for (let i = 0; i < 3; i++) {
      const aurora = document.createElement('div')
      aurora.className = 'absolute inset-0 opacity-5 pointer-events-none'
      aurora.style.background = `radial-gradient(ellipse at ${Math.random() * 100}% ${Math.random() * 100}%,
        hsl(${200 + i * 40}, 80%, 60%) 0%,
        transparent 50%)`

      auroraRef.current.appendChild(aurora)
      auroras.push(aurora)

      gsap.to(aurora, {
        background: `radial-gradient(ellipse at ${Math.random() * 100}% ${Math.random() * 100}%,
          hsl(${220 + i * 40}, 80%, 60%) 0%,
          transparent 50%)`,
        duration: Math.random() * 8 + 4,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      })
    }
  }

  // 💫 RIPPLE WAVE EFFECT
  const createRippleEffect = (element, event) => {
    const rect = element.getBoundingClientRect()
    const ripple = document.createElement('div')
    ripple.className = 'absolute rounded-full bg-blue-400 opacity-30 pointer-events-none'

    const size = Math.max(rect.width, rect.height)
    ripple.style.width = ripple.style.height = size + 'px'
    ripple.style.left = (event.clientX - rect.left - size / 2) + 'px'
    ripple.style.top = (event.clientY - rect.top - size / 2) + 'px'

    element.appendChild(ripple)

    gsap.fromTo(ripple,
      { scale: 0, opacity: 0.6 },
      {
        scale: 2,
        opacity: 0,
        duration: 0.6,
        ease: "power2.out",
        onComplete: () => ripple.remove()
      }
    )
  }

  // Initialize all animations
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Delay initial animations to ensure DOM is ready
    setTimeout(() => {
      animateEntrance()
      createFloatingParticles()
      createAuroraEffect()

      // Add magnetic effects to interactive elements
      magneticRefs.current.forEach(ref => {
        if (ref) createMagneticEffect(ref)
      })
    }, 100)

    return () => {
      gsap.killTweensOf([containerRef.current, headerRef.current, ...sectionsRef.current])
    }
  }, [])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'active': return <CheckCircle className="w-3 h-3 text-green-500" />
      case 'warning': return <AlertCircle className="w-3 h-3 text-yellow-500" />
      case 'error': return <AlertCircle className="w-3 h-3 text-red-500" />
      case 'pending':
      case 'migrating': return <Clock className="w-3 h-3 text-blue-500" />
      case 'planned': return <Info className="w-3 h-3 text-purple-500" />
      default: return <Info className="w-3 h-3 text-gray-500" />
    }
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num)
  }

  // Update system metrics with real data from props
  useEffect(() => {
    if (tokenUsage) {
      setSystemMetrics(prev => ({
        ...prev,
        tokenUsage: {
          ...prev.tokenUsage,
          ...tokenUsage
        }
      }))
    }
  }, [tokenUsage])

  // Update processing steps and active tools
  useEffect(() => {
    if (processingSteps || activeTools) {
      setSystemMetrics(prev => ({
        ...prev,
        streamingStatus: {
          ...prev.streamingStatus,
          activeStreams: activeTools?.length || 0,
          processingQueue: processingSteps || [],
          lastUpdate: new Date()
        }
      }))
    }
  }, [processingSteps, activeTools])

  // Simulate real-time updates for demo data
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        streamingStatus: {
          ...prev.streamingStatus,
          lastUpdate: new Date(),
          totalQueries: prev.streamingStatus.totalQueries + (Math.random() > 0.9 ? 1 : 0)
        }
      }))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div
      ref={containerRef}
      className="h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-slate-900 relative overflow-hidden"
    >
      {/* Aurora Background */}
      <div ref={auroraRef} className="absolute inset-0 z-0" />

      {/* Floating Particles */}
      <div ref={particlesRef} className="absolute inset-0 z-0" />

      {/* Header with enhanced animations */}
      <div
        ref={headerRef}
        className="p-3 border-b border-gray-700/50 backdrop-blur-sm relative z-10"
      >
        <div className="flex items-center gap-2 mb-2">
          <div
            ref={el => magneticRefs.current[0] = el}
            className="p-1.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg backdrop-blur-sm"
          >
            <Brain className="w-4 h-4 text-blue-400" />
          </div>
          <h2 className="text-sm font-semibold text-white">Brain LLM Monitor</h2>
        </div>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant={activeSection === 'system' ? 'default' : 'ghost'}
            onClick={(e) => {
              createRippleEffect(e.currentTarget, e);
              setActiveSection('system');
              setExpandedSections(prev => ({
                ...prev,
                tokenUsage: true,
                systemStatus: true,
                collections: false,
                capabilities: false,
                streaming: false,
              }));
            }}
            className="text-xs h-6 px-2 rounded-lg font-medium transition-all duration-300 hover:scale-105"
            ref={el => magneticRefs.current[1] = el}
          >
            <Activity className="w-3 h-3 mr-1" />
            System
          </Button>
          <Button
            size="sm"
            variant={activeSection === 'data' ? 'default' : 'ghost'}
            onClick={(e) => {
              createRippleEffect(e.currentTarget, e);
              setActiveSection('data');
              setExpandedSections(prev => ({
                ...prev,
                database: true,
                llm: true,
                vectorstore: true,
              }));
            }}
            className="text-xs h-6 px-2 rounded-lg font-medium transition-all duration-300 hover:scale-105"
            ref={el => magneticRefs.current[2] = el}
          >
            <Database className="w-3 h-3 mr-1" />
            Data
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-2">
        {activeSection === 'system' ? (
          <div className="space-y-2">
            {/* Token Usage Section */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('tokenUsage')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-blue-500/20 rounded-lg">
                    <Zap className="w-3 h-3 text-blue-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">Token Usage</span>
                </div>
                {expandedSections.tokenUsage ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.tokenUsage && (
                <div className="px-2 pb-2 space-y-2">
                  <div className="grid grid-cols-2 gap-1.5 text-xs">
                    <div className="bg-gray-700/60 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">Total Tokens</div>
                      <div className="text-white font-semibold text-xs">{formatNumber(systemMetrics.tokenUsage.totalTokens)}</div>
                    </div>
                    <div className="bg-gray-700/60 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">LLM Calls</div>
                      <div className="text-white font-semibold text-xs">{systemMetrics.tokenUsage.llmCalls}</div>
                    </div>
                    <div className="bg-gray-700/60 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">Prompt</div>
                      <div className="text-blue-400 font-semibold text-xs">{formatNumber(systemMetrics.tokenUsage.promptTokens)}</div>
                    </div>
                    <div className="bg-gray-700/60 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">Response</div>
                      <div className="text-green-400 font-semibold text-xs">{formatNumber(systemMetrics.tokenUsage.responseTokens)}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 text-xs">
                    <div className="bg-gray-700/60 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">Avg Time</div>
                      <div className="text-yellow-400 font-semibold text-xs">{systemMetrics.tokenUsage.avgResponseTime}s</div>
                    </div>
                    <div className="bg-gray-700/60 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">Est. Cost</div>
                      <div className="text-purple-400 font-semibold text-xs">${systemMetrics.tokenUsage.costEstimate}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* System Status */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('systemStatus')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-green-500/20 rounded-lg">
                    <Server className="w-3 h-3 text-green-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">System Health</span>
                </div>
                {expandedSections.systemStatus ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.systemStatus && (
                <div className="px-2 pb-2 space-y-1">
                  {Object.entries(systemMetrics.systemHealth).map(([service, status]) => (
                    <div key={service} className="flex items-center justify-between p-1.5 bg-gray-700/40 rounded-lg border border-gray-600/30">
                      <div className="flex items-center gap-2">
                        <div className="flex items-center justify-center w-4 h-4">
                          {getStatusIcon(status)}
                        </div>
                        <span className="text-xs text-gray-300 capitalize font-medium">{service.replace(/([A-Z])/g, ' $1')}</span>
                      </div>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
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

            {/* Streaming Status */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('streaming')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-cyan-500/20 rounded-lg">
                    <MessageSquare className="w-3 h-3 text-cyan-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">Query Processing</span>
                </div>
                {expandedSections.streaming ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.streaming && (
                <div className="px-2 pb-2 space-y-2">
                  <div className="grid grid-cols-2 gap-1.5">
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">Active Streams</div>
                      <div className="text-white font-semibold text-xs">{systemMetrics.streamingStatus.activeStreams}</div>
                    </div>
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">Total Queries</div>
                      <div className="text-white font-semibold text-xs">{formatNumber(systemMetrics.streamingStatus.totalQueries)}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5">
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">Avg Processing</div>
                      <div className="text-cyan-400 font-semibold text-xs">{systemMetrics.streamingStatus.avgProcessingTime}s</div>
                    </div>
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 mb-0.5 text-xs">Last Update</div>
                      <div className="text-gray-300 font-medium text-xs">{systemMetrics.streamingStatus.lastUpdate.toLocaleTimeString()}</div>
                    </div>
                  </div>

                  {/* Active Tools Display */}
                  {activeTools && activeTools.length > 0 && (
                    <div className="bg-gray-700/30 rounded-lg p-2 border border-gray-600/30">
                      <div className="text-xs text-gray-300 font-medium mb-2 flex items-center gap-2">
                        <Brain className="w-3 h-3 text-cyan-400" />
                        Active AI Tools
                      </div>
                      <div className="space-y-1">
                        {activeTools.map((tool, index) => (
                          <div key={index} className="flex items-center gap-2 p-1.5 bg-gray-800/40 rounded-lg">
                            <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></div>
                            <span className="text-xs text-cyan-300 font-medium">{tool}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing Steps Display */}
                  {processingSteps && processingSteps.length > 0 && (
                    <div className="bg-gray-700/30 rounded-lg p-2 border border-gray-600/30">
                      <div className="text-xs text-gray-300 font-medium mb-2 flex items-center gap-2">
                        <Clock className="w-3 h-3 text-yellow-400" />
                        Thinking Process
                      </div>
                      <div className="max-h-24 overflow-y-auto space-y-1">
                        {processingSteps.slice(-4).map((step, index) => (
                          <div key={index} className="text-xs text-gray-300 leading-relaxed p-1.5 bg-gray-800/40 rounded-lg">
                            <span className="text-blue-400 mr-1">•</span> {step}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Vector Collections */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('collections')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-purple-500/20 rounded-lg">
                    <Layers className="w-3 h-3 text-purple-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">Vector Collections</span>
                </div>
                {expandedSections.collections ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.collections && (
                <div className="px-2 pb-2 space-y-1.5">
                  <div className="grid grid-cols-2 gap-1.5">
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">DQ Rules</div>
                      <div className="text-purple-400 font-semibold text-xs">{formatNumber(systemMetrics.collections.dqRules)}</div>
                    </div>
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">Conversations</div>
                      <div className="text-white font-semibold text-xs">{formatNumber(systemMetrics.collections.conversations)}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5">
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">Query Cache</div>
                      <div className="text-cyan-400 font-semibold text-xs">{formatNumber(systemMetrics.collections.queryCache)}</div>
                    </div>
                    <div className="bg-gray-700/40 rounded-lg p-1.5 border border-gray-600/30">
                      <div className="text-gray-400 text-xs mb-0.5">Schema Embeddings</div>
                      <div className="text-green-400 font-semibold text-xs">{formatNumber(systemMetrics.collections.schemaEmbeddings)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* AI Tools */}
            <div className="bg-gray-800/60 rounded-lg border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('capabilities')}
                className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-cyan-500/20 rounded-lg">
                    <Brain className="w-4 h-4 text-cyan-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">AI Tools</span>
                </div>
                {expandedSections.capabilities ?
                  <ChevronDown className="w-4 h-4 text-gray-400" /> :
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                }
              </button>
              {expandedSections.capabilities && (
                <div className="px-3 pb-3 space-y-2">
                  {Object.entries(systemMetrics.aiCapabilities).map(([capability, data]) => (
                    <div key={capability} className="flex items-center justify-between p-2 bg-gray-700/40 rounded-lg border border-gray-600/30">
                      <div className="flex items-center gap-2">
                        <div className="flex items-center justify-center w-5 h-5">
                          {getStatusIcon(data.status)}
                        </div>
                        <span className="text-xs text-gray-300 capitalize font-medium">
                          {capability.replace(/([A-Z])/g, ' $1')}
                        </span>
                      </div>
                      <span className="text-xs text-cyan-400 font-semibold">{data.usage}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* System Actions */}
            <div className="bg-gray-800/60 rounded-lg border border-gray-700/50 backdrop-blur-sm p-3">
              <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
                <Activity className="w-3 h-3 text-blue-400" />
                System Actions
              </h3>
              <div className="space-y-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white hover:bg-gray-700/50 h-8 rounded-lg transition-all"
                >
                  <Upload className="w-3 h-3 mr-2" />
                  Upload DQ Rules (Soon)
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white hover:bg-gray-700/50 h-8 rounded-lg transition-all"
                >
                  <Search className="w-3 h-3 mr-2" />
                  Search Collections
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white hover:bg-gray-700/50 h-8 rounded-lg transition-all"
                >
                  <TrendingUp className="w-3 h-3 mr-2" />
                  View Analytics
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white hover:bg-gray-700/50 h-8 rounded-lg transition-all"
                >
                  <FileText className="w-3 h-3 mr-2" />
                  Export Logs
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* Data Configuration Section */
          <div className="space-y-2">
            {/* Database Configuration */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('database')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-green-500/20 rounded-lg">
                    <Database className="w-3 h-3 text-green-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">Database Connection</span>
                </div>
                {expandedSections.database ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.database && (
                <div className="px-2 pb-2 space-y-2">
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">Database Type</label>
                    <select className="w-full bg-gray-800 border border-gray-600 rounded text-xs text-white p-1">
                      <option>PostgreSQL</option>
                      <option>MySQL</option>
                      <option>SQLite</option>
                    </select>
                  </div>
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">Host</label>
                    <input type="text" placeholder="localhost" className="w-full bg-gray-800 border border-gray-600 rounded text-white text-xs p-1" />
                  </div>
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">Port</label>
                    <input type="number" placeholder="5432" className="w-full bg-gray-800 border border-gray-600 rounded text-white text-xs p-1" />
                  </div>
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">Username</label>
                    <input type="text" placeholder="user" className="w-full bg-gray-800 border border-gray-600 rounded text-white text-xs p-1" />
                  </div>
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">Password</label>
                    <input type="password" placeholder="********" className="w-full bg-gray-800 border border-gray-600 rounded text-white text-xs p-1" />
                  </div>
                  <Button
                    size="sm"
                    className="w-full justify-center text-xs h-8 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 transition-all duration-300"
                  >
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Test Connection
                  </Button>
                </div>
              )}
            </div>

            {/* LLM Configuration Section (Example of another data-related section) */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('llm')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-purple-500/20 rounded-lg">
                    <Brain className="w-3 h-3 text-purple-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">LLM Configuration</span>
                </div>
                {expandedSections.llm ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.llm && (
                <div className="px-2 pb-2 space-y-2">
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">LLM Provider</label>
                    <select className="w-full bg-gray-800 border border-gray-600 rounded text-xs text-white p-1">
                      <option>Google Gemini</option>
                      <option>OpenAI GPT</option>
                      <option>Ollama</option>
                    </select>
                  </div>
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">API Key</label>
                    <input type="password" placeholder="sk-**********" className="w-full bg-gray-800 border border-gray-600 rounded text-white text-xs p-1" />
                  </div>
                  <Button
                    size="sm"
                    className="w-full justify-center text-xs h-8 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 transition-all duration-300"
                  >
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Save Configuration
                  </Button>
                </div>
              )}
            </div>

            {/* Vector Store Configuration */}
            <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 backdrop-blur-sm">
              <button
                onClick={() => toggleSection('vectorstore')}
                className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-700/30 transition-all duration-200 rounded-xl"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-yellow-500/20 rounded-lg">
                    <Layers className="w-3 h-3 text-yellow-400" />
                  </div>
                  <span className="text-xs font-semibold text-white">Vector Store</span>
                </div>
                {expandedSections.vectorstore ?
                  <ChevronDown className="w-3 h-3 text-gray-400" /> :
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                }
              </button>
              {expandedSections.vectorstore && (
                <div className="px-2 pb-2 space-y-2">
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">Vector DB</label>
                    <select className="w-full bg-gray-800 border border-gray-600 rounded text-xs text-white p-1">
                      <option>ChromaDB</option>
                      <option>Pinecone</option>
                      <option>Weaviate</option>
                    </select>
                  </div>
                  <div className="bg-gray-700/40 rounded-lg p-2 border border-gray-600/30">
                    <label className="text-xs text-gray-400 block mb-1">API Endpoint</label>
                    <input type="text" placeholder="https://api.vectordb.com" className="w-full bg-gray-800 border border-gray-600 rounded text-white text-xs p-1" />
                  </div>
                  <Button
                    size="sm"
                    className="w-full justify-center text-xs h-8 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 transition-all duration-300"
                  >
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Connect
                  </Button>
                </div>
              )}
            </div>

            {/* Data Upload Actions */}
            <div className="bg-gray-800/60 rounded-lg border border-gray-700/50 backdrop-blur-sm p-3">
              <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
                <Upload className="w-3 h-3 text-blue-400" />
                Data Actions
              </h3>
              <div className="space-y-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white hover:bg-gray-700/50 h-8 rounded-lg transition-all"
                >
                  <FileText className="w-3 h-3 mr-2" />
                  Upload Schema Files
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-gray-300 hover:text-white hover:bg-gray-700/50 h-8 rounded-lg transition-all"
                >
                  <Users className="w-3 h-3 mr-2" />
                  Manage User Data
                </Button>
              </div>
            </div>
          </div>
        )}
      </ScrollArea>
    </div>
  )
}