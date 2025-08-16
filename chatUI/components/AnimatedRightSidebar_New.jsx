'use client'

import { useState, useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { 
  Settings, 
  Database, 
  Key, 
  User, 
  Brain,
  Thermometer,
  Save,
  RotateCcw,
  Eye,
  EyeOff,
  ChevronDown, 
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Download,
  Upload
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

// Register GSAP plugins
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

export default function AnimatedRightSidebar({ 
  config = {}, 
  onConfigChange, 
  tokenUsage, 
  processingSteps = [], 
  activeTools = [] 
}) {
  const [localConfig, setLocalConfig] = useState({
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

  const [expandedSections, setExpandedSections] = useState({
    apiConfig: true,
    database: true,
    memory: false,
    monitoring: false,
    actions: false
  })

  const [showPasswords, setShowPasswords] = useState({
    api_key: false,
    db_password: false
  })

  const [unsavedChanges, setUnsavedChanges] = useState(false)

  // Refs for animations
  const containerRef = useRef(null)
  const headerRef = useRef(null)
  const sectionsRef = useRef([])

  // Initialize local config from props
  useEffect(() => {
    if (config && Object.keys(config).length > 0) {
      setLocalConfig(prev => ({ ...prev, ...config }))
    }
  }, [config])

  // Track unsaved changes
  useEffect(() => {
    if (config && Object.keys(config).length > 0) {
      const hasChanges = JSON.stringify(localConfig) !== JSON.stringify(config)
      setUnsavedChanges(hasChanges)
    }
  }, [localConfig, config])

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }))
  }

  const handleConfigChange = (path, value) => {
    setLocalConfig(prev => {
      const newConfig = { ...prev }
      const keys = path.split('.')
      let current = newConfig
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {}
        current = current[keys[i]]
      }
      
      if (keys[keys.length - 1] === 'db_port') {
        current[keys[keys.length - 1]] = parseInt(value) || 5432
      } else {
        current[keys[keys.length - 1]] = value
      }
      
      return newConfig
    })
  }

  const handleMemoryChange = (index, value) => {
    setLocalConfig(prev => ({
      ...prev,
      short_term_memory: prev.short_term_memory.map((item, i) => 
        i === index ? value : item
      )
    }))
  }

  const addMemoryItem = () => {
    setLocalConfig(prev => ({
      ...prev,
      short_term_memory: [...prev.short_term_memory, ""]
    }))
  }

  const removeMemoryItem = (index) => {
    setLocalConfig(prev => ({
      ...prev,
      short_term_memory: prev.short_term_memory.filter((_, i) => i !== index)
    }))
  }

  const saveConfig = () => {
    if (onConfigChange) {
      onConfigChange(localConfig)
      setUnsavedChanges(false)
    }
  }

  const resetConfig = () => {
    if (config && Object.keys(config).length > 0) {
      setLocalConfig(config)
      setUnsavedChanges(false)
    }
  }

  const copyConfig = () => {
    navigator.clipboard.writeText(JSON.stringify(localConfig, null, 2))
  }

  const exportConfig = () => {
    const blob = new Blob([JSON.stringify(localConfig, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'brain-llm-config.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  // Animation effects
  useEffect(() => {
    if (typeof window === 'undefined') return

    const tl = gsap.timeline()
    
    tl.fromTo(headerRef.current,
      { y: -30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, ease: "back.out(1.7)" }
    )

    sectionsRef.current.forEach((section, index) => {
      if (section) {
        gsap.fromTo(section, 
          { x: 50, opacity: 0 },
          { x: 0, opacity: 1, duration: 0.5, delay: index * 0.1, ease: "power2.out" }
        )
      }
    })

    return () => {
      gsap.killTweensOf([headerRef.current, ...sectionsRef.current])
    }
  }, [])

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-gradient-to-b from-gray-900 to-gray-800 relative overflow-hidden">
      
      {/* Header */}
      <div ref={headerRef} className="p-4 border-b border-gray-700 bg-gradient-to-r from-gray-800 to-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-400" />
            Configuration
          </h2>
          {unsavedChanges && (
            <div className="flex items-center gap-1 text-xs text-yellow-400">
              <AlertTriangle className="w-3 h-3" />
              Unsaved
            </div>
          )}
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={saveConfig}
            disabled={!unsavedChanges}
            className="text-xs h-7 bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-3 h-3 mr-1" />
            Save
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={resetConfig}
            disabled={!unsavedChanges}
            className="text-xs h-7"
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Reset
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          
          {/* API Configuration */}
          <div 
            ref={el => sectionsRef.current[0] = el}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg"
          >
            <button
              onClick={() => toggleSection('apiConfig')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/50 transition-all duration-300 rounded-t-lg"
            >
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-yellow-400" />
                <span className="text-sm font-medium text-white">API Configuration</span>
              </div>
              {expandedSections.apiConfig ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.apiConfig && (
              <div className="p-3 space-y-3 border-t border-gray-700">
                <div>
                  <Label className="text-xs text-gray-400">User ID</Label>
                  <Input
                    value={localConfig.user_id}
                    onChange={(e) => handleConfigChange('user_id', e.target.value)}
                    className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                    placeholder="Enter user ID"
                  />
                </div>
                
                <div>
                  <Label className="text-xs text-gray-400">API Key</Label>
                  <div className="relative mt-1">
                    <Input
                      type={showPasswords.api_key ? "text" : "password"}
                      value={localConfig.api_key}
                      onChange={(e) => handleConfigChange('api_key', e.target.value)}
                      className="bg-gray-700 border-gray-600 text-white text-xs pr-8"
                      placeholder="Enter Gemini API key"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility('api_key')}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                    >
                      {showPasswords.api_key ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    </button>
                  </div>
                </div>

                <div>
                  <Label className="text-xs text-gray-400">Model Name</Label>
                  <Input
                    value={localConfig.model_name}
                    onChange={(e) => handleConfigChange('model_name', e.target.value)}
                    className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                    placeholder="gemini-2.0-flash"
                  />
                </div>

                <div>
                  <Label className="text-xs text-gray-400">Temperature ({localConfig.temperature})</Label>
                  <div className="mt-1 flex items-center gap-2">
                    <Thermometer className="w-3 h-3 text-blue-400" />
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={localConfig.temperature}
                      onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                      className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-xs text-gray-400 w-8">{localConfig.temperature}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Database Configuration */}
          <div 
            ref={el => sectionsRef.current[1] = el}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg"
          >
            <button
              onClick={() => toggleSection('database')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/50 transition-all duration-300 rounded-t-lg"
            >
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-white">Database Connection</span>
              </div>
              {expandedSections.database ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.database && (
              <div className="p-3 space-y-3 border-t border-gray-700">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs text-gray-400">Host</Label>
                    <Input
                      value={localConfig.db_connection_info.db_host}
                      onChange={(e) => handleConfigChange('db_connection_info.db_host', e.target.value)}
                      className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                      placeholder="localhost"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-gray-400">Port</Label>
                    <Input
                      type="number"
                      value={localConfig.db_connection_info.db_port}
                      onChange={(e) => handleConfigChange('db_connection_info.db_port', e.target.value)}
                      className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                      placeholder="5432"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs text-gray-400">Database Name</Label>
                  <Input
                    value={localConfig.db_connection_info.db_name}
                    onChange={(e) => handleConfigChange('db_connection_info.db_name', e.target.value)}
                    className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                    placeholder="chinook"
                  />
                </div>

                <div>
                  <Label className="text-xs text-gray-400">Username</Label>
                  <Input
                    value={localConfig.db_connection_info.db_user}
                    onChange={(e) => handleConfigChange('db_connection_info.db_user', e.target.value)}
                    className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                    placeholder="postgres"
                  />
                </div>

                <div>
                  <Label className="text-xs text-gray-400">Password</Label>
                  <div className="relative mt-1">
                    <Input
                      type={showPasswords.db_password ? "text" : "password"}
                      value={localConfig.db_connection_info.db_password}
                      onChange={(e) => handleConfigChange('db_connection_info.db_password', e.target.value)}
                      className="bg-gray-700 border-gray-600 text-white text-xs pr-8"
                      placeholder="Enter database password"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility('db_password')}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                    >
                      {showPasswords.db_password ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    </button>
                  </div>
                </div>

                <div>
                  <Label className="text-xs text-gray-400">Schema (Optional)</Label>
                  <Input
                    value={localConfig.db_connection_info.db_schema || ''}
                    onChange={(e) => handleConfigChange('db_connection_info.db_schema', e.target.value || null)}
                    className="mt-1 bg-gray-700 border-gray-600 text-white text-xs"
                    placeholder="Leave empty for default"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Short-term Memory */}
          <div 
            ref={el => sectionsRef.current[2] = el}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg"
          >
            <button
              onClick={() => toggleSection('memory')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-700/50 transition-all duration-300 rounded-t-lg"
            >
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-white">Short-term Memory</span>
              </div>
              {expandedSections.memory ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.memory && (
              <div className="p-3 space-y-3 border-t border-gray-700">
                {localConfig.short_term_memory.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <Textarea
                      value={item}
                      onChange={(e) => handleMemoryChange(index, e.target.value)}
                      className="flex-1 bg-gray-700 border-gray-600 text-white text-xs min-h-[60px]"
                      placeholder="Enter memory context..."
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeMemoryItem(index)}
                      disabled={localConfig.short_term_memory.length === 1}
                      className="text-xs h-fit mt-1"
                    >
                      ✕
                    </Button>
                  </div>
                ))}
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={addMemoryItem}
                  className="w-full text-xs"
                >
                  + Add Memory Item
                </Button>
              </div>
            )}
          </div>

          {/* Token Usage Monitor */}
          {tokenUsage && (
            <div 
              ref={el => sectionsRef.current[3] = el}
              className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 shadow-lg"
            >
              <div className="p-3">
                <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  Token Usage
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Total</div>
                    <div className="text-white font-medium">{tokenUsage.total || 0}</div>
                  </div>
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Cost</div>
                    <div className="text-white font-medium">${tokenUsage.cost || '0.00'}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Config Actions */}
          <div 
            ref={el => sectionsRef.current[4] = el}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg border border-gray-600 p-3"
          >
            <h3 className="text-sm font-medium text-white mb-3">Config Actions</h3>
            <div className="space-y-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={copyConfig}
                className="w-full justify-start text-xs text-gray-300 hover:text-white h-7"
              >
                <Copy className="w-3 h-3 mr-2" />
                Copy Configuration
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={exportConfig}
                className="w-full justify-start text-xs text-gray-300 hover:text-white h-7"
              >
                <Download className="w-3 h-3 mr-2" />
                Export Config
              </Button>
            </div>
          </div>

        </div>
      </ScrollArea>
    </div>
  )
}
