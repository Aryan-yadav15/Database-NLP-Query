'use client'

import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'

export default function ParticleBackground() {
  const canvasRef = useRef(null)
  const particlesRef = useRef([])
  const animationRef = useRef(null)

  useEffect(() => {
    if (typeof window === 'undefined') return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    
    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Particle class
    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height
        this.vx = (Math.random() - 0.5) * 0.5
        this.vy = (Math.random() - 0.5) * 0.5
        this.life = Math.random() * 100 + 100
        this.maxLife = this.life
        this.size = Math.random() * 2 + 1
        this.opacity = Math.random() * 0.5 + 0.1
        
        // Color variations
        const colors = [
          { r: 59, g: 130, b: 246 },   // Blue
          { r: 147, g: 51, b: 234 },   // Purple
          { r: 236, g: 72, b: 153 },   // Pink
          { r: 34, g: 197, b: 94 },    // Green
          { r: 251, g: 191, b: 36 }    // Yellow
        ]
        this.color = colors[Math.floor(Math.random() * colors.length)]
      }

      update() {
        this.x += this.vx
        this.y += this.vy
        this.life--

        // Fade out as life decreases
        this.opacity = (this.life / this.maxLife) * 0.5

        // Wrap around screen
        if (this.x < 0) this.x = canvas.width
        if (this.x > canvas.width) this.x = 0
        if (this.y < 0) this.y = canvas.height
        if (this.y > canvas.height) this.y = 0
      }

      draw() {
        ctx.save()
        ctx.globalAlpha = this.opacity
        ctx.fillStyle = `rgb(${this.color.r}, ${this.color.g}, ${this.color.b})`
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      }

      isDead() {
        return this.life <= 0
      }
    }

    // Initialize particles
    const createParticles = () => {
      particlesRef.current = []
      for (let i = 0; i < 50; i++) {
        particlesRef.current.push(new Particle())
      }
    }

    // Animation loop
    const animate = () => {
      // Clear canvas with fade effect
      ctx.fillStyle = 'rgba(0, 0, 0, 0.02)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Update and draw particles
      particlesRef.current.forEach((particle, index) => {
        particle.update()
        particle.draw()

        // Remove dead particles and create new ones
        if (particle.isDead()) {
          particlesRef.current[index] = new Particle()
        }
      })

      animationRef.current = requestAnimationFrame(animate)
    }

    createParticles()
    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  return (
    <canvas 
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-30"
      style={{ mixBlendMode: 'screen' }}
    />
  )
}
