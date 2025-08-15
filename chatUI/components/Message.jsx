'use client'

import DataTable from '@/components/DataTable'
import { Bot, User, Copy, Code } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

export default function Message({ message }) {
  const [showSQL, setShowSQL] = useState(false)

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}
      
      <div className={`max-w-3xl ${isUser ? 'order-first' : ''}`}>
        <div className={`p-4 rounded-2xl ${
          isUser 
            ? 'bg-gray-800 text-white ml-auto' 
            : 'bg-gray-100 text-gray-900 border border-gray-200'
        }`}>
          {/* Status indicator for loading messages */}
          {message.status && (
            <div className="text-gray-500 text-sm mb-2 italic">
              {message.status}
            </div>
          )}
          
          {/* Message content */}
          {message.content && (
            <div className="prose prose-gray max-w-none">
              <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
            </div>
          )}

          {/* Error state */}
          {message.isError && (
            <div className="text-red-600 text-sm">
              ⚠️ Error processing request
            </div>
          )}

          {/* SQL Query */}
          {message.sql && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSQL(!showSQL)}
                  className="text-gray-600 hover:text-gray-800 p-0 h-auto"
                >
                  <Code className="w-4 h-4 mr-2" />
                  {showSQL ? 'Hide' : 'Show'} SQL Query
                </Button>
                {showSQL && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(message.sql)}
                    className="text-gray-600 hover:text-gray-800 p-1 h-auto"
                  >
                    <Copy className="w-3 h-3" />
                  </Button>
                )}
              </div>
              
              {showSQL && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 font-mono text-sm overflow-x-auto">
                  <pre className="text-gray-800">{message.sql}</pre>
                </div>
              )}
            </div>
          )}

          {/* Data Table */}
          {message.table && (
            <div className="mt-4">
              <DataTable data={message.table} />
            </div>
          )}
        </div>
        
        {/* Timestamp */}
        <div className="text-xs text-gray-500 mt-2 px-4">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  )
}
