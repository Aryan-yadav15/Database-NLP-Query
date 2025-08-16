'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { TextPlugin } from 'gsap/TextPlugin'
import { User, Bot, Copy, ThumbsUp, ThumbsDown, Sparkles, CheckCircle, Database, BarChart3, Shield, Code } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(TextPlugin)
}

// Component for rendering SQL results table
const SQLResultTable = ({ table, sql }) => {
  if (!table || !table.columns || !table.rows) return null

  return (
    <Card className="mt-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-500" />
          SQL Query Results
        </CardTitle>
        {sql && (
          <div className="bg-gray-100 rounded p-2 mt-2">
            <code className="text-xs text-gray-700">{sql}</code>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50">
                {table.columns.map((column, index) => (
                  <th key={index} className="px-3 py-2 text-left font-medium text-gray-700 border-b">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-3 py-2 text-gray-900 border-b">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

// Component for rendering network graph visualization
const NetworkGraph = ({ graph }) => {
  const graphRef = useRef(null)
  const networkRef = useRef(null)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [layoutType, setLayoutType] = useState('hierarchical') // hierarchical, physics, circular

  const createNetwork = async (vis, layoutMode = 'hierarchical') => {
    if (!graphRef.current) return

    // Transform data for vis-network
    const nodes = new vis.DataSet(
      graph.nodes.map(node => ({
        id: node.id,
        label: node.label.replace('public.', ''),
        title: `Table: ${node.label}\nClick for details`, // Tooltip
        color: {
          background: '#3b82f6',
          border: '#1e40af',
          highlight: {
            background: '#2563eb',
            border: '#1d4ed8'
          }
        },
        font: {
          color: 'white',
          size: 14,
          face: 'Inter, system-ui, sans-serif',
          bold: true
        },
        shape: 'box',
        margin: 12,
        widthConstraint: {
          minimum: 100,
          maximum: 140
        },
        heightConstraint: {
          minimum: 40
        }
      }))
    )

    const edges = new vis.DataSet(
      graph.edges.map((edge, index) => ({
        id: index,
        from: edge.from,
        to: edge.to,
        label: edge.label || '',
        title: `Relationship: ${edge.label || 'connects'}`,
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 1,
            type: 'arrow'
          }
        },
        color: {
          color: '#64748b',
          highlight: '#475569',
          hover: '#374151'
        },
        font: {
          size: 11,
          color: '#374151',
          background: 'rgba(255,255,255,0.9)',
          strokeWidth: 2,
          strokeColor: 'white'
        },
        smooth: {
          type: layoutMode === 'hierarchical' ? 'vertical' : 'curvedCW',
          roundness: layoutMode === 'hierarchical' ? 0 : 0.2
        },
        width: 2
      }))
    )

    const data = { nodes, edges }

    let options = {
      nodes: {
        borderWidth: 2,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.15)',
          size: 8,
          x: 3,
          y: 3
        },
        chosen: {
          node: function(values, id, selected, hovering) {
            values.shadow = true
            values.shadowSize = 12
            values.shadowColor = 'rgba(59, 130, 246, 0.4)'
          }
        }
      },
      edges: {
        width: 2,
        selectionWidth: 4,
        hoverWidth: 3,
        chosen: {
          edge: function(values, id, selected, hovering) {
            values.width = 3
            values.color = '#3b82f6'
          }
        }
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        selectConnectedEdges: true,
        hover: true,
        hoverConnectedEdges: true,
        keyboard: {
          enabled: true,
          speed: { x: 10, y: 10, zoom: 0.02 }
        },
        multiselect: false,
        tooltipDelay: 300,
        zoomSpeed: 1
      },
      configure: {
        enabled: false
      }
    }

    // Different layout configurations
    switch (layoutMode) {
      case 'hierarchical':
        options.physics = {
          enabled: false // Disable physics for hierarchical
        }
        options.layout = {
          improvedLayout: true,
          hierarchical: {
            enabled: true,
            levelSeparation: 180,
            nodeSpacing: 160,
            treeSpacing: 200,
            blockShifting: true,
            edgeMinimization: true,
            parentCentralization: true,
            direction: 'UD',
            sortMethod: 'hubsize'
          }
        }
        break
      
      case 'physics':
        options.physics = {
          enabled: true,
          solver: 'repulsion',
          repulsion: {
            centralGravity: 0.3,
            springLength: 200,
            springConstant: 0.05,
            nodeDistance: 180,
            damping: 0.09
          },
          maxVelocity: 50,
          minVelocity: 0.1,
          timestep: 0.5,
          adaptiveTimestep: true,
          stabilization: {
            enabled: true,
            iterations: 1000,
            updateInterval: 25
          }
        }
        options.layout = {
          improvedLayout: true,
          hierarchical: false
        }
        break
      
      case 'circular':
        options.physics = {
          enabled: false
        }
        options.layout = {
          improvedLayout: false,
          hierarchical: false
        }
        // Position nodes in a circle
        const nodeCount = graph.nodes.length
        const radius = Math.max(150, nodeCount * 15)
        const centerX = 0, centerY = 0
        
        graph.nodes.forEach((node, index) => {
          const angle = (index / nodeCount) * 2 * Math.PI
          nodes.update({
            id: node.id,
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle),
            physics: false
          })
        })
        break
    }

    // Destroy existing network if it exists
    if (networkRef.current) {
      networkRef.current.destroy()
    }

    // Create new network
    networkRef.current = new vis.Network(graphRef.current, data, options)

    // Add event listeners for interactions
    networkRef.current.on('click', function (params) {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0]
        const node = nodes.get(nodeId)
        console.log('Selected table:', node.label)
      }
    })

    networkRef.current.on('hoverNode', function (params) {
      graphRef.current.style.cursor = 'pointer'
    })

    networkRef.current.on('blurNode', function (params) {
      graphRef.current.style.cursor = 'default'
    })

    networkRef.current.on('doubleClick', function (params) {
      if (params.nodes.length > 0) {
        networkRef.current.focus(params.nodes[0], {
          scale: 1.5,
          animation: {
            duration: 800,
            easingFunction: 'easeInOutQuad'
          }
        })
      }
    })

    // Handle stabilization for physics layouts
    if (layoutMode === 'physics') {
      networkRef.current.once('stabilizationIterationsDone', function () {
        networkRef.current.fit({
          animation: {
            duration: 1200,
            easingFunction: 'easeInOutQuad'
          }
        })
        setIsLoading(false)
      })

      networkRef.current.on('stabilizationProgress', function (params) {
        const progress = params.iterations / params.total
        if (graphRef.current) {
          const progressElement = graphRef.current.querySelector('.loading-progress')
          if (progressElement) {
            progressElement.style.width = (progress * 100) + '%'
          }
        }
      })
    } else {
      // For non-physics layouts, fit immediately
      setTimeout(() => {
        networkRef.current.fit({
          animation: {
            duration: 800,
            easingFunction: 'easeInOutQuad'
          }
        })
        setIsLoading(false)
      }, 100)
    }
  }

  useEffect(() => {
    if (!graph || !graph.nodes || !graph.edges || !graphRef.current) return

    setIsLoading(true)
    setHasError(false)

    // Dynamic import to avoid SSR issues
    const loadVisualization = async () => {
      try {
        const vis = await import('vis-network/standalone')
        await createNetwork(vis, layoutType)
      } catch (error) {
        console.error('Failed to load vis-network:', error)
        setHasError(true)
        setIsLoading(false)
      }
    }

    loadVisualization()

    // Cleanup function
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [graph, layoutType])

  const handleLayoutChange = async (newLayout) => {
    setLayoutType(newLayout)
  }

  if (!graph) return null

  return (
    <Card className="mt-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-purple-500" />
            Interactive Database Schema
          </CardTitle>
          
          {/* Layout Switcher */}
          <div className="flex gap-1">
            <Button
              variant={layoutType === 'hierarchical' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleLayoutChange('hierarchical')}
              className="text-xs h-7 px-2"
              disabled={isLoading}
            >
              📊 Hierarchy
            </Button>
            <Button
              variant={layoutType === 'physics' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleLayoutChange('physics')}
              className="text-xs h-7 px-2"
              disabled={isLoading}
            >
              🌐 Physics
            </Button>
            <Button
              variant={layoutType === 'circular' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleLayoutChange('circular')}
              className="text-xs h-7 px-2"
              disabled={isLoading}
            >
              ⭕ Circle
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <div 
            ref={graphRef} 
            className="w-full h-96 border rounded-lg bg-gradient-to-br from-gray-50 to-gray-100 relative overflow-hidden"
            style={{ height: '400px' }}
          />
          
          {/* Loading overlay */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 rounded-lg">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-sm text-gray-600 mb-2">
                  {layoutType === 'hierarchical' ? 'Organizing hierarchy...' : 
                   layoutType === 'physics' ? 'Calculating forces...' : 
                   'Arranging in circle...'}
                </p>
                <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="loading-progress h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300 ease-out" style={{ width: '0%' }}></div>
                </div>
              </div>
            </div>
          )}
          
          {/* Error state */}
          {hasError && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 rounded-lg">
              <div className="text-center text-gray-500">
                <div className="text-4xl mb-2">⚠️</div>
                <p className="font-medium">Visualization Error</p>
                <p className="text-sm mt-1">{graph.nodes?.length || 0} tables, {graph.edges?.length || 0} relationships</p>
                <button 
                  onClick={() => window.location.reload()} 
                  className="mt-3 px-4 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                >
                  Reload Page
                </button>
              </div>
            </div>
          )}
        </div>
        
        <div className="text-xs text-gray-500 mt-3 flex justify-between items-center">
          <span className="font-medium">
            {graph.nodes?.length || 0} tables • {graph.edges?.length || 0} relationships
          </span>
          <div className="flex gap-4 text-xs">
            <span>🖱️ Drag to explore</span>
            <span>🔍 Scroll to zoom</span>
            <span>👆 Double-click to focus</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Component for rendering Data Quality Rules
const DataQualityRules = ({ table, dqRules }) => {
  if (!table && !dqRules) return null

  return (
    <Card className="mt-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Shield className="w-4 h-4 text-green-500" />
          Data Quality Rules
        </CardTitle>
      </CardHeader>
      <CardContent>
        {table && (
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-50">
                  {table.columns.map((column, index) => (
                    <th key={index} className="px-3 py-2 text-left font-medium text-gray-700 border-b">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, rowIndex) => (
                  <tr key={rowIndex} className="hover:bg-gray-50">
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="px-3 py-2 text-gray-900 border-b">
                        {cellIndex === 3 && cell ? ( // SQL Code column
                          <code className="bg-gray-100 rounded px-1 text-xs">{cell}</code>
                        ) : (
                          cell || 'N/A'
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {dqRules && (
          <div className="space-y-3">
            <h4 className="font-medium text-sm">Detailed Rules Information:</h4>
            {dqRules.map((rule, index) => (
              <div key={index} className="bg-gray-50 rounded p-3">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-sm">Rule {rule.Rule_ID}</span>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {rule.Quality_Dimension}
                  </span>
                </div>
                <p className="text-xs text-gray-700 mb-2">{rule.Description}</p>
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                  <div><strong>Domain:</strong> {rule.Domain}</div>
                  <div><strong>Module:</strong> {rule.SAP_Module}</div>
                  <div><strong>Data Type:</strong> {rule.Data_Type}</div>
                  <div><strong>Relevance:</strong> {(rule.relevance_score * 100).toFixed(1)}%</div>
                </div>
                {rule.sql_query && (
                  <div className="mt-2">
                    <div className="text-xs font-medium text-gray-700 mb-1">SQL Query:</div>
                    <code className="bg-gray-200 rounded p-2 text-xs block">{rule.sql_query}</code>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function AnimatedMessage({ message }) {
  const [isTyping, setIsTyping] = useState(false)
  const [showActions, setShowActions] = useState(false)
  const [copied, setCopied] = useState(false)
  const [liked, setLiked] = useState(null) // null, 'up', 'down'

  // Animation refs
  const messageRef = useRef(null)
  const avatarRef = useRef(null)
  const contentRef = useRef(null)
  const actionsRef = useRef(null)
  const sparklesRef = useRef([])

  const isUser = message.role === 'user'
  const isError = message.isError
  const timestamp = new Date(message.timestamp).toLocaleTimeString()

  // Create sparkles for AI messages
  const createSparkles = () => {
    if (isUser || !contentRef.current) return

    for (let i = 0; i < 6; i++) {
      const sparkle = document.createElement('div')
      sparkle.className = 'absolute w-1 h-1 bg-blue-400 rounded-full opacity-20 pointer-events-none'
      sparkle.style.left = Math.random() * 100 + '%'
      sparkle.style.top = Math.random() * 100 + '%'
      contentRef.current.appendChild(sparkle)
      sparklesRef.current.push(sparkle)

      gsap.to(sparkle, {
        opacity: 0.4,
        scale: 1.5,
        duration: 1 + Math.random(),
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut",
        delay: Math.random() * 2
      })

      gsap.to(sparkle, {
        x: (Math.random() - 0.5) * 20,
        y: -10 - Math.random() * 20,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      })
    }
  }

  // Animate avatar with pulsing effect
  const animateAvatar = () => {
    if (!avatarRef.current) return

    if (isUser) {
      // User avatar: subtle scale on hover
      avatarRef.current.addEventListener('mouseenter', () => {
        gsap.to(avatarRef.current, {
          scale: 1.1,
          duration: 0.3,
          ease: "back.out(1.7)"
        })
      })

      avatarRef.current.addEventListener('mouseleave', () => {
        gsap.to(avatarRef.current, {
          scale: 1,
          duration: 0.3,
          ease: "power2.out"
        })
      })
    } else {
      // AI avatar: continuous gentle pulsing
      gsap.to(avatarRef.current, {
        scale: 1.05,
        duration: 2,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut"
      })

      // Glow effect
      gsap.to(avatarRef.current, {
        boxShadow: "0 0 15px rgba(59, 130, 246, 0.3)",
        duration: 2,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut"
      })
    }
  }

  // Typewriter effect for AI messages
  const animateTypewriter = () => {
    if (isUser || !contentRef.current) return

    const textElement = contentRef.current.querySelector('.message-text')
    if (!textElement || !message.content) return

    setIsTyping(true)
    textElement.textContent = ''

    // Simulate typing
    let index = 0
    const text = message.content
    const typeSpeed = 30 // ms per character

    const typeInterval = setInterval(() => {
      if (index < text.length) {
        textElement.textContent = text.slice(0, index + 1)
        index++

        // Add cursor effect
        if (index < text.length) {
          textElement.textContent += '|'
        }
      } else {
        clearInterval(typeInterval)
        setIsTyping(false)
        textElement.textContent = text

        // Show actions after typing is complete
        setTimeout(() => setShowActions(true), 500)
      }
    }, typeSpeed)

    return typeInterval
  }

  // Copy to clipboard with animation
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)

      // Animate copy success
      if (actionsRef.current) {
        const copyButton = actionsRef.current.querySelector('.copy-button')
        if (copyButton) {
          gsap.to(copyButton, {
            scale: 1.2,
            duration: 0.2,
            yoyo: true,
            repeat: 1,
            ease: "back.out(1.7)"
          })
        }
      }

      // Create success particles
      for (let i = 0; i < 8; i++) {
        const particle = document.createElement('div')
        particle.className = 'absolute w-1 h-1 bg-green-400 rounded-full pointer-events-none'
        particle.style.left = '50%'
        particle.style.top = '50%'
        messageRef.current?.appendChild(particle)

        gsap.to(particle, {
          x: (Math.random() - 0.5) * 100,
          y: -20 - Math.random() * 30,
          opacity: 0,
          scale: 0,
          duration: 1,
          ease: "power2.out",
          onComplete: () => particle.remove()
        })
      }

      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // Handle like/dislike with animation
  const handleReaction = (type) => {
    setLiked(liked === type ? null : type)

    // Animate reaction button
    if (actionsRef.current) {
      const button = actionsRef.current.querySelector(`.${type}-button`)
      if (button) {
        gsap.to(button, {
          scale: 1.3,
          rotation: type === 'up' ? 10 : -10,
          duration: 0.3,
          yoyo: true,
          repeat: 1,
          ease: "back.out(1.7)"
        })
      }
    }

    // Create reaction particles
    const color = type === 'up' ? 'bg-green-400' : 'bg-red-400'
    for (let i = 0; i < 5; i++) {
      const particle = document.createElement('div')
      particle.className = `absolute w-2 h-2 ${color} rounded-full pointer-events-none`
      particle.style.left = '50%'
      particle.style.top = '50%'
      messageRef.current?.appendChild(particle)

      gsap.to(particle, {
        x: (Math.random() - 0.5) * 80,
        y: -15 - Math.random() * 25,
        opacity: 0,
        scale: 0,
        duration: 0.8,
        ease: "power2.out",
        onComplete: () => particle.remove()
      })
    }
  }

  // Initialize animations
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Message entrance animation
    gsap.fromTo(messageRef.current,
      { 
        opacity: 0, 
        y: 30, 
        scale: 0.95,
        x: isUser ? 20 : -20
      },
      { 
        opacity: 1, 
        y: 0, 
        scale: 1,
        x: 0,
        duration: 0.6, 
        ease: "back.out(1.7)" 
      }
    )

    animateAvatar()
    createSparkles()

    // Start typewriter effect for AI messages
    if (!isUser) {
      setTimeout(() => animateTypewriter(), 300)
    } else {
      setShowActions(true)
    }

    return () => {
      gsap.killTweensOf([messageRef.current, avatarRef.current, contentRef.current])
    }
  }, [])

  // Animate actions appearance
  useEffect(() => {
    if (showActions && actionsRef.current) {
      gsap.fromTo(actionsRef.current,
        { opacity: 0, y: 10, scale: 0.9 },
        { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.7)" }
      )
    }
  }, [showActions])

  return (
    <div 
      ref={messageRef}
      className={`flex gap-3 group ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div 
        ref={avatarRef}
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 relative overflow-hidden ${
          isUser 
            ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
            : isError
              ? 'bg-gradient-to-r from-red-500 to-pink-600'
              : 'bg-gradient-to-r from-emerald-500 to-blue-600'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
        {!isUser && !isError && (
          <Sparkles className="absolute top-0 right-0 w-2 h-2 text-yellow-300 animate-pulse" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-3xl ${isUser ? 'text-right' : 'text-left'}`}>
        <div 
          ref={contentRef}
          className={`inline-block p-4 rounded-2xl relative overflow-hidden ${
            isUser
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
              : isError
                ? 'bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 text-red-800'
                : 'bg-gradient-to-r from-gray-50 to-white border border-gray-200 text-gray-900'
          } ${isUser ? 'rounded-br-sm' : 'rounded-bl-sm'}`}
        >
          <div className="message-text text-sm leading-relaxed relative z-10">
            {isUser || isTyping ? message.content : ''}
          </div>
          
          {/* Structured Data Display */}
          {!isUser && !isTyping && message.structuredData && (
            <div className="mt-4">
              {/* SQL Strategy */}
              {message.structuredData.strategy_used === 'SQL' && (
                <SQLResultTable 
                  table={message.structuredData.table} 
                  sql={message.structuredData.sql}
                />
              )}
              
              {/* Visualization Strategy */}
              {message.structuredData.strategy_used === 'VISUALIZE' && (
                <NetworkGraph graph={message.structuredData.graph?.graph} />
              )}
              
              {/* Data Quality Strategy */}
              {message.structuredData.strategy_used === 'DQ_RULE' && (
                <DataQualityRules 
                  table={message.structuredData.table}
                  dqRules={message.structuredData.dqRules}
                />
              )}
            </div>
          )}
          
          {isTyping && (
            <div className="flex items-center gap-1 mt-2 text-xs opacity-60">
              <div className="w-1 h-1 bg-current rounded-full animate-pulse"></div>
              <div className="w-1 h-1 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-1 h-1 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              <span className="ml-2">Lumina is typing...</span>
            </div>
          )}

          {/* Gradient overlay for depth */}
          {!isUser && !isError && (
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 pointer-events-none"></div>
          )}
        </div>

        {/* Timestamp */}
        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {timestamp}
        </div>

        {/* Actions */}
        {showActions && !isUser && (
          <div 
            ref={actionsRef}
            className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="copy-button h-8 px-2 text-xs hover:bg-gray-100 transition-all duration-200"
            >
              {copied ? (
                <CheckCircle className="w-3 h-3 text-green-500" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
              {copied ? 'Copied!' : 'Copy'}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleReaction('up')}
              className={`up-button h-8 px-2 text-xs transition-all duration-200 ${
                liked === 'up' ? 'bg-green-100 text-green-600' : 'hover:bg-gray-100'
              }`}
            >
              <ThumbsUp className="w-3 h-3" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleReaction('down')}
              className={`down-button h-8 px-2 text-xs transition-all duration-200 ${
                liked === 'down' ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100'
              }`}
            >
              <ThumbsDown className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
