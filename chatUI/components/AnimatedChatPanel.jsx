'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { TextPlugin } from 'gsap/TextPlugin'
import { v4 as uuidv4 } from 'uuid'
import AnimatedMessage from './AnimatedMessage'
import AnimatedChatInput from './AnimatedChatInput'
import AnimatedTokenTracker from './AnimatedTokenTracker'
import DatabaseSelector from './DatabaseSelector'
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
  onAddMessage,
  onUpdateMessage,  // Add this prop for updating existing messages
  config,
  onConfigChange
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [tokenUsage, setTokenUsage] = useState(null)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [processingSteps, setProcessingSteps] = useState([])
  const [chatConfig, setChatConfig] = useState({
    user_id: "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
    api_key: "AIzaSyBja5P8lEZQ6qYs1SM2ZRXwzm9EgCsERLc",
    model_name: "gemini-2.0-flash",
    temperature: 0.2,
    db_connection_info: {
      db_host: "localhost",
      db_port: 5432,
      db_user: "postgres",
      db_name: "chinook",
      db_password: "iamaryan15",
      db_schema: null
    },
    short_term_memory: [
      "SUMMARY: The table names are case sensitive, use double quotes while generating commands"
    ]
  })

  // Update local config when prop changes
  useEffect(() => {
    if (config && Object.keys(config).length > 0) {
      setChatConfig(config)
    }
  }, [config])

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

      // Prepare chat history in the correct format for backend
      const chatHistory = conversation.messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      // Add the current user message to chat history
      chatHistory.push({
        role: 'user',
        content: message
      })

      // Prepare the payload in the exact format expected by backend
      const payload = {
        query: message,
        user_id: chatConfig.user_id,
        conversation_id: conversation.id,
        message_id: userMessage.id,
        chat_history: chatHistory,
        short_term_memory: chatConfig.short_term_memory,
        model_name: chatConfig.model_name,
        temperature: chatConfig.temperature,
        api_key: chatConfig.api_key,
        db_connection_info: chatConfig.db_connection_info
      }

      console.log('Sending payload to backend:', payload)

      const response = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
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
      let finalResponse = null
      let currentEventType = ''
      let hasTokenUsage = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
            continue
          }
          
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              // Handle different event types based on the backend's Server-Sent Events format
              switch (currentEventType) {
                case 'status_update':
                  if (data.message) {
                    setProcessingSteps(prev => [...prev, { id: uuidv4(), step: data.message }])
                  }
                  break
                
                case 'sql_generated':
                  if (data.sql) {
                    console.log('SQL Generated:', data.sql)
                    setProcessingSteps(prev => [...prev, { id: uuidv4(), step: `SQL: ${data.sql}` }])
                  }
                  break
                
                case 'structured_response':
                  if (data.answer_text) {
                    finalResponse = data
                    accumulatedContent = data.answer_text
                    
                    // Update message with final response including structured data
                    assistantMessage = {
                      ...assistantMessage,
                      content: accumulatedContent,
                      structuredData: {
                        strategy_used: data.strategy_used,
                        table: data.table,
                        graph: data.graph,
                        dqRules: data.dqRules,
                        sql: data.sql
                      }
                    }
                    
                    setStreamingMessage(accumulatedContent)
                    
                    // Update the existing message
                    if (onUpdateMessage) {
                      onUpdateMessage(conversation.id, assistantMessage)
                    }
                  }
                  break
                
                case 'token_usage':
                  if (data.token_usage) {
                    setTokenUsage({
                      total: data.token_usage.total_token_count,
                      prompt: data.token_usage.prompt_token_count,
                      completion: data.token_usage.candidates_token_count,
                      cost: (data.token_usage.total_token_count * 0.00001).toFixed(6) // Rough estimate
                    })
                    hasTokenUsage = true
                  }
                  break
                
                default:
                  // Handle old format for backward compatibility
                  if (data.type === 'content') {
                    accumulatedContent += data.content
                    setStreamingMessage(accumulatedContent)
                    
                    assistantMessage = {
                      ...assistantMessage,
                      content: accumulatedContent
                    }
                    
                    if (onUpdateMessage) {
                      onUpdateMessage(conversation.id, assistantMessage)
                    }
                  } else if (data.type === 'token_usage') {
                    setTokenUsage(data.usage)
                    hasTokenUsage = true
                  } else if (data.type === 'processing_step') {
                    setProcessingSteps(prev => [...prev, { id: uuidv4(), step: data.step }])
                  }
                  break
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, 'Line:', line)
            }
          }
        }
      }

      // Auto-generate title for first message
      if (conversation.messages.length === 1) { // Only user message exists
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

  const handleDatabaseTypeChange = (newDbType) => {
    // Define default configurations for each database type
    const dbDefaults = {
      postgresql: {
        db_type: 'postgresql',
        db_host: 'localhost',
        db_port: 5432,
        db_user: 'postgres',
        db_name: 'chinook',
        db_password: '',
        db_schema: null
      },
      mysql: {
        db_type: 'mysql',
        db_host: 'localhost',
        db_port: 3306,
        db_user: 'root',
        db_name: 'chinook',
        db_password: '',
        db_schema: null
      },
      sqlite: {
        db_type: 'sqlite',
        db_host: '',
        db_port: null,
        db_user: '',
        db_name: 'chinook.db',
        db_password: '',
        db_schema: null
      },
      snowflake: {
        db_type: 'snowflake',
        db_host: 'your-account.snowflakecomputing.com',
        db_port: 443,
        db_user: '',
        db_name: 'CHINOOK',
        db_password: '',
        db_schema: 'PUBLIC'
      }
    }

    // Get default config for the new database type
    const defaultConfig = dbDefaults[newDbType] || dbDefaults.postgresql
    
    // Update the database connection info with new type and defaults
    const updatedConnection = {
      ...dbConnection,
      ...defaultConfig
    }
    
    onDbConnectionChange(updatedConnection)
    
    // Also update the global config if available
    if (onConfigChange && config) {
      const updatedConfig = {
        ...config,
        db_connection_info: updatedConnection
      }
      onConfigChange(updatedConfig)
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
      {/* Chat Header */}
      <div className="border-b border-gray-200 p-4 bg-gradient-to-r from-white to-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-500" />
            <h2 className="font-semibold text-gray-900">Brain LLM Assistant</h2>
          </div>
          <div className="text-sm text-gray-500">
            Connected to {chatConfig.db_connection_info.db_name}@{chatConfig.db_connection_info.db_host}
          </div>
        </div>
      </div>

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

            {/* Database Selector on Welcome Screen */}
            <div className="mb-6 flex items-center justify-center">
              <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm">
                <span className="text-sm text-gray-600">Database:</span>
                <DatabaseSelector 
                  currentDbType={dbConnection?.db_type || 'postgresql'}
                  onDatabaseTypeChange={handleDatabaseTypeChange}
                />
              </div>
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
            {/* Database Selector */}
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Database:</span>
                <DatabaseSelector 
                  currentDbType={dbConnection?.db_type || 'postgresql'}
                  onDatabaseTypeChange={handleDatabaseTypeChange}
                />
              </div>
            </div>
            
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
