'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { TextPlugin } from 'gsap/TextPlugin'
import { User, Bot, Copy, ThumbsUp, ThumbsDown, Sparkles, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(TextPlugin)
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
