'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { 
  Plus, 
  MessageSquare, 
  User, 
  Zap, 
  ChevronsLeft, 
  ChevronsRight,
  Sparkles,
  Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

export default function AnimatedLeftSidebar({ 
  conversations = [], 
  activeConversationId, 
  onConversationSelect, 
  onNewChat,
  isCollapsed,
  onToggleCollapse
}) {
  // Animation refs
  const sidebarRef = useRef(null)
  const logoRef = useRef(null)
  const newChatRef = useRef(null)
  const conversationsRef = useRef([])
  const upgradeRef = useRef(null)
  const toggleRef = useRef(null)
  const sparklesRef = useRef([])

  // Create floating sparkles
  const createSparkles = () => {
    if (!sidebarRef.current || isCollapsed) return

    // Clear existing sparkles
    sparklesRef.current.forEach(sparkle => sparkle?.remove())
    sparklesRef.current = []

    for (let i = 0; i < 12; i++) {
      const sparkle = document.createElement('div')
      sparkle.className = 'absolute w-1 h-1 bg-yellow-400 rounded-full opacity-30 pointer-events-none'
      sparkle.style.left = Math.random() * 100 + '%'
      sparkle.style.top = Math.random() * 100 + '%'
      sidebarRef.current.appendChild(sparkle)
      sparklesRef.current.push(sparkle)

      // Twinkling animation
      gsap.to(sparkle, {
        opacity: 0.8,
        scale: 1.5,
        duration: 0.5 + Math.random() * 1,
        yoyo: true,
        repeat: -1,
        ease: "power2.inOut",
        delay: Math.random() * 2
      })

      // Floating movement
      gsap.to(sparkle, {
        y: -20 - Math.random() * 30,
        x: (Math.random() - 0.5) * 40,
        duration: 3 + Math.random() * 2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      })
    }
  }

  // Animate logo with pulsing glow
  const animateLogo = () => {
    if (!logoRef.current) return

    gsap.to(logoRef.current, {
      boxShadow: "0 0 20px rgba(251, 191, 36, 0.5)",
      duration: 2,
      yoyo: true,
      repeat: -1,
      ease: "power2.inOut"
    })

    // Subtle rotation on hover
    logoRef.current.addEventListener('mouseenter', () => {
      gsap.to(logoRef.current, {
        rotation: 10,
        scale: 1.1,
        duration: 0.3,
        ease: "back.out(1.7)"
      })
    })

    logoRef.current.addEventListener('mouseleave', () => {
      gsap.to(logoRef.current, {
        rotation: 0,
        scale: 1,
        duration: 0.3,
        ease: "back.out(1.7)"
      })
    })
  }

  // Magnetic new chat button
  const animateNewChatButton = () => {
    if (!newChatRef.current) return

    const button = newChatRef.current

    button.addEventListener('mouseenter', () => {
      gsap.to(button, {
        scale: 1.05,
        y: -2,
        boxShadow: "0 8px 25px rgba(59, 130, 246, 0.3)",
        duration: 0.3,
        ease: "back.out(1.7)"
      })

      // Create ripple effect
      const ripple = document.createElement('div')
      ripple.className = 'absolute inset-0 bg-blue-400 rounded-lg opacity-20 animate-ping'
      button.appendChild(ripple)
      setTimeout(() => ripple.remove(), 600)
    })

    button.addEventListener('mouseleave', () => {
      gsap.to(button, {
        scale: 1,
        y: 0,
        boxShadow: "0 0 0px rgba(59, 130, 246, 0)",
        duration: 0.3,
        ease: "power2.out"
      })
    })
  }

  // Staggered conversation animations
  const animateConversations = () => {
    conversationsRef.current.forEach((conv, index) => {
      if (!conv) return

      // Entrance animation
      gsap.fromTo(conv,
        { x: -50, opacity: 0, scale: 0.9 },
        { 
          x: 0, 
          opacity: 1, 
          scale: 1,
          duration: 0.5,
          delay: index * 0.1,
          ease: "back.out(1.7)"
        }
      )

      // Hover animations
      conv.addEventListener('mouseenter', () => {
        gsap.to(conv, {
          x: isCollapsed ? 0 : 5,
          scale: 1.02,
          duration: 0.3,
          ease: "power2.out"
        })

        // Glow effect for active conversation
        if (conv.dataset.active === 'true') {
          gsap.to(conv, {
            boxShadow: "0 0 15px rgba(59, 130, 246, 0.4)",
            duration: 0.3
          })
        }
      })

      conv.addEventListener('mouseleave', () => {
        gsap.to(conv, {
          x: 0,
          scale: 1,
          boxShadow: "0 0 0px rgba(59, 130, 246, 0)",
          duration: 0.3,
          ease: "power2.out"
        })
      })
    })
  }

  // Smooth sidebar collapse/expand
  const animateSidebarToggle = (collapsed) => {
    if (!sidebarRef.current) return

    const tl = gsap.timeline()

    if (collapsed) {
      // Collapsing animation
      tl.to(sidebarRef.current, {
        width: "4rem",
        duration: 0.5,
        ease: "power2.inOut"
      })
      .to(".sidebar-text", {
        opacity: 0,
        scale: 0.8,
        duration: 0.2,
        ease: "power2.in"
      }, 0)
      .to(".sidebar-full-width", {
        opacity: 0,
        duration: 0.3,
        ease: "power2.in"
      }, 0)
    } else {
      // Expanding animation
      tl.to(sidebarRef.current, {
        width: "16rem",
        duration: 0.5,
        ease: "power2.inOut"
      })
      .to(".sidebar-text", {
        opacity: 1,
        scale: 1,
        duration: 0.3,
        ease: "back.out(1.7)",
        delay: 0.2
      })
      .to(".sidebar-full-width", {
        opacity: 1,
        duration: 0.3,
        ease: "power2.out",
        delay: 0.2
      })
    }

    // Recreate sparkles after toggle
    setTimeout(() => createSparkles(), 500)
  }

  // Upgrade card animation
  const animateUpgradeCard = () => {
    if (!upgradeRef.current || isCollapsed) return

    gsap.fromTo(upgradeRef.current,
      { y: 20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8, ease: "back.out(1.7)", delay: 0.5 }
    )

    // Periodic highlight animation
    setInterval(() => {
      gsap.to(upgradeRef.current, {
        scale: 1.02,
        duration: 0.3,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut"
      })
    }, 8000)
  }

  // Toggle button animation
  const animateToggleButton = () => {
    if (!toggleRef.current) return

    toggleRef.current.addEventListener('mouseenter', () => {
      gsap.to(toggleRef.current, {
        scale: 1.1,
        rotation: 10,
        duration: 0.3,
        ease: "back.out(1.7)"
      })
    })

    toggleRef.current.addEventListener('mouseleave', () => {
      gsap.to(toggleRef.current, {
        scale: 1,
        rotation: 0,
        duration: 0.3,
        ease: "power2.out"
      })
    })
  }

  // Initialize animations
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Initial sidebar entrance
    gsap.fromTo(sidebarRef.current,
      { x: -100, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.8, ease: "power2.out" }
    )

    animateLogo()
    animateNewChatButton()
    animateToggleButton()
    createSparkles()

    return () => {
      gsap.killTweensOf([sidebarRef.current, logoRef.current, newChatRef.current, toggleRef.current])
    }
  }, [])

  // Animate conversations when they change
  useEffect(() => {
    animateConversations()
  }, [conversations])

  // Handle sidebar toggle
  useEffect(() => {
    animateSidebarToggle(isCollapsed)
  }, [isCollapsed])

  // Animate upgrade card
  useEffect(() => {
    if (!isCollapsed) {
      animateUpgradeCard()
    }
  }, [isCollapsed])

  return (
    <div 
      ref={sidebarRef}
      className="h-full flex flex-col bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 relative transition-all duration-500 overflow-hidden"
      style={{ width: isCollapsed ? '4rem' : '16rem' }}
    >
      {/* Header */}
      <div className={`border-b border-gray-800 ${isCollapsed ? 'p-2' : 'p-4'} relative z-10`}>
        <div className={`flex items-center gap-2 mb-4 ${isCollapsed ? 'justify-center' : ''}`}>
          <div 
            ref={logoRef}
            className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center relative overflow-hidden"
          >
            <Zap className="w-5 h-5 text-white relative z-10" />
            <div className="absolute inset-0 bg-gradient-to-r from-yellow-300 to-orange-400 opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
          </div>
          {!isCollapsed && (
            <span className="sidebar-text font-semibold text-lg text-white bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Lumina
            </span>
          )}
        </div>
        
        <Button 
          ref={newChatRef}
          onClick={onNewChat}
          className={`w-full bg-gradient-to-r from-gray-800 to-gray-700 hover:from-gray-700 hover:to-gray-600 text-white border border-gray-700 rounded-lg flex items-center gap-2 transition-all duration-300 relative overflow-hidden ${
            isCollapsed ? 'px-2 py-2 justify-center' : 'px-3 py-2 justify-start'
          }`}
          variant="outline"
        >
          <Plus className="w-4 h-4" />
          {!isCollapsed && <span className="sidebar-text">New Chat</span>}
          {!isCollapsed && <span className="sidebar-text ml-auto text-xs text-gray-400">⌘ N</span>}
        </Button>
      </div>

      {/* Navigation */}
      <div className={`py-2 ${isCollapsed ? 'px-2' : 'px-4'} relative z-10`}>
        <div className={`space-y-1 ${isCollapsed ? 'flex flex-col items-center' : ''}`}>
          {[
            { icon: MessageSquare, text: "Notifications" },
            { icon: User, text: "Community" },
            { icon: MessageSquare, text: "Commands" }
          ].map((item, index) => (
            <div 
              key={index}
              className={`flex items-center gap-2 p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-md cursor-pointer transition-all duration-300 group ${
                isCollapsed ? 'justify-center' : ''
              }`}
            >
              <item.icon className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
              {!isCollapsed && <span className="sidebar-text text-sm">{item.text}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Conversations */}
      <div className="flex-1 flex flex-col overflow-hidden relative z-10">
        <div className={`py-2 ${isCollapsed ? 'px-2' : 'px-4'}`}>
          <h3 className={`text-sm text-gray-500 font-medium ${isCollapsed ? 'text-center' : ''}`}>
            {isCollapsed ? (
              <MessageSquare className="w-4 h-4 mx-auto" />
            ) : (
              <span className="sidebar-text">Recent Conversations</span>
            )}
          </h3>
        </div>
        
        <ScrollArea className={`flex-1 ${isCollapsed ? 'px-2' : 'px-4'}`}>
          <div className="space-y-1">
            {conversations.map((conversation, index) => (
              <div
                key={conversation.id}
                ref={el => conversationsRef.current[index] = el}
                data-active={activeConversationId === conversation.id}
                onClick={() => onConversationSelect(conversation.id)}
                className={`rounded-lg cursor-pointer transition-all duration-300 group relative overflow-hidden ${
                  activeConversationId === conversation.id 
                    ? 'bg-gradient-to-r from-gray-800 to-gray-700 text-white shadow-lg' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                } ${isCollapsed ? 'p-2 flex justify-center' : 'p-3'}`}
              >
                {isCollapsed ? (
                  <MessageSquare className="w-5 h-5" />
                ) : (
                  <>
                    <div className="sidebar-text text-sm font-medium truncate relative z-10">
                      {conversation.title}
                    </div>
                    <div className="sidebar-text text-xs text-gray-500 mt-1 relative z-10">
                      {new Date(conversation.createdAt).toLocaleDateString()}
                    </div>
                    {activeConversationId === conversation.id && (
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 opacity-50"></div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Upgrade Section */}
      {!isCollapsed && (
        <div className="sidebar-full-width p-4 border-t border-gray-800 relative z-10">
          <div 
            ref={upgradeRef}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg p-3 mb-3 border border-gray-700 relative overflow-hidden"
          >
            <div className="absolute top-2 right-2">
              <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
            </div>
            <div className="text-sm text-gray-300 mb-2 flex items-center gap-1">
              <Star className="w-3 h-3 text-yellow-400" />
              Your trial ends in 14 days
            </div>
            <div className="text-xs text-gray-400 mb-3">
              Enjoy working with reports, extract data, advanced search experience and much more.
            </div>
            <Button className="w-full bg-gradient-to-r from-lime-400 to-lime-500 hover:from-lime-500 hover:to-lime-600 text-black border-0 font-medium transition-all duration-300 hover:scale-105 hover:shadow-lg">
              ↗ Upgrade
            </Button>
          </div>
        </div>
      )}

      {/* Toggle Button */}
      <div className="absolute bottom-4 right-4 z-20">
        <Button
          ref={toggleRef}
          onClick={onToggleCollapse}
          variant="ghost"
          size="icon"
          className="bg-gradient-to-r from-gray-800 to-gray-700 hover:from-gray-700 hover:to-gray-600 text-white rounded-full h-8 w-8 border border-gray-700 shadow-lg transition-all duration-300"
        >
          {isCollapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <ChevronsLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
