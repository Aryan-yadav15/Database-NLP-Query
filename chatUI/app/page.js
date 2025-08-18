'use client'

import { useState, useEffect } from 'react'
import AnimatedLeftSidebar from '@/components/AnimatedLeftSidebar'
import AnimatedRightSidebar from '@/components/AnimatedRightSidebar'
import AnimatedChatPanel from '@/components/AnimatedChatPanel'
import { ToastProvider } from '@/components/ui/toast'
import { v4 as uuidv4 } from 'uuid'

export default function Home() {
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [dbConnection, setDbConnection] = useState(null)
  const [globalTokenUsage, setGlobalTokenUsage] = useState(null)
  const [globalProcessingSteps, setGlobalProcessingSteps] = useState([])
  const [globalActiveTools, setGlobalActiveTools] = useState([])
  const [tokenUsage, setTokenUsage] = useState(null)
  const [processingSteps, setProcessingSteps] = useState([])
  const [activeTools, setActiveTools] = useState([])
  const [isLeftSidebarCollapsed, setIsLeftSidebarCollapsed] = useState(false)
  const [chatConfig, setChatConfig] = useState({
    user_id: "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
    api_key: "AIzaSyBja5P8lEZQ6qYs1SM2ZRXwzm9EgCsERLc",
    model_name: "gemini-2.0-flash",
    temperature: 0.2,
    db_connection_info: {
      db_type: "postgresql",      // Add database type
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

  // Initialize with a default conversation and database connection
  useEffect(() => {
    const defaultConversation = {
      id: uuidv4(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString()
    }
    setConversations([defaultConversation])
    setActiveConversationId(defaultConversation.id)
    
    // Initialize database connection from config
    setDbConnection(chatConfig.db_connection_info)
  }, [])

  const toggleLeftSidebar = () => {
    setIsLeftSidebarCollapsed(prev => !prev)
  }

  const createNewChat = () => {
    const newConversation = {
      id: uuidv4(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString()
    }
    setConversations(prev => [newConversation, ...prev])
    setActiveConversationId(newConversation.id)
  }

  const updateConversationTitle = (conversationId, title) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { ...conv, title: title.substring(0, 50) + (title.length > 50 ? '...' : '') }
          : conv
      )
    )
  }

  const addMessageToConversation = (conversationId, message) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { ...conv, messages: [...conv.messages, message] }
          : conv
      )
    )
  }

  const updateMessageInConversation = (conversationId, updatedMessage) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? {
              ...conv,
              messages: conv.messages.map(msg => 
                msg.id === updatedMessage.id ? updatedMessage : msg
              )
            }
          : conv
      )
    )
  }

  const activeConversation = conversations.find(conv => conv.id === activeConversationId)

  return (
    <ToastProvider>
      <div className="flex h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white overflow-hidden">
        {/* Left Sidebar */}
        <div className={`transition-all duration-500 ${isLeftSidebarCollapsed ? 'w-16' : 'w-72'} bg-gray-900 border-r border-gray-700`}>
          <AnimatedLeftSidebar 
            conversations={conversations}
            activeConversationId={activeConversationId}
            onConversationSelect={setActiveConversationId}
            onNewChat={createNewChat}
            isCollapsed={isLeftSidebarCollapsed}
            onToggleCollapse={toggleLeftSidebar}
          />
        </div>

        {/* Main Chat Panel */}
        <div className="flex-1 flex flex-col m-2">
          <div className="bg-gradient-to-br from-white via-gray-50 to-gray-100 text-black rounded-2xl overflow-hidden shadow-2xl h-full border border-gray-200">
            <AnimatedChatPanel 
              conversation={activeConversation}
              dbConnection={dbConnection}
              onDbConnectionChange={setDbConnection}
              onUpdateTitle={updateConversationTitle}
              onAddMessage={addMessageToConversation}
              onUpdateMessage={updateMessageInConversation}
              config={chatConfig}
              onConfigChange={setChatConfig}
            />
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 bg-gray-900 border-l border-gray-700">
          <AnimatedRightSidebar 
            config={chatConfig}
            onConfigChange={setChatConfig}
            tokenUsage={globalTokenUsage}
            processingSteps={globalProcessingSteps}
            activeTools={globalActiveTools}
          />
        </div>
      </div>
    </ToastProvider>
  )
}
