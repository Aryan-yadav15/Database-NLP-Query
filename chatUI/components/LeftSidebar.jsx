'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Plus, MessageSquare, User, Zap, ChevronsLeft, ChevronsRight } from 'lucide-react'

export default function LeftSidebar({ 
  conversations = [], 
  activeConversationId, 
  onConversationSelect, 
  onNewChat,
  isCollapsed,
  onToggleCollapse
}) {
  return (
    <div className="h-full flex flex-col bg-gray-900 relative">
      {/* Header */}
      <div className={`border-b border-gray-800 ${isCollapsed ? 'p-2' : 'p-4'}`}>
        <div className={`flex items-center gap-2 mb-4 ${isCollapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          {!isCollapsed && <span className="font-semibold text-lg text-white">Lumina</span>}
        </div>
        
        <Button 
          onClick={onNewChat}
          className={`w-full bg-gray-800 hover:bg-gray-700 text-white border border-gray-700 rounded-lg flex items-center gap-2 transition-all duration-200 ${
            isCollapsed ? 'px-2 py-2 justify-center' : 'px-3 py-2 justify-start'
          }`}
          variant="outline"
        >
          <Plus className="w-4 h-4" />
          {!isCollapsed && <span>New Chat</span>}
          {!isCollapsed && <span className="ml-auto text-xs text-gray-400">⌘ N</span>}
        </Button>
      </div>

      {/* Navigation */}
      <div className={`py-2 ${isCollapsed ? 'px-2' : 'px-4'}`}>
        <div className={`space-y-1 ${isCollapsed ? 'flex flex-col items-center' : ''}`}>
          <div className={`flex items-center gap-2 p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-md cursor-pointer transition-colors ${
            isCollapsed ? 'justify-center' : ''
          }`}>
            <MessageSquare className="w-4 h-4" />
            {!isCollapsed && <span className="text-sm">Notifications</span>}
          </div>
          <div className={`flex items-center gap-2 p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-md cursor-pointer transition-colors ${
            isCollapsed ? 'justify-center' : ''
          }`}>
            <User className="w-4 h-4" />
            {!isCollapsed && <span className="text-sm">Community</span>}
          </div>
          <div className={`flex items-center gap-2 p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-md cursor-pointer transition-colors ${
            isCollapsed ? 'justify-center' : ''
          }`}>
            <MessageSquare className="w-4 h-4" />
            {!isCollapsed && <span className="text-sm">Commands</span>}
          </div>
        </div>
      </div>

      {/* Recent Conversations */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className={`py-2 ${isCollapsed ? 'px-2' : 'px-4'}`}>
          <h3 className={`text-sm text-gray-500 font-medium ${isCollapsed ? 'text-center' : ''}`}>
            {isCollapsed ? 'Recent' : 'Recent Conversations'}
          </h3>
        </div>
        
        <ScrollArea className={`flex-1 ${isCollapsed ? 'px-2' : 'px-4'}`}>
          <div className="space-y-1">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onConversationSelect(conversation.id)}
                className={`rounded-lg cursor-pointer transition-colors group ${
                  activeConversationId === conversation.id 
                    ? 'bg-gray-800 text-white' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                } ${isCollapsed ? 'p-2 flex justify-center' : 'p-3'}`}
              >
                {isCollapsed ? (
                  <MessageSquare className="w-5 h-5" />
                ) : (
                  <>
                    <div className="text-sm font-medium truncate">
                      {conversation.title}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(conversation.createdAt).toLocaleDateString()}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Bottom Section */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-800">
          <div className="bg-gray-800 rounded-lg p-3 mb-3 border border-gray-700">
            <div className="text-sm text-gray-300 mb-2">Your trial ends in 14 days</div>
            <div className="text-xs text-gray-400 mb-3">
              Enjoy working with reports, extract data, advanced search experience and much more.
            </div>
            <Button className="w-full bg-gradient-to-r from-lime-400 to-lime-500 hover:from-lime-500 hover:to-lime-600 text-black border-0 font-medium">
              ↗ Upgrade
            </Button>
          </div>
        </div>
      )}

      {/* Collapse Button */}
      <div className="absolute bottom-4 right-4">
        <Button
          onClick={onToggleCollapse}
          variant="ghost"
          size="icon"
          className="bg-gray-800 hover:bg-gray-700 text-white rounded-full h-8 w-8 border border-gray-700"
        >
          {isCollapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  )
}
