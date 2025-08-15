'use client'

import { ScrollArea } from '@/components/ui/scroll-area'
import { Brain, Database, Search, MessageSquare, Zap, Activity, Code, Bot, Layers, ChevronRight, Clock, CheckCircle2, Loader2, TrendingUp } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function RightSidebar({ tokenUsage, processingSteps = [], activeTools = [] }) {
  const [activeFeatures, setActiveFeatures] = useState({
    sqlGeneration: false,
    vectorSearch: false,
    dqRules: false,
    streaming: false
  })

  const systemCapabilities = [
    {
      category: "AI-Powered Query Generation",
      icon: Brain,
      color: "text-blue-500",
      features: [
        "Natural Language → SQL Translation",
        "600+ Data Quality Rules",
        "Real-time Schema Discovery",
        "Conversational Query Refinement"
      ]
    },
    {
      category: "Vector-Enhanced Search",
      icon: Search,
      color: "text-purple-500",
      features: [
        "ChromaDB Semantic Search",
        "Sentence Transformers",
        "Rule Similarity Matching",
        "Context-Aware Retrieval"
      ]
    },
    {
      category: "Streaming Intelligence",
      icon: Zap,
      color: "text-yellow-500",
      features: [
        "Server-Sent Events (SSE)",
        "LangChain Agent Framework",
        "Real-time Token Tracking",
        "Multi-tool Orchestration"
      ]
    },
    {
      category: "Data Quality Management",
      icon: Database,
      color: "text-green-500",
      features: [
        "Automated DQ Rule Discovery",
        "SQL Validation Generation",
        "Business Rule Compliance",
        "Quality Dimension Analysis"
      ]
    }
  ]

  const agentTools = [
    { name: "sql_workflow", description: "Natural language → SQL → Results", active: false },
    { name: "query_dq_rules", description: "Semantic DQ rule discovery", active: false },
    { name: "generate_visualization", description: "ER diagrams & relationships", active: false },
    { name: "conversational_response", description: "Direct chat interactions", active: false }
  ]

  const [tools, setTools] = useState(agentTools)
  const [processingSteps, setProcessingSteps] = useState([])

  // Simulate real processing steps based on backend documentation
  const simulateProcessing = () => {
    const steps = [
      "🧠 Analyzing natural language query...",
      "🔍 Discovering database schema...", 
      "⚡ Selecting appropriate LangChain tool...",
      "📝 Generating optimized SQL query...",
      "🎯 Executing query on target database...",
      "📊 Formatting results for presentation...",
      "🔢 Calculating token usage metrics..."
    ]
    
    setProcessingSteps([])
    steps.forEach((step, index) => {
      setTimeout(() => {
        setProcessingSteps(prev => [...prev, { text: step, timestamp: new Date().toLocaleTimeString() }])
      }, index * 800)
    })
  }

  useEffect(() => {
    // Simulate periodic tool activation
    const interval = setInterval(() => {
      setTools(prev => prev.map((tool, index) => ({
        ...tool,
        active: Math.random() > 0.7
      })))
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="h-full flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="w-6 h-6 text-blue-400" />
          <h2 className="text-lg font-semibold">Brain LLM Intelligence</h2>
        </div>
        <p className="text-sm text-gray-400">AI-Powered SQL & Data Quality System</p>
      </div>

      <ScrollArea className="flex-1">
        {/* Real-time Processing */}
        {(tokenUsage || processingSteps.length > 0 || activeTools.length > 0) && (
          <div className="p-6 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-green-400" />
              Live Processing
            </h3>
            
            {/* Token Usage */}
            {tokenUsage && (
              <div className="bg-gray-800 rounded-lg p-4 mb-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-yellow-400" />
                  <h4 className="text-xs font-medium text-white">Token Usage</h4>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="text-gray-400">
                    <div>Input: <span className="text-white">{tokenUsage.input_tokens || 0}</span></div>
                    <div>Output: <span className="text-white">{tokenUsage.output_tokens || 0}</span></div>
                  </div>
                  <div className="text-gray-400">
                    <div>Total: <span className="text-white">{(tokenUsage.input_tokens || 0) + (tokenUsage.output_tokens || 0)}</span></div>
                    <div>Calls: <span className="text-white">{tokenUsage.llm_calls_count || 1}</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* Active Tools */}
            {activeTools.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-4 mb-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="w-4 h-4 text-blue-400" />
                  <h4 className="text-xs font-medium text-white">Agent Tools</h4>
                </div>
                <div className="space-y-2">
                  {activeTools.map((tool, index) => (
                    <div key={index} className="flex items-center gap-2 text-xs">
                      {tool.status === 'running' ? (
                        <Loader2 className="w-3 h-3 text-yellow-400 animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-3 h-3 text-green-400" />
                      )}
                      <span className="text-gray-300">{tool.tool}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Processing Steps */}
            {processingSteps.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-4 h-4 text-purple-400" />
                  <h4 className="text-xs font-medium text-white">Processing Steps</h4>
                </div>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {processingSteps.slice(-5).map((step, index) => (
                    <div key={step.id} className="flex items-start gap-2 text-xs">
                      <div className="w-1 h-1 bg-purple-400 rounded-full mt-2 flex-shrink-0"></div>
                      <span className="text-gray-300">{step.step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* System Capabilities */}
        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4" />
              System Capabilities
            </h3>
            <div className="space-y-4">
              {systemCapabilities.map((capability, index) => {
                const IconComponent = capability.icon
                return (
                  <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <div className="flex items-center gap-3 mb-3">
                      <IconComponent className={`w-5 h-5 ${capability.color}`} />
                      <h4 className="font-medium text-sm text-white">{capability.category}</h4>
                    </div>
                    <div className="space-y-2">
                      {capability.features.map((feature, fIndex) => (
                        <div key={fIndex} className="flex items-center gap-2 text-xs text-gray-400">
                          <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                          {feature}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* LangChain Agent Tools */}
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Bot className="w-4 h-4" />
              Active Agent Tools
            </h3>
            <div className="space-y-2">
              {tools.map((tool, index) => (
                <div 
                  key={index} 
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                    tool.active 
                      ? 'bg-green-900/20 border-green-600/30 text-green-400' 
                      : 'bg-gray-800 border-gray-700 text-gray-400'
                  }`}
                >
                  <div>
                    <div className="font-mono text-xs font-medium">{tool.name}</div>
                    <div className="text-xs opacity-80">{tool.description}</div>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${tool.active ? 'bg-green-400' : 'bg-gray-600'}`}></div>
                </div>
              ))}
            </div>
          </div>

          {/* Processing Pipeline */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Processing Pipeline
              </h3>
              <button 
                onClick={simulateProcessing}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Simulate
              </button>
            </div>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {processingSteps.map((step, index) => (
                <div key={index} className="flex items-start gap-3 text-xs">
                  <span className="text-gray-500 font-mono">{step.timestamp}</span>
                  <span className="text-gray-300 flex-1">{step.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Technical Stack */}
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Code className="w-4 h-4" />
              Tech Stack
            </h3>
            <div className="grid grid-cols-1 gap-2 text-xs">
              {[
                { name: "LangChain", desc: "Agent Framework", color: "bg-blue-500" },
                { name: "ChromaDB", desc: "Vector Store", color: "bg-purple-500" },
                { name: "Gemini", desc: "LLM Provider", color: "bg-yellow-500" },
                { name: "FastAPI", desc: "Backend", color: "bg-green-500" }
              ].map((tech, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${tech.color}`}></div>
                  <span className="text-white font-medium">{tech.name}</span>
                  <span className="text-gray-400">{tech.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Data Quality Rules */}
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-4">DQ Rule Repository</h3>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-400">600+</div>
                  <div className="text-xs text-gray-400">Rules Available</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">95%</div>
                  <div className="text-xs text-gray-400">Match Accuracy</div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-700 text-xs text-gray-400">
                <div>Domains: Customer Master, Sales, Finance, HR</div>
                <div>SAP Modules: FI, CO, SD, MM, HR</div>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  )
}
