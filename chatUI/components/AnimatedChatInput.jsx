'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { TextPlugin } from 'gsap/TextPlugin'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Paperclip, Send, Zap, Database } from 'lucide-react'
import DBConnectionModal from '@/components/DBConnectionModal'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(TextPlugin)
}

export default function AnimatedChatInput({ 
  onSendMessage, 
  isLoading, 
  dbConnection, 
  onDbConnectionChange 
}) {
  const [message, setMessage] = useState('')
  const [showDBModal, setShowDBModal] = useState(false)
  const [isTyping, setIsTyping] = useState(false)

  // Refs for animations
  const containerRef = useRef(null)
  const inputRef = useRef(null)
  const sendButtonRef = useRef(null)
  const attachButtonRef = useRef(null)
  const statusRef = useRef(null)
  const placeholderRef = useRef(null)

  // Animated placeholders
  const placeholders = [
    "Ask about your data quality rules...",
    "Generate SQL queries...",
    "Analyze database schema...",
    "What insights can you find?",
    "How can I improve data quality?",
    "Show me sales trends...",
    "Find data anomalies..."
  ]

  const [currentPlaceholder, setCurrentPlaceholder] = useState(0)

  // Create floating particles around input
  const createInputParticles = () => {
    if (!containerRef.current) return

    for (let i = 0; i < 8; i++) {
      const particle = document.createElement('div')
      particle.className = 'absolute w-1 h-1 bg-blue-400 rounded-full opacity-30 pointer-events-none'
      particle.style.left = Math.random() * 100 + '%'
      particle.style.top = Math.random() * 100 + '%'
      containerRef.current.appendChild(particle)

      // Animate particles in orbit
      gsap.to(particle, {
        rotation: 360,
        repeat: -1,
        duration: 4 + Math.random() * 2,
        ease: "none",
        transformOrigin: `${-50 + Math.random() * 100}px ${-50 + Math.random() * 100}px`
      })

      // Fade in and out
      gsap.to(particle, {
        opacity: 0.6,
        duration: 1,
        yoyo: true,
        repeat: -1,
        ease: "power2.inOut"
      })
    }
  }

  // Magnetic button effect
  const createMagneticButton = (buttonRef) => {
    if (!buttonRef.current) return

    const button = buttonRef.current

    button.addEventListener('mouseenter', () => {
      gsap.to(button, {
        scale: 1.1,
        duration: 0.3,
        ease: "back.out(1.7)"
      })
    })

    button.addEventListener('mouseleave', () => {
      gsap.to(button, {
        scale: 1,
        x: 0,
        y: 0,
        duration: 0.3,
        ease: "power2.out"
      })
    })

    button.addEventListener('mousemove', (e) => {
      const rect = button.getBoundingClientRect()
      const x = e.clientX - rect.left - rect.width / 2
      const y = e.clientY - rect.top - rect.height / 2

      gsap.to(button, {
        x: x * 0.2,
        y: y * 0.2,
        duration: 0.3,
        ease: "power2.out"
      })
    })
  }

  // Typewriter effect for placeholders
  const animatePlaceholder = () => {
    if (!inputRef.current) return

    const placeholder = placeholders[currentPlaceholder]
    
    gsap.to(inputRef.current, {
      text: "",
      duration: 0.5,
      ease: "power2.inOut",
      onComplete: () => {
        gsap.to(inputRef.current, {
          text: placeholder,
          duration: 1.5,
          ease: "power2.out"
        })
      }
    })
  }

  // Pulsing input border on focus
  const animateInputFocus = (focused) => {
    if (!containerRef.current) return

    if (focused) {
      gsap.to(containerRef.current, {
        boxShadow: "0 0 20px rgba(59, 130, 246, 0.3)",
        scale: 1.02,
        duration: 0.3,
        ease: "power2.out"
      })
    } else {
      gsap.to(containerRef.current, {
        boxShadow: "0 0 0px rgba(59, 130, 246, 0)",
        scale: 1,
        duration: 0.3,
        ease: "power2.out"
      })
    }
  }

  // Loading animation for send button
  const animateLoading = (loading) => {
    if (!sendButtonRef.current) return

    if (loading) {
      gsap.to(sendButtonRef.current, {
        rotation: 360,
        repeat: -1,
        duration: 1,
        ease: "none"
      })
      
      gsap.to(sendButtonRef.current, {
        scale: 0.9,
        yoyo: true,
        repeat: -1,
        duration: 0.5,
        ease: "power2.inOut"
      })
    } else {
      gsap.killTweensOf(sendButtonRef.current)
      gsap.to(sendButtonRef.current, {
        rotation: 0,
        scale: 1,
        duration: 0.3,
        ease: "back.out(1.7)"
      })
    }
  }

  // Database connection status animation
  const animateConnectionStatus = (connected) => {
    if (!statusRef.current) return

    if (connected) {
      gsap.fromTo(statusRef.current,
        { scale: 0, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.5, ease: "back.out(1.7)" }
      )
    } else {
      gsap.to(statusRef.current, {
        scale: 1.1,
        duration: 0.2,
        yoyo: true,
        repeat: 3,
        ease: "power2.inOut"
      })
    }
  }

  // Send message with animation
  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      // Animate message sending
      gsap.to(inputRef.current, {
        scale: 0.95,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut"
      })

      // Create sending particle effect
      for (let i = 0; i < 5; i++) {
        const particle = document.createElement('div')
        particle.className = 'absolute w-2 h-2 bg-blue-500 rounded-full pointer-events-none'
        particle.style.left = '50%'
        particle.style.top = '50%'
        containerRef.current?.appendChild(particle)

        gsap.to(particle, {
          x: (Math.random() - 0.5) * 200,
          y: -100 - Math.random() * 50,
          opacity: 0,
          scale: 0,
          duration: 0.8,
          ease: "power2.out",
          onComplete: () => particle.remove()
        })
      }

      onSendMessage(message.trim())
      setMessage('')
      
      // Reset input with bounce
      gsap.fromTo(inputRef.current,
        { x: -10 },
        { x: 0, duration: 0.3, ease: "elastic.out(1, 0.3)" }
      )
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Initialize animations
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Initial entrance animation
    gsap.fromTo(containerRef.current,
      { y: 50, opacity: 0, scale: 0.9 },
      { y: 0, opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.7)" }
    )

    // Create magnetic effects
    createMagneticButton(sendButtonRef)
    createMagneticButton(attachButtonRef)

    // Create input particles
    createInputParticles()

    return () => {
      gsap.killTweensOf([containerRef.current, sendButtonRef.current, attachButtonRef.current])
    }
  }, [])

  // Placeholder rotation animation
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentPlaceholder(prev => (prev + 1) % placeholders.length)
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  // Animate placeholder changes
  useEffect(() => {
    if (!message) {
      animatePlaceholder()
    }
  }, [currentPlaceholder, message])

  // Loading animation effect
  useEffect(() => {
    animateLoading(isLoading)
  }, [isLoading])

  // Connection status animation
  useEffect(() => {
    animateConnectionStatus(!!dbConnection)
  }, [dbConnection])

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="relative">
        <div 
          ref={containerRef}
          className="flex items-center gap-3 p-4 bg-gradient-to-r from-gray-100 to-gray-50 rounded-2xl border border-gray-200 hover:border-gray-300 transition-all duration-300 relative overflow-hidden"
          onFocus={() => animateInputFocus(true)}
          onBlur={() => animateInputFocus(false)}
        >
          {/* Animated attachment button */}
          <Button
            ref={attachButtonRef}
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setShowDBModal(true)}
            className="text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-xl transition-all duration-300 relative z-10"
          >
            <Paperclip className="w-5 h-5" />
          </Button>
          
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={message ? "" : placeholders[currentPlaceholder]}
              className="bg-transparent border-0 text-gray-900 placeholder-gray-500 focus-visible:ring-0 focus-visible:ring-offset-0 text-lg transition-all duration-300"
              disabled={isLoading}
            />
          </div>

          <div className="flex items-center gap-2 relative z-10">
            <span className="text-xs text-gray-400 opacity-50 hover:opacity-100 transition-opacity duration-300">⌘</span>
            <Button
              ref={sendButtonRef}
              type="submit"
              size="icon"
              disabled={!message.trim() || isLoading}
              className="bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-900 hover:to-black text-white rounded-xl transition-all duration-300 disabled:opacity-50 relative overflow-hidden"
            >
              <Send className="w-4 h-4" />
              {isLoading && (
                <div className="absolute inset-0 bg-blue-500 opacity-20 animate-pulse rounded-xl"></div>
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Animated Database Connection Status */}
      <div ref={statusRef} className="px-2">
        {dbConnection ? (
          <div className="text-xs text-green-600 flex items-center gap-1 animate-pulse">
            <Database className="w-3 h-3" />
            <span>Connected to: {dbConnection.db_name} ({dbConnection.db_host}:{dbConnection.db_port})</span>
          </div>
        ) : (
          <div className="text-xs text-amber-600 flex items-center gap-1">
            <Zap className="w-3 h-3 animate-bounce" />
            <span>⚠️ No database connection. Click the attachment button to connect.</span>
          </div>
        )}
      </div>

      <DBConnectionModal
        isOpen={showDBModal}
        onClose={() => setShowDBModal(false)}
        onSave={onDbConnectionChange}
        currentConnection={dbConnection}
      />
    </div>
  )
}
