'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { 
  Pin, 
  Plus, 
  BarChart3, 
  Table, 
  PieChart, 
  TrendingUp,
  LayoutDashboard
} from 'lucide-react'
import { useToast } from '@/components/ui/toast'

/**
 * Pin to Dashboard Component
 * 
 * This component allows users to pin query results from the chat interface
 * to their analytics dashboards. It provides dashboard selection and card
 * customization options.
 */
export default function PinToDashboard({ 
  isOpen, 
  onClose, 
  queryData,
  onSuccess 
}) {
  const { addToast } = useToast()
  const [dashboards, setDashboards] = useState([])
  const [selectedDashboard, setSelectedDashboard] = useState('')
  const [cardTitle, setCardTitle] = useState('')
  const [visualizationType, setVisualizationType] = useState('table')
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)

  // Visualization type options
  const visualizationTypes = [
    { value: 'table', label: 'Table', icon: Table },
    { value: 'bar_chart', label: 'Bar Chart', icon: BarChart3 },
    { value: 'line_chart', label: 'Line Chart', icon: TrendingUp },
    { value: 'pie_chart', label: 'Pie Chart', icon: PieChart },
  ]

  useEffect(() => {
    if (isOpen) {
      fetchDashboards()
      // Auto-generate a title from the query
      if (queryData?.query_text) {
        setCardTitle(generateCardTitle(queryData.query_text))
      }
    }
  }, [isOpen, queryData])

  const fetchDashboards = async () => {
    try {
      setLoading(true)
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/analytics/dashboards')
      // const data = await response.json()
      
      // Mock data for now
      const mockDashboards = [
        {
          id: '1',
          name: 'Sales Analytics',
          description: 'Monthly sales performance and trends',
          cards_count: 5
        },
        {
          id: '2',
          name: 'Customer Insights', 
          description: 'Customer behavior and segmentation analysis',
          cards_count: 3
        }
      ]
      
      setDashboards(mockDashboards)
    } catch (err) {
      console.error('Error fetching dashboards:', err)
      addToast('Failed to load dashboards', 'error')
    } finally {
      setLoading(false)
    }
  }

  const generateCardTitle = (queryText) => {
    // Simple title generation from query text
    const words = queryText.split(' ')
    if (words.length <= 5) {
      return queryText
    }
    return words.slice(0, 5).join(' ') + '...'
  }

  const handlePin = async () => {
    if (!selectedDashboard || !cardTitle.trim()) {
      addToast('Please select a dashboard and enter a card title', 'warning')
      return
    }

    try {
      setCreating(true)
      
      const pinData = {
        dashboard_id: selectedDashboard,
        title: cardTitle.trim(),
        query_text: queryData.query_text,
        generated_sql: queryData.generated_sql,
        database_type: queryData.database_type || 'postgresql',
        visualization_type: visualizationType,
        position: { x: 0, y: 0, w: 6, h: 4 } // Default position
      }

      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/analytics/cards/pin-query', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(pinData)
      // })
      // const card = await response.json()

      // Mock success for now
      console.log('Pinning data:', pinData)
      
      addToast('Query pinned to dashboard successfully!', 'success')
      onSuccess?.()
      onClose()
      
      // Reset form
      setSelectedDashboard('')
      setCardTitle('')
      setVisualizationType('table')
      
    } catch (err) {
      console.error('Error pinning to dashboard:', err)
      addToast('Failed to pin query to dashboard', 'error')
    } finally {
      setCreating(false)
    }
  }

  const handleCreateNewDashboard = () => {
    // TODO: Open create dashboard modal
    console.log('Create new dashboard')
    addToast('Dashboard creation will be available soon', 'info')
  }

  if (!queryData) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Pin className="w-5 h-5 text-blue-600" />
            Pin to Dashboard
          </DialogTitle>
          <DialogDescription>
            Save this query result as a card in your analytics dashboard
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Query Preview */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <Label className="text-sm font-medium text-gray-700">Query</Label>
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
              {queryData.query_text}
            </p>
          </div>

          {/* Dashboard Selection */}
          <div className="space-y-2">
            <Label htmlFor="dashboard">Select Dashboard</Label>
            {loading ? (
              <div className="h-10 bg-gray-100 animate-pulse rounded-md"></div>
            ) : (
              <div className="flex gap-2">
                <Select
                  value={selectedDashboard}
                  onValueChange={setSelectedDashboard}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Choose a dashboard" />
                  </SelectTrigger>
                  <SelectContent>
                    {dashboards.map((dashboard) => (
                      <SelectItem key={dashboard.id} value={dashboard.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>{dashboard.name}</span>
                          <Badge variant="secondary" className="ml-2 text-xs">
                            {dashboard.cards_count} cards
                          </Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={handleCreateNewDashboard}
                  title="Create new dashboard"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Card Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Card Title</Label>
            <Input
              id="title"
              value={cardTitle}
              onChange={(e) => setCardTitle(e.target.value)}
              placeholder="Enter a descriptive title for this card"
            />
          </div>

          {/* Visualization Type */}
          <div className="space-y-2">
            <Label>Visualization Type</Label>
            <div className="grid grid-cols-2 gap-2">
              {visualizationTypes.map((type) => {
                const Icon = type.icon
                return (
                  <Button
                    key={type.value}
                    type="button"
                    variant={visualizationType === type.value ? "default" : "outline"}
                    className="flex items-center gap-2 h-auto p-3"
                    onClick={() => setVisualizationType(type.value)}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm">{type.label}</span>
                  </Button>
                )
              })}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handlePin} 
            disabled={!selectedDashboard || !cardTitle.trim() || creating}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {creating ? (
              <>
                <div className="animate-spin w-4 h-4 border-b-2 border-white mr-2"></div>
                Pinning...
              </>
            ) : (
              <>
                <Pin className="w-4 h-4 mr-2" />
                Pin to Dashboard
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Pin Button Component
 * 
 * A simple button that can be added to query results to trigger the pin modal.
 */
export function PinButton({ queryData, className = '' }) {
  const [showModal, setShowModal] = useState(false)

  const handlePin = () => {
    setShowModal(true)
  }

  const handleSuccess = () => {
    // Optional: Add any additional success handling
    console.log('Query pinned successfully')
  }

  return (
    <>
      <Button
        onClick={handlePin}
        variant="outline"
        size="sm"
        className={`hover:bg-blue-50 hover:border-blue-300 ${className}`}
      >
        <Pin className="w-4 h-4 mr-1" />
        Pin to Dashboard
      </Button>

      <PinToDashboard
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        queryData={queryData}
        onSuccess={handleSuccess}
      />
    </>
  )
}
