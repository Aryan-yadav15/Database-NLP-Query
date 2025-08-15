'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Paperclip, Send } from 'lucide-react'
import DBConnectionModal from '@/components/DBConnectionModal'

export default function ChatInput({ 
  onSendMessage, 
  isLoading, 
  dbConnection, 
  onDbConnectionChange 
}) {
  const [message, setMessage] = useState('')
  const [showDBModal, setShowDBModal] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center gap-3 p-4 bg-gray-100 rounded-2xl border border-gray-200 focus-within:border-gray-400 transition-colors">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setShowDBModal(true)}
            className="text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-xl"
          >
            <Paperclip className="w-5 h-5" />
          </Button>
          
          <div className="flex-1">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question or make a request..."
              className="bg-transparent border-0 text-gray-900 placeholder-gray-500 focus-visible:ring-0 focus-visible:ring-offset-0 text-lg"
              disabled={isLoading}
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">⌘</span>
            <Button
              type="submit"
              size="icon"
              disabled={!message.trim() || isLoading}
              className="bg-gray-800 hover:bg-gray-900 text-white rounded-xl"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </form>

      {/* Database Connection Status */}
      {dbConnection && (
        <div className="text-xs text-gray-500 px-2">
          Connected to: {dbConnection.db_name} ({dbConnection.db_host}:{dbConnection.db_port})
        </div>
      )}

      {!dbConnection && (
        <div className="text-xs text-amber-600 px-2">
          ⚠️ No database connection. Click the attachment button to connect.
        </div>
      )}

      <DBConnectionModal
        isOpen={showDBModal}
        onClose={() => setShowDBModal(false)}
        onSave={onDbConnectionChange}
        currentConnection={dbConnection}
      />
    </div>
  )
}
