'use client'

import { useState, useEffect } from 'react'
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
  MessageSquare
} from 'lucide-react'

export default function RightSidebar() {
  const [activeSection, setActiveSection] = useState('system')
  const [expandedSections, setExpandedSections] = useState({
    tokenUsage: true,
    systemStatus: true,
    collections: false,
    capabilities: false,
    streaming: false
  })

  // Mock real-time data - in real app, this would come from SSE or websockets
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

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        tokenUsage: {
          ...prev.tokenUsage,
          totalTokens: prev.tokenUsage.totalTokens + Math.floor(Math.random() * 50),
          llmCalls: prev.tokenUsage.llmCalls + (Math.random() > 0.8 ? 1 : 0)
        },
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
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-2">Brain LLM Monitor</h2>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={activeSection === 'system' ? 'default' : 'ghost'}
            onClick={() => setActiveSection('system')}
            className="text-xs h-7"
          >
            <Activity className="w-3 h-3 mr-1" />
            System
          </Button>
          <Button
            size="sm"
            variant={activeSection === 'data' ? 'default' : 'ghost'}
            onClick={() => setActiveSection('data')}
            className="text-xs h-7"
          >
            <Database className="w-3 h-3 mr-1" />
            Data
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {/* Token Usage Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <button
              onClick={() => toggleSection('tokenUsage')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-white">Token Usage</span>
              </div>
              {expandedSections.tokenUsage ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.tokenUsage && (
              <div className="px-3 pb-3 space-y-3">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Total Tokens</div>
                    <div className="text-white font-medium">{formatNumber(systemMetrics.tokenUsage.totalTokens)}</div>
                  </div>
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">LLM Calls</div>
                    <div className="text-white font-medium">{systemMetrics.tokenUsage.llmCalls}</div>
                  </div>
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Prompt</div>
                    <div className="text-blue-400 font-medium">{formatNumber(systemMetrics.tokenUsage.promptTokens)}</div>
                  </div>
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Response</div>
                    <div className="text-green-400 font-medium">{formatNumber(systemMetrics.tokenUsage.responseTokens)}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Avg Time</div>
                    <div className="text-yellow-400 font-medium">{systemMetrics.tokenUsage.avgResponseTime}s</div>
                  </div>
                  <div className="bg-gray-700 rounded p-2">
                    <div className="text-gray-400">Est. Cost</div>
                    <div className="text-purple-400 font-medium">${systemMetrics.tokenUsage.costEstimate}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* System Status */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <button
              onClick={() => toggleSection('systemStatus')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-white">System Health</span>
              </div>
              {expandedSections.systemStatus ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.systemStatus && (
              <div className="px-3 pb-3 space-y-2">
                {Object.entries(systemMetrics.systemHealth).map(([service, status]) => (
                  <div key={service} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(status)}
                      <span className="text-xs text-gray-300 capitalize">{service.replace(/([A-Z])/g, ' $1')}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
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
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <button
              onClick={() => toggleSection('streaming')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-medium text-white">Query Processing</span>
              </div>
              {expandedSections.streaming ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.streaming && (
              <div className="px-3 pb-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Active Streams</span>
                  <span className="text-xs text-white font-medium">{systemMetrics.streamingStatus.activeStreams}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Total Queries</span>
                  <span className="text-xs text-white font-medium">{formatNumber(systemMetrics.streamingStatus.totalQueries)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Avg Processing</span>
                  <span className="text-xs text-white font-medium">{systemMetrics.streamingStatus.avgProcessingTime}s</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Last Update</span>
                  <span className="text-xs text-gray-400">{systemMetrics.streamingStatus.lastUpdate.toLocaleTimeString()}</span>
                </div>
              </div>
            )}
          </div>

          {/* ChromaDB Collections */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <button
              onClick={() => toggleSection('collections')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-white">Vector Collections</span>
              </div>
              {expandedSections.collections ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.collections && (
              <div className="px-3 pb-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">DQ Rules</span>
                  <span className="text-xs text-white font-medium">{formatNumber(systemMetrics.collections.dqRules)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Conversations</span>
                  <span className="text-xs text-white font-medium">{formatNumber(systemMetrics.collections.conversations)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Query Cache</span>
                  <span className="text-xs text-white font-medium">{formatNumber(systemMetrics.collections.queryCache)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">Schema Embeddings</span>
                  <span className="text-xs text-white font-medium">{formatNumber(systemMetrics.collections.schemaEmbeddings)}</span>
                </div>
              </div>
            )}
          </div>

          {/* AI Capabilities */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <button
              onClick={() => toggleSection('capabilities')}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-medium text-white">AI Tools</span>
              </div>
              {expandedSections.capabilities ? 
                <ChevronDown className="w-4 h-4 text-gray-400" /> : 
                <ChevronRight className="w-4 h-4 text-gray-400" />
              }
            </button>
            {expandedSections.capabilities && (
              <div className="px-3 pb-3 space-y-2">
                {Object.entries(systemMetrics.aiCapabilities).map(([capability, data]) => (
                  <div key={capability} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(data.status)}
                      <span className="text-xs text-gray-300 capitalize">
                        {capability.replace(/([A-Z])/g, ' $1')}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">{data.usage}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <h3 className="text-sm font-medium text-white mb-3">System Actions</h3>
            <div className="space-y-2">
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-xs text-gray-300 hover:text-white h-7"
              >
                <Upload className="w-3 h-3 mr-2" />
                Upload DQ Rules (Soon)
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-xs text-gray-300 hover:text-white h-7"
              >
                <Search className="w-3 h-3 mr-2" />
                Search Collections
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-xs text-gray-300 hover:text-white h-7"
              >
                <TrendingUp className="w-3 h-3 mr-2" />
                View Analytics
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-xs text-gray-300 hover:text-white h-7"
              >
                <FileText className="w-3 h-3 mr-2" />
                Export Logs
              </Button>
            </div>
          </div>

          {/* Footer Info */}
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
