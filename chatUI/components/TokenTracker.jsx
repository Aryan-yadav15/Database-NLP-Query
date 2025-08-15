'use client'

import { Activity, Zap } from 'lucide-react'

export default function TokenTracker({ tokenUsage }) {
  if (!tokenUsage) return null

  const {
    prompt_token_count = 0,
    candidates_token_count = 0,
    total_token_count = 0,
    llm_calls_count = 0
  } = tokenUsage

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-3">
      <div className="flex items-center gap-4 text-sm text-gray-700">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-500" />
          <span className="text-xs text-gray-500">Token Usage:</span>
        </div>
        
        <div className="flex items-center gap-4">
          <span>
            <span className="text-gray-500">Prompt:</span>{' '}
            <span className="text-gray-900 font-medium">{prompt_token_count.toLocaleString()}</span>
          </span>
          
          <span className="text-gray-300">|</span>
          
          <span>
            <span className="text-gray-500">Completion:</span>{' '}
            <span className="text-gray-900 font-medium">{candidates_token_count.toLocaleString()}</span>
          </span>
          
          <span className="text-gray-300">|</span>
          
          <span>
            <span className="text-gray-500">Total:</span>{' '}
            <span className="text-blue-600 font-medium">{total_token_count.toLocaleString()}</span>
          </span>
          
          <span className="text-gray-300">|</span>
          
          <div className="flex items-center gap-1">
            <Activity className="w-3 h-3 text-green-500" />
            <span>
              <span className="text-gray-500">LLM Calls:</span>{' '}
              <span className="text-green-600 font-medium">{llm_calls_count}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
