'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Settings, Database, Key, User, Server, Cloud, HardDrive, Snowflake } from 'lucide-react'

export default function ConfigurationModal({ 
  config, 
  onConfigChange, 
  trigger 
}) {
  const [localConfig, setLocalConfig] = useState({
    user_id: "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
    api_key: "AIzaSyBja5P8lEZQ6qYs1SM2ZRXwzm9EgCsERLc",
    model_name: "gemini-2.0-flash",
    temperature: 0.2,
    db_connection_info: {
      db_type: "postgresql",        // Added database type support
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

  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    if (config) {
      setLocalConfig(prev => ({ ...prev, ...config }))
    }
  }, [config])

  const handleSave = () => {
    onConfigChange(localConfig)
    setIsOpen(false)
  }

  const handleDatabaseChange = (field, value) => {
    setLocalConfig(prev => ({
      ...prev,
      db_connection_info: {
        ...prev.db_connection_info,
        [field]: field === 'db_port' ? parseInt(value) || getDefaultPort(field === 'db_type' ? value : prev.db_connection_info.db_type) : value
      }
    }))
  }

  // Helper function to get default port based on database type
  const getDefaultPort = (dbType) => {
    const portMapping = {
      postgresql: 5432,
      mysql: 3306,
      sqlite: null, // SQLite doesn't use ports
      snowflake: 443
    }
    return portMapping[dbType] || 5432
  }

  // Helper function to get database type icon
  const getDatabaseIcon = (dbType) => {
    const iconMapping = {
      postgresql: <Server className="w-4 h-4" />,
      mysql: <Database className="w-4 h-4" />,
      sqlite: <HardDrive className="w-4 h-4" />,
      snowflake: <Snowflake className="w-4 h-4" />
    }
    return iconMapping[dbType] || <Database className="w-4 h-4" />
  }

  // Helper function to check if field is required for database type
  const isFieldRequired = (field, dbType) => {
    if (dbType === 'sqlite') {
      return field === 'db_name' // SQLite only needs file path
    }
    return ['db_host', 'db_name', 'db_user', 'db_password'].includes(field)
  }

  const handleMemoryChange = (index, value) => {
    setLocalConfig(prev => ({
      ...prev,
      short_term_memory: prev.short_term_memory.map((item, i) => 
        i === index ? value : item
      )
    }))
  }

  const addMemoryItem = () => {
    setLocalConfig(prev => ({
      ...prev,
      short_term_memory: [...prev.short_term_memory, ""]
    }))
  }

  const removeMemoryItem = (index) => {
    setLocalConfig(prev => ({
      ...prev,
      short_term_memory: prev.short_term_memory.filter((_, i) => i !== index)
    }))
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Configuration
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Chat Configuration
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="api" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="api" className="flex items-center gap-2">
              <Key className="w-4 h-4" />
              API
            </TabsTrigger>
            <TabsTrigger value="database" className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              Database
            </TabsTrigger>
            <TabsTrigger value="user" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              User
            </TabsTrigger>
            <TabsTrigger value="memory">Memory</TabsTrigger>
          </TabsList>

          <TabsContent value="api" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>API Configuration</CardTitle>
                <CardDescription>
                  Configure the LLM model and API settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="api_key">API Key</Label>
                  <Input
                    id="api_key"
                    type="password"
                    value={localConfig.api_key}
                    onChange={(e) => setLocalConfig(prev => ({ ...prev, api_key: e.target.value }))}
                    placeholder="Enter your Gemini API key"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model_name">Model Name</Label>
                  <Input
                    id="model_name"
                    value={localConfig.model_name}
                    onChange={(e) => setLocalConfig(prev => ({ ...prev, model_name: e.target.value }))}
                    placeholder="gemini-2.0-flash"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperature ({localConfig.temperature})</Label>
                  <input
                    id="temperature"
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={localConfig.temperature}
                    onChange={(e) => setLocalConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Precise (0.0)</span>
                    <span>Creative (1.0)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="database" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {getDatabaseIcon(localConfig.db_connection_info.db_type)}
                  Multi-Database Connection
                </CardTitle>
                <CardDescription>
                  Configure your database connection - supports PostgreSQL, MySQL, SQLite, and Snowflake
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                
                {/* Database Type Selector */}
                <div className="space-y-2">
                  <Label htmlFor="db_type">Database Type</Label>
                  <Select
                    value={localConfig.db_connection_info.db_type}
                    onValueChange={(value) => {
                      handleDatabaseChange('db_type', value)
                      // Auto-update port when database type changes
                      handleDatabaseChange('db_port', getDefaultPort(value))
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select database type">
                        <div className="flex items-center gap-2">
                          {getDatabaseIcon(localConfig.db_connection_info.db_type)}
                          <span className="capitalize">{localConfig.db_connection_info.db_type}</span>
                        </div>
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="postgresql">
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4" />
                          PostgreSQL
                        </div>
                      </SelectItem>
                      <SelectItem value="mysql">
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4" />
                          MySQL
                        </div>
                      </SelectItem>
                      <SelectItem value="sqlite">
                        <div className="flex items-center gap-2">
                          <HardDrive className="w-4 h-4" />
                          SQLite
                        </div>
                      </SelectItem>
                      <SelectItem value="snowflake">
                        <div className="flex items-center gap-2">
                          <Snowflake className="w-4 h-4" />
                          Snowflake
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Connection Fields - Dynamic based on database type */}
                {localConfig.db_connection_info.db_type === 'sqlite' ? (
                  // SQLite specific configuration
                  <div className="space-y-2">
                    <Label htmlFor="db_name">Database File Path</Label>
                    <Input
                      id="db_name"
                      value={localConfig.db_connection_info.db_name}
                      onChange={(e) => handleDatabaseChange('db_name', e.target.value)}
                      placeholder="/path/to/database.db"
                      className="font-mono"
                    />
                    <div className="text-xs text-gray-500">
                      Specify the full path to your SQLite database file
                    </div>
                  </div>
                ) : (
                  // Standard database configuration (PostgreSQL, MySQL, Snowflake)
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="db_host">
                          Host {isFieldRequired('db_host', localConfig.db_connection_info.db_type) && <span className="text-red-500">*</span>}
                        </Label>
                        <Input
                          id="db_host"
                          value={localConfig.db_connection_info.db_host}
                          onChange={(e) => handleDatabaseChange('db_host', e.target.value)}
                          placeholder="localhost"
                          required={isFieldRequired('db_host', localConfig.db_connection_info.db_type)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="db_port">Port</Label>
                        <Input
                          id="db_port"
                          type="number"
                          value={localConfig.db_connection_info.db_port}
                          onChange={(e) => handleDatabaseChange('db_port', e.target.value)}
                          placeholder={getDefaultPort(localConfig.db_connection_info.db_type).toString()}
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="db_name">
                        Database Name {isFieldRequired('db_name', localConfig.db_connection_info.db_type) && <span className="text-red-500">*</span>}
                      </Label>
                      <Input
                        id="db_name"
                        value={localConfig.db_connection_info.db_name}
                        onChange={(e) => handleDatabaseChange('db_name', e.target.value)}
                        placeholder={localConfig.db_connection_info.db_type === 'snowflake' ? 'database_name' : 'database_name'}
                        required={isFieldRequired('db_name', localConfig.db_connection_info.db_type)}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="db_user">
                          Username {isFieldRequired('db_user', localConfig.db_connection_info.db_type) && <span className="text-red-500">*</span>}
                        </Label>
                        <Input
                          id="db_user"
                          value={localConfig.db_connection_info.db_user}
                          onChange={(e) => handleDatabaseChange('db_user', e.target.value)}
                          placeholder="username"
                          required={isFieldRequired('db_user', localConfig.db_connection_info.db_type)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="db_password">
                          Password {isFieldRequired('db_password', localConfig.db_connection_info.db_type) && <span className="text-red-500">*</span>}
                        </Label>
                        <Input
                          id="db_password"
                          type="password"
                          value={localConfig.db_connection_info.db_password}
                          onChange={(e) => handleDatabaseChange('db_password', e.target.value)}
                          placeholder="password"
                          required={isFieldRequired('db_password', localConfig.db_connection_info.db_type)}
                        />
                      </div>
                    </div>

                    {localConfig.db_connection_info.db_type === 'snowflake' && (
                      <div className="space-y-2">
                        <Label htmlFor="db_schema">Schema (Optional)</Label>
                        <Input
                          id="db_schema"
                          value={localConfig.db_connection_info.db_schema || ''}
                          onChange={(e) => handleDatabaseChange('db_schema', e.target.value)}
                          placeholder="schema_name"
                        />
                        <div className="text-xs text-gray-500">
                          Specify a default schema for Snowflake queries
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Connection Status Indicator */}
                <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                  <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">
                    {localConfig.db_connection_info.db_type === 'sqlite' 
                      ? 'SQLite connection configured' 
                      : `${localConfig.db_connection_info.db_type.charAt(0).toUpperCase() + localConfig.db_connection_info.db_type.slice(1)} connection configured`}
                  </span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="user" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>User Settings</CardTitle>
                <CardDescription>
                  Configure user identification and preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="user_id">User ID</Label>
                  <Input
                    id="user_id"
                    value={localConfig.user_id}
                    onChange={(e) => setLocalConfig(prev => ({ ...prev, user_id: e.target.value }))}
                    placeholder="Your unique user identifier"
                  />
                  <p className="text-xs text-gray-500">
                    This is used to track your conversations and preferences
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="memory" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Short-term Memory</CardTitle>
                <CardDescription>
                  Configure context and instructions that persist across the conversation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {localConfig.short_term_memory.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={item}
                      onChange={(e) => handleMemoryChange(index, e.target.value)}
                      placeholder="Enter memory item..."
                      className="flex-1"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeMemoryItem(index)}
                      disabled={localConfig.short_term_memory.length === 1}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
                <Button variant="outline" onClick={addMemoryItem}>
                  Add Memory Item
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
