'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  LayoutDashboard, 
  Plus, 
  RefreshCw, 
  Settings, 
  Share, 
  BarChart3,
  Table,
  PieChart,
  TrendingUp,
  Calendar,
  Users
} from 'lucide-react'

/**
 * Dashboard List Component
 * 
 * Displays a list of user's dashboards with creation and management options.
 * This is the main landing page for the analytics feature.
 */
function DashboardList({ onSelectDashboard, onCreateDashboard, apiBaseUrl }) {
  const [dashboards, setDashboards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboards()
  }, [])

  const fetchDashboards = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`${apiBaseUrl}/analytics/dashboards/`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Handle paginated response
      const dashboardList = data.dashboards || data
      
      // Transform data to match our component expectations
      const transformedDashboards = dashboardList.map(dashboard => ({
        id: dashboard.id,
        name: dashboard.name,
        description: dashboard.description,
        created_at: dashboard.created_at,
        updated_at: dashboard.updated_at,
        cards_count: dashboard.cards_count || 0,
        layout_config: dashboard.layout_config,
        sharing_config: dashboard.sharing_config
      }))
      
      setDashboards(transformedDashboards)
    } catch (err) {
      setError('Failed to load dashboards. Make sure the backend server is running.')
      console.error('Error fetching dashboards:', err)
      
      // Fallback to mock data for development
      const mockDashboards = [
        {
          id: 'mock-1',
          name: 'Sales Analytics (Demo)',
          description: 'Monthly sales performance and trends - Demo data',
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-18T15:30:00Z',
          cards_count: 5
        },
        {
          id: 'mock-2', 
          name: 'Customer Insights (Demo)',
          description: 'Customer behavior and segmentation analysis - Demo data',
          created_at: '2025-01-10T09:00:00Z',
          updated_at: '2025-01-17T11:20:00Z',
          cards_count: 3
        }
      ]
      setDashboards(mockDashboards)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboards...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={fetchDashboards} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboards</h1>
          <p className="text-gray-600">Create and manage your data insights</p>
        </div>
        <Button onClick={onCreateDashboard} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          New Dashboard
        </Button>
      </div>

      {/* Dashboard Grid */}
      {dashboards.length === 0 ? (
        <div className="text-center py-12">
          <LayoutDashboard className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No dashboards yet</h3>
          <p className="text-gray-600 mb-6">Get started by creating your first analytics dashboard</p>
          <Button onClick={onCreateDashboard} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Create Dashboard
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dashboards.map((dashboard) => (
            <Card 
              key={dashboard.id} 
              className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
              onClick={() => onSelectDashboard(dashboard)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{dashboard.name}</CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    {dashboard.cards_count} cards
                  </Badge>
                </div>
                <CardDescription className="line-clamp-2">
                  {dashboard.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center text-sm text-gray-500">
                  <span>Updated {new Date(dashboard.updated_at).toLocaleDateString()}</span>
                  <div className="flex space-x-2">
                    <Button size="sm" variant="ghost" onClick={(e) => {
                      e.stopPropagation()
                      // TODO: Implement sharing
                    }}>
                      <Share className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={(e) => {
                      e.stopPropagation()
                      // TODO: Implement settings
                    }}>
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Create Dashboard Modal
 * 
 * Simple form for creating a new dashboard with real API integration.
 */
function CreateDashboardModal({ isOpen, onClose, onSave, apiBaseUrl }) {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.name.trim()) return

    setSaving(true)
    setError(null)
    
    try {
      const dashboardPayload = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        layout: {
          columns: 12,
          rows: 6,
          widgets: []
        },
        filters: {},
        is_public: false
      }

      const response = await fetch(`${apiBaseUrl}/analytics/dashboards/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dashboardPayload)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }
      
      const dashboard = await response.json()
      
      console.log('✅ Dashboard created successfully:', dashboard)
      
      onSave(dashboard)
      setFormData({ name: '', description: '' })
      
    } catch (err) {
      console.error('Error creating dashboard:', err)
      setError(err.message || 'Failed to create dashboard')
      
      // Fallback to mock success for development
      const mockDashboard = {
        id: `mock-${Date.now()}`,
        ...formData,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        cards_count: 0
      }
      
      console.log('📝 Using mock dashboard due to API error')
      onSave(mockDashboard)
      setFormData({ name: '', description: '' })
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create New Dashboard</CardTitle>
          <CardDescription>
            Create a new analytics dashboard to organize your insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}
            <div>
              <Label htmlFor="name">Dashboard Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g., Sales Analytics"
                required
              />
            </div>
            <div>
              <Label htmlFor="description">Description (optional)</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Brief description of this dashboard"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving || !formData.name.trim()}>
                {saving ? 'Creating...' : 'Create Dashboard'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Dashboard Analytics Component
 * 
 * Main component that provides dashboard management functionality.
 * This serves as the entry point for the analytics feature and integrates with the backend API.
 */
export default function DashboardAnalytics({ dbConnection, config }) {
  const [selectedDashboard, setSelectedDashboard] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [apiBaseUrl] = useState('http://localhost:8000/api/v1') // Backend API URL

  const handleSelectDashboard = (dashboard) => {
    setSelectedDashboard(dashboard)
    // TODO: Navigate to dashboard view or show dashboard content
    console.log('Selected dashboard:', dashboard)
  }

  const handleCreateDashboard = () => {
    setShowCreateModal(true)
  }

  const handleSaveDashboard = (dashboard) => {
    setShowCreateModal(false)
    console.log('Created dashboard:', dashboard)
    // TODO: Refresh dashboard list or navigate to new dashboard
  }

  const handleCloseModal = () => {
    setShowCreateModal(false)
  }

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      <div className="container mx-auto px-6 py-6">
        <DashboardList
          onSelectDashboard={handleSelectDashboard}
          onCreateDashboard={handleCreateDashboard}
          apiBaseUrl={apiBaseUrl}
        />
        
        <CreateDashboardModal
          isOpen={showCreateModal}
          onClose={handleCloseModal}
          onSave={handleSaveDashboard}
          apiBaseUrl={apiBaseUrl}
        />
      </div>
    </div>
  )
}
