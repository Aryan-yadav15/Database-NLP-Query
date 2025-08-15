'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { TextPlugin } from 'gsap/TextPlugin'
import { v4 as uuidv4 } from 'uuid'
import AnimatedMessage from './AnimatedMessage'
import AnimatedChatInput from './AnimatedChatInput'
import AnimatedTokenTracker from './AnimatedTokenTracker'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/components/ui/toast'
import { Sparkles, Bot, User, Wand2 } from 'lucide-react'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger, TextPlugin)
}

const SUGGESTED_PROMPTS = [
  {
    icon: "📊",
    title: "Analyze sales data trends",
    description: "Get insights from your sales database"
  },
  {
    icon: "🔍", 
    title: "Find data quality issues",
    description: "Identify anomalies and inconsistencies"
  },
  {
    icon: "💡",
    title: "Suggest database optimizations", 
    description: "Improve query performance and structure"
  },
  {
    icon: "📈",
    title: "Generate financial reports",
    description: "Create comprehensive financial analysis"
  }
]

export default function AnimatedChatPanel({ 
  conversation, 
  dbConnection, 
  onDbConnectionChange, 
  onUpdateTitle, 
  onAddMessage
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [tokenUsage, setTokenUsage] = useState(null)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [processingSteps, setProcessingSteps] = useState([])

  // Animation refs
  const containerRef = useRef(null)
  const welcomeRef = useRef(null)
  const promptsRef = useRef([])
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const particlesRef = useRef(null)

  const { addToast } = useToast()

  // Create floating particles for welcome screen
  const createWelcomeParticles = () => {
    if (!particlesRef.current || conversation?.messages?.length > 0) return

    for (let i = 0; i < 25; i++) {
      const particle = document.createElement('div')
      particle.className = 'absolute rounded-full pointer-events-none'
      
      // Random size and color
      const size = Math.random() * 4 + 2
      const colors = ['bg-blue-400', 'bg-purple-400', 'bg-pink-400', 'bg-yellow-400', 'bg-green-400']
      particle.className += ` ${colors[Math.floor(Math.random() * colors.length)]}`
      particle.style.width = size + 'px'
      particle.style.height = size + 'px'
      particle.style.left = Math.random() * 100 + '%'
      particle.style.top = Math.random() * 100 + '%'
      particle.style.opacity = '0.1'
      
      particlesRef.current.appendChild(particle)

      // Floating animation
      gsap.to(particle, {
        y: -100 - Math.random() * 200,
        x: (Math.random() - 0.5) * 200,
        opacity: 0.3,
        duration: 5 + Math.random() * 5,
        repeat: -1,
        ease: "none"
      })

      // Scale pulsing
      gsap.to(particle, {
        scale: 1.5,
        duration: 2 + Math.random() * 2,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut"
      })
    }
  }

  // Animate welcome screen entrance
  const animateWelcomeScreen = () => {
    if (!welcomeRef.current) return

    const tl = gsap.timeline()

    // Title animation with typewriter effect
    tl.fromTo(welcomeRef.current.querySelector('h1'),
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, duration: 0.8, ease: "back.out(1.7)" }
    )
    .fromTo(welcomeRef.current.querySelector('h2'),
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }, "-=0.4"
    )
    .fromTo(welcomeRef.current.querySelector('p'),
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, "-=0.3"
    )

    // Animate prompts with stagger
    promptsRef.current.forEach((prompt, index) => {
      if (prompt) {
        tl.fromTo(prompt,
          { opacity: 0, y: 30, scale: 0.9, rotationX: -15 },
          { 
            opacity: 1, 
            y: 0, 
            scale: 1,
            rotationX: 0,
            duration: 0.6, 
            ease: "back.out(1.7)" 
          }, `-=${0.8 - index * 0.1}`
        )
      }
    })
  }

  // Animate prompt hover effects
  const animatePromptHover = (element, isEntering) => {
    if (isEntering) {
      gsap.to(element, {
        scale: 1.05,
        y: -5,
        boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
        duration: 0.3,
        ease: "back.out(1.7)"
      })

      // Icon bounce
      const icon = element.querySelector('.prompt-icon')
      if (icon) {
        gsap.to(icon, {
          scale: 1.2,
          rotation: 5,
          duration: 0.3,
          ease: "back.out(1.7)"
        })
      }
    } else {
      gsap.to(element, {
        scale: 1,
        y: 0,
        boxShadow: "0 0 0px rgba(0,0,0,0)",
        duration: 0.3,
        ease: "power2.out"
      })

      const icon = element.querySelector('.prompt-icon')
      if (icon) {
        gsap.to(icon, {
          scale: 1,
          rotation: 0,
          duration: 0.3,
          ease: "power2.out"
        })
      }
    }
  }

  // Animate new message appearance
  const animateNewMessage = (messageElement, isUser = false) => {
    if (!messageElement) return

    if (isUser) {
      // User message slides in from right
      gsap.fromTo(messageElement,
        { x: 50, opacity: 0, scale: 0.9 },
        { x: 0, opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.7)" }
      )
    } else {
      // AI message typewriter effect
      gsap.fromTo(messageElement,
        { x: -30, opacity: 0, scale: 0.95 },
        { x: 0, opacity: 1, scale: 1, duration: 0.6, ease: "power2.out" }
      )

      // Add thinking particles for AI messages
      const rect = messageElement.getBoundingClientRect()
      for (let i = 0; i < 5; i++) {
        const particle = document.createElement('div')
        particle.className = 'absolute w-2 h-2 bg-blue-400 rounded-full pointer-events-none'
        particle.style.left = rect.left + Math.random() * rect.width + 'px'
        particle.style.top = rect.top + 'px'
        document.body.appendChild(particle)

        gsap.to(particle, {
          y: -30,
          opacity: 0,
          scale: 0,
          duration: 1,
          ease: "power2.out",
          onComplete: () => particle.remove()
        })
      }
    }
  }

  // Simulate typing effect for streaming
  const animateTyping = (text, element, speed = 50) => {
    if (!element) return

    let index = 0
    const typeInterval = setInterval(() => {
      if (index < text.length) {
        element.textContent = text.slice(0, index + 1)
        index++
      } else {
        clearInterval(typeInterval)
      }
    }, speed)

    return typeInterval
  }

  // Enhanced message sending handler
  const handleSendMessage = async (message) => {
    if (!message.trim() || isLoading) return

    setIsLoading(true)
    setProcessingSteps([])
    setStreamingMessage('')

    // Add user message with animation
    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }
    onAddMessage(conversation.id, userMessage)

    // Create sparkle effect for message sending
    const sparkles = []
    for (let i = 0; i < 10; i++) {
      const sparkle = document.createElement('div')
      sparkle.className = 'absolute w-1 h-1 bg-yellow-400 rounded-full pointer-events-none'
      sparkle.style.left = '50%'
      sparkle.style.top = '50%'
      messagesContainerRef.current?.appendChild(sparkle)
      sparkles.push(sparkle)

      gsap.to(sparkle, {
        x: (Math.random() - 0.5) * 300,
        y: -50 - Math.random() * 100,
        opacity: 0,
        scale: 0,
        duration: 1,
        ease: "power2.out",
        onComplete: () => sparkle.remove()
      })
    }

    try {
      // Simulate processing steps
      const steps = [
        'Analyzing query intent...',
        'Connecting to database...',
        'Generating SQL query...',
        'Executing query...',
        'Processing results...',
        'Generating response...'
      ]

      for (let i = 0; i < steps.length; i++) {
        setProcessingSteps(prev => [...prev, { id: uuidv4(), step: steps[i] }])
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      const response = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: message,
          conversation_id: conversation.id,
          db_connection: dbConnection
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      }

      onAddMessage(conversation.id, assistantMessage)

      let accumulatedContent = ''
      let hasTokenUsage = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'content') {
                accumulatedContent += data.content
                setStreamingMessage(accumulatedContent)
                
                // Update message with streaming content
                assistantMessage = {
                  ...assistantMessage,
                  content: accumulatedContent
                }
                onAddMessage(conversation.id, assistantMessage)
              } else if (data.type === 'token_usage') {
                setTokenUsage(data.usage)
                hasTokenUsage = true
              } else if (data.type === 'processing_step') {
                setProcessingSteps(prev => [...prev, { id: uuidv4(), step: data.step }])
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }

      // Auto-generate title for first message
      if (conversation.messages.length === 0) {
        const title = message.length > 50 ? message.substring(0, 50) + '...' : message
        onUpdateTitle(conversation.id, title)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      addToast('Failed to send message. Please check your connection.', 'error')
      
      const errorMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      }
      onAddMessage(conversation.id, errorMessage)
    } finally {
      setIsLoading(false)
      setProcessingSteps([])
    }
  }

  const handlePromptClick = (prompt) => {
    // Animate prompt click
    const clickedElement = promptsRef.current.find(el => 
      el?.textContent.includes(prompt.title)
    )
    
    if (clickedElement) {
      gsap.to(clickedElement, {
        scale: 0.95,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut",
        onComplete: () => {
          handleSendMessage(prompt.title)
        }
      })
    } else {
      handleSendMessage(prompt.title)
    }
  }

  // Initialize animations
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Container entrance
    gsap.fromTo(containerRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }
    )

    createWelcomeParticles()

    return () => {
      gsap.killTweensOf(containerRef.current)
    }
  }, [])

  // Animate welcome screen when no messages
  useEffect(() => {
    if (conversation?.messages?.length === 0) {
      setTimeout(() => animateWelcomeScreen(), 300)
      createWelcomeParticles()
    }
  }, [conversation?.messages?.length])

  // Auto-scroll to bottom with animation
  useEffect(() => {
    if (messagesEndRef.current) {
      gsap.to(messagesEndRef.current, {
        scrollIntoView: true,
        duration: 0.5,
        ease: "power2.out"
      })
    }
  }, [conversation?.messages])

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-400 flex items-center gap-2">
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          Loading...
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="flex-1 flex flex-col h-full">
      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-6" ref={messagesContainerRef}>
        {conversation.messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center max-w-3xl mx-auto px-4 relative">
            {/* Floating particles background */}
            <div ref={particlesRef} className="absolute inset-0 pointer-events-none" />
            
            <div ref={welcomeRef} className="text-center mb-8 relative z-10">
              <h1 className="text-4xl font-bold text-gray-900 mb-3 flex items-center justify-center gap-2">
                Hi, Aryan
                <Wand2 className="w-8 h-8 text-purple-500 animate-pulse" />
              </h1>
              <h2 className="text-xl font-semibold text-gray-700 mb-4 flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                What can I help you with?
              </h2>
              <p className="text-gray-500 text-sm">Choose a prompt below or write your own to start chatting with Lumina.</p>
            </div>

            <div className="grid grid-cols-2 gap-2.5 w-full max-w-xl relative z-10">
              {SUGGESTED_PROMPTS.map((prompt, index) => (
                <div
                  key={index}
                  ref={el => promptsRef.current[index] = el}
                  onClick={() => handlePromptClick(prompt)}
                  onMouseEnter={(e) => animatePromptHover(e.currentTarget, true)}
                  onMouseLeave={(e) => animatePromptHover(e.currentTarget, false)}
                  className="p-2.5 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200 hover:border-gray-300 cursor-pointer transition-all duration-200 group relative overflow-hidden"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-sm prompt-icon">{prompt.icon}</span>
                    <div>
                      <h3 className="font-medium text-gray-900 mb-0.5 text-xs group-hover:text-gray-800 leading-tight">
                        {prompt.title}
                      </h3>
                      <p className="text-xs text-gray-600 leading-tight">{prompt.description}</p>
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {conversation.messages.map((message, index) => (
              <div
                key={message.id}
                ref={el => {
                  if (el && index === conversation.messages.length - 1) {
                    setTimeout(() => animateNewMessage(el, message.role === 'user'), 100)
                  }
                }}
              >
                <AnimatedMessage message={message} />
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* Chat Input */}
      <div className="border-t border-gray-200 p-4 bg-gradient-to-r from-white to-gray-50">
        <div className="max-w-4xl mx-auto">
          <AnimatedChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            dbConnection={dbConnection}
            onDbConnectionChange={onDbConnectionChange}
          />
          
          {/* Token Tracker */}
          {tokenUsage && (
            <div className="mt-2">
              <AnimatedTokenTracker tokenUsage={tokenUsage} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
