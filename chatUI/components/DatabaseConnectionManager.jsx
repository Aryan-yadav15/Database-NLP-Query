'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  Server, 
  Database, 
  HardDrive, 
  Snowflake, 
  TestTube, 
  Save, 
  Trash2,
  Plus,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react'
import { useToast } from '@/components/ui/toast'

export default function DatabaseConnectionManager({ 
  isOpen, 
  onClose, 
  onConnectionSaved,
  currentDbType,
  savedConnections = []
}) {
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState('existing')
  const [selectedConnection, setSelectedConnection] = useState(null)
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [testResult, setTestResult] = useState(null)
  
  // Form state for new connections
  const [newConnection, setNewConnection] = useState({
    name: '',
    type: currentDbType || 'postgresql',
    host: 'localhost',
    port: '',
    username: '',
    password: '',
    database: '',
    schema: ''
  })

  // Database type configurations
  const databaseConfigs = {
    postgresql: {
      label: 'PostgreSQL',
      icon: <Server className="w-4 h-4" />,
      color: 'bg-blue-100 text-blue-800',
      defaultPort: 5432,
      fields: ['host', 'port', 'username', 'password', 'database', 'schema'],
      requiredFields: ['host', 'port', 'username', 'password', 'database']
    },
    mysql: {
      label: 'MySQL',
      icon: <Database className="w-4 h-4" />,
      color: 'bg-orange-100 text-orange-800',
      defaultPort: 3306,
      fields: ['host', 'port', 'username', 'password', 'database'],
      requiredFields: ['host', 'port', 'username', 'password', 'database']
    },
    sqlite: {
      label: 'SQLite',
      icon: <HardDrive className="w-4 h-4" />,
      color: 'bg-green-100 text-green-800',
      defaultPort: null,
      fields: ['database'],
      requiredFields: ['database'],
      description: 'File path to SQLite database'
    },
    snowflake: {
      label: 'Snowflake',
      icon: <Snowflake className="w-4 h-4" />,
      color: 'bg-cyan-100 text-cyan-800',
      defaultPort: 443,
      fields: ['account', 'username', 'password', 'database', 'schema', 'warehouse'],
      requiredFields: ['account', 'username', 'password', 'database']
    }
  }

  // Update default port when database type changes
  useEffect(() => {
    const config = databaseConfigs[newConnection.type]
    if (config?.defaultPort) {
      setNewConnection(prev => ({ ...prev, port: config.defaultPort.toString() }))
    }
  }, [newConnection.type])

  // Handle form input changes
  const handleInputChange = (field, value) => {
    setNewConnection(prev => ({ ...prev, [field]: value }))
    setTestResult(null) // Clear test result when form changes
  }

  // Test database connection
  const testConnection = async () => {
    setIsTestingConnection(true)
    setTestResult(null)

    try {
      const response = await fetch('/api/database/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConnection)
      })

      const result = await response.json()
      
      if (response.ok) {
        setTestResult({ success: true, message: result.message })
        addToast("Database connection test passed!", "success")
      } else {
        setTestResult({ success: false, message: result.error })
        addToast(result.error, "error")
      }
    } catch (error) {
      setTestResult({ success: false, message: "Network error occurred" })
      addToast("Could not test connection", "error")
    } finally {
      setIsTestingConnection(false)
    }
  }

  // Save new connection
  const saveConnection = async () => {
    try {
      const response = await fetch('/api/database/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConnection)
      })

      if (response.ok) {
        const savedConnection = await response.json()
        onConnectionSaved?.(savedConnection)
        addToast(`${newConnection.name} connection saved successfully!`, "success")
        onClose()
      } else {
        const error = await response.json()
        addToast(error.message, "error")
      }
    } catch (error) {
      addToast("Could not save connection", "error")
    }
  }

  // Delete connection
  const deleteConnection = async (connectionId) => {
    try {
      const response = await fetch(`/api/database/connections/${connectionId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        addToast("Database connection removed successfully", "success")
        // Refresh connections list
      }
    } catch (error) {
      addToast("Could not delete connection", "error")
    }
  }

  // Select existing connection
  const selectConnection = (connection) => {
    onConnectionSaved?.(connection)
    onClose()
  }

  const currentConfig = databaseConfigs[newConnection.type]
  const isFormValid = currentConfig?.requiredFields.every(field => newConnection[field])

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-gray-900 text-white border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Database Connection Manager
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Manage your database connections for AI-powered data analysis
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-gray-800">
            <TabsTrigger value="existing" className="data-[state=active]:bg-gray-700">
              Existing Connections
            </TabsTrigger>
            <TabsTrigger value="new" className="data-[state=active]:bg-gray-700">
              New Connection
            </TabsTrigger>
          </TabsList>

          {/* Existing Connections Tab */}
          <TabsContent value="existing" className="space-y-4">
            {savedConnections.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No saved connections</p>
                <Button 
                  variant="outline" 
                  onClick={() => setActiveTab('new')}
                  className="mt-4 bg-gray-800 border-gray-600 hover:bg-gray-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Connection
                </Button>
              </div>
            ) : (
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {savedConnections.map((connection) => {
                  const config = databaseConfigs[connection.type]
                  return (
                    <div 
                      key={connection.id}
                      className="flex items-center justify-between p-4 bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded ${config.color}`}>
                          {config.icon}
                        </div>
                        <div>
                          <h4 className="font-medium">{connection.name}</h4>
                          <p className="text-sm text-gray-400">
                            {config.label} • {connection.host || connection.database}
                          </p>
                        </div>
                        {connection.isActive && (
                          <Badge className="bg-green-600 text-white">Active</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          onClick={() => selectConnection(connection)}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          Connect
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteConnection(connection.id)}
                          className="border-gray-600 hover:bg-red-600 hover:border-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </TabsContent>

          {/* New Connection Tab */}
          <TabsContent value="new" className="space-y-4">
            <div className="space-y-4">
              {/* Connection Name */}
              <div className="space-y-2">
                <Label htmlFor="name">Connection Name</Label>
                <Input
                  id="name"
                  value={newConnection.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="My Database"
                  className="bg-gray-800 border-gray-600 text-white"
                />
              </div>

              {/* Database Type */}
              <div className="space-y-2">
                <Label>Database Type</Label>
                <Select 
                  value={newConnection.type} 
                  onValueChange={(value) => handleInputChange('type', value)}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-600">
                    {Object.entries(databaseConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        <div className="flex items-center gap-2">
                          {config.icon}
                          <span>{config.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Dynamic Fields Based on Database Type */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {currentConfig?.fields.includes('host') && (
                  <div className="space-y-2">
                    <Label htmlFor="host">Host</Label>
                    <Input
                      id="host"
                      value={newConnection.host}
                      onChange={(e) => handleInputChange('host', e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white"
                      required={currentConfig.requiredFields.includes('host')}
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('port') && (
                  <div className="space-y-2">
                    <Label htmlFor="port">Port</Label>
                    <Input
                      id="port"
                      type="number"
                      value={newConnection.port}
                      onChange={(e) => handleInputChange('port', e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white"
                      required={currentConfig.requiredFields.includes('port')}
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('account') && (
                  <div className="space-y-2">
                    <Label htmlFor="account">Account</Label>
                    <Input
                      id="account"
                      value={newConnection.account || ''}
                      onChange={(e) => handleInputChange('account', e.target.value)}
                      placeholder="your-account.snowflakecomputing.com"
                      className="bg-gray-800 border-gray-600 text-white"
                      required={currentConfig.requiredFields.includes('account')}
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('username') && (
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      value={newConnection.username}
                      onChange={(e) => handleInputChange('username', e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white"
                      required={currentConfig.requiredFields.includes('username')}
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('password') && (
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={newConnection.password}
                      onChange={(e) => handleInputChange('password', e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white"
                      required={currentConfig.requiredFields.includes('password')}
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('database') && (
                  <div className="space-y-2">
                    <Label htmlFor="database">
                      {newConnection.type === 'sqlite' ? 'Database File Path' : 'Database Name'}
                    </Label>
                    <Input
                      id="database"
                      value={newConnection.database}
                      onChange={(e) => handleInputChange('database', e.target.value)}
                      placeholder={newConnection.type === 'sqlite' ? '/path/to/database.db' : 'database_name'}
                      className="bg-gray-800 border-gray-600 text-white"
                      required={currentConfig.requiredFields.includes('database')}
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('schema') && (
                  <div className="space-y-2">
                    <Label htmlFor="schema">Schema (Optional)</Label>
                    <Input
                      id="schema"
                      value={newConnection.schema}
                      onChange={(e) => handleInputChange('schema', e.target.value)}
                      placeholder="public"
                      className="bg-gray-800 border-gray-600 text-white"
                    />
                  </div>
                )}

                {currentConfig?.fields.includes('warehouse') && (
                  <div className="space-y-2">
                    <Label htmlFor="warehouse">Warehouse</Label>
                    <Input
                      id="warehouse"
                      value={newConnection.warehouse || ''}
                      onChange={(e) => handleInputChange('warehouse', e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white"
                    />
                  </div>
                )}
              </div>

              {/* Test Connection Result */}
              {testResult && (
                <div className={`flex items-center gap-2 p-3 rounded-lg ${
                  testResult.success 
                    ? 'bg-green-900/20 border border-green-800 text-green-300'
                    : 'bg-red-900/20 border border-red-800 text-red-300'
                }`}>
                  {testResult.success ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    <XCircle className="w-5 h-5" />
                  )}
                  <span className="text-sm">{testResult.message}</span>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex justify-between">
          <Button 
            variant="outline" 
            onClick={onClose}
            className="bg-gray-800 border-gray-600 hover:bg-gray-700"
          >
            Cancel
          </Button>
          
          {activeTab === 'new' && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={testConnection}
                disabled={!isFormValid || isTestingConnection}
                className="bg-gray-800 border-gray-600 hover:bg-gray-700"
              >
                {isTestingConnection ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <TestTube className="w-4 h-4 mr-2" />
                )}
                Test Connection
              </Button>
              <Button
                onClick={saveConnection}
                disabled={!isFormValid || !testResult?.success}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Connection
              </Button>
            </div>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
