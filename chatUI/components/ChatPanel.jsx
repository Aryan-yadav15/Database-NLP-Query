'use client'

import { useState, useRef, useEffect } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import ChatInput from '@/components/ChatInput'
import Message from '@/components/Message'
import TokenTracker from '@/components/TokenTracker'
import DatabaseSelector from '@/components/DatabaseSelector'
import { useToast } from '@/components/ui/toast'
import { v4 as uuidv4 } from 'uuid'

const SUGGESTED_PROMPTS = [
  {
    icon: '🧠',
    title: 'Show me the top 5 customers by total sales',
    description: 'Natural language to SQL generation'
  },
  {
    icon: '◆',
    title: 'Find data quality rules for customer addresses',
    description: 'Vector search in 600+ DQ rules'
  },
  {
    icon: '📊',
    title: 'Generate an ER diagram for sales tables',
    description: 'Smart visualization creation'
  },
  {
    icon: '🔍',
    title: 'What are the monthly sales trends?',
    description: 'Query generation with insights'
  }
]

export default function ChatPanel({ 
  conversation, 
  dbConnection, 
  onDbConnectionChange, 
  onUpdateTitle, 
  onAddMessage
}) {
  const [isLoading, setIsLoading] = useState(false)
  const [tokenUsage, setTokenUsage] = useState(null)
  const [processingSteps, setProcessingSteps] = useState([])
  const [activeTools, setActiveTools] = useState([])
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [conversation?.messages])

  const { addToast } = useToast()

  const handleSendMessage = async (message) => {
    if (!conversation || !dbConnection) {
      addToast('Please connect to a database first', 'warning')
      return
    }

    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }

    // Add user message immediately
    onAddMessage(conversation.id, userMessage)

    // Update conversation title if it's the first message
    if (conversation.messages.length === 0) {
      const title = message.length > 50 ? message.substring(0, 50) + '...' : message
      onUpdateTitle(conversation.id, title)
    }

    setIsLoading(true)
    setTokenUsage(null)
    setProcessingSteps([])
    setActiveTools([])

    try {
      const requestBody = {
        query_text: message,
        user_id: "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
        conversation_id: conversation.id,
        message_id: uuidv4(),
        chat_history: conversation.messages.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        short_term_memory: [],
        model_name: "gemini-2.0-flash-lite",
        temperature: 0.2,
        api_key: "AIzaSyA4IHwHEifp7wcCFhGmLITY2rvelvWH-qY",
        db_connection_info: dbConnection
      }

      const response = await fetch('/api/v1/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(requestBody)
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
        timestamp: new Date().toISOString(),
        status: 'Analyzing query...',
        sql: '',
        table: null
      }

      onAddMessage(conversation.id, assistantMessage)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('event:')) {
            const eventType = line.substring(6).trim()
            continue
          }
          
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.substring(5).trim())
              
              if (data.message) {
                // Status update
                assistantMessage = { ...assistantMessage, status: data.message }
                onAddMessage(conversation.id, assistantMessage)
                
                // Track processing steps for visualization
                setProcessingSteps(prev => [...prev.slice(-4), {
                  id: Date.now(),
                  step: data.message,
                  timestamp: Date.now()
                }])
              } else if (data.answer_text) {
                // Structured response
                assistantMessage = {
                  ...assistantMessage,
                  content: data.answer_text,
                  sql: data.sql || '',
                  table: data.table || null,
                  status: null
                }
                onAddMessage(conversation.id, assistantMessage)
              } else if (data.token_usage) {
                // Token usage
                setTokenUsage({
                  ...data.token_usage,
                  llm_calls_count: data.llm_calls_count || 1
                })
              } else if (data.tool_start) {
                // Track tool execution
                setActiveTools(prev => [...prev, {
                  tool: data.tool_name,
                  status: 'running',
                  timestamp: Date.now()
                }])
              } else if (data.tool_complete) {
                // Mark tool as complete
                setActiveTools(prev => prev.map(tool =>
                  tool.tool === data.tool_name
                    ? { ...tool, status: 'complete' }
                    : tool
                ))
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
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
    }
  }

  const handlePromptClick = (prompt) => {
    handleSendMessage(prompt.title)
  }

  const handleDatabaseTypeChange = (newDbType) => {
    // Update the database connection info with new type
    const updatedConnection = {
      ...dbConnection,
      db_type: newDbType
    }
    onDbConnectionChange(updatedConnection)
  }

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-6">
        {conversation.messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center max-w-3xl mx-auto px-4">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-3">Hi, Aryan</h1>

              <h2 className="text-xl font-semibold text-gray-700 mb-4">What can I help you with?</h2>
              <p className="text-gray-500 text-sm">Choose a prompt below or write your own to start chatting with Lumina.</p>
            </div>

            <div className="grid grid-cols-2 gap-2.5 w-full max-w-xl">
              {SUGGESTED_PROMPTS.map((prompt, index) => (
                <div
                  key={index}
                  onClick={() => handlePromptClick(prompt)}
                  className="p-2.5 bg-gray-50 rounded-xl border border-gray-200 hover:border-gray-300 hover:bg-gray-100 cursor-pointer transition-all duration-200 group"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-sm">{prompt.icon}</span>
                    <div>
                      <h3 className="font-medium text-gray-900 mb-0.5 text-xs group-hover:text-gray-800 leading-tight">{prompt.title}</h3>
                      <p className="text-xs text-gray-600 leading-tight">{prompt.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {conversation.messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* Chat Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="max-w-4xl mx-auto">
          
          {/* Database Selector */}
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Database:</span>
              <DatabaseSelector 
                currentDbType={dbConnection?.db_type || 'postgresql'}
                onDatabaseTypeChange={handleDatabaseTypeChange}
              />
            </div>
            
            {/* Processing Steps Indicator */}
            {processingSteps.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="text-xs text-gray-500">
                  {processingSteps[processingSteps.length - 1]}
                </div>
                <div className="animate-spin w-3 h-3 border border-gray-300 border-t-blue-500 rounded-full"></div>
              </div>
            )}
          </div>

          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            dbConnection={dbConnection}
            onDbConnectionChange={onDbConnectionChange}
          />
          
          {/* Token Tracker */}
          {tokenUsage && (
            <div className="mt-2">
              <TokenTracker tokenUsage={tokenUsage} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
