'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Settings, Database, Key, User } from 'lucide-react'

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
        [field]: field === 'db_port' ? parseInt(value) || 5432 : value
      }
    }))
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
                <CardTitle>Database Connection</CardTitle>
                <CardDescription>
                  Configure your PostgreSQL database connection
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="db_host">Host</Label>
                    <Input
                      id="db_host"
                      value={localConfig.db_connection_info.db_host}
                      onChange={(e) => handleDatabaseChange('db_host', e.target.value)}
                      placeholder="localhost"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="db_port">Port</Label>
                    <Input
                      id="db_port"
                      type="number"
                      value={localConfig.db_connection_info.db_port}
                      onChange={(e) => handleDatabaseChange('db_port', e.target.value)}
                      placeholder="5432"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_name">Database Name</Label>
                  <Input
                    id="db_name"
                    value={localConfig.db_connection_info.db_name}
                    onChange={(e) => handleDatabaseChange('db_name', e.target.value)}
                    placeholder="chinook"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_user">Username</Label>
                  <Input
                    id="db_user"
                    value={localConfig.db_connection_info.db_user}
                    onChange={(e) => handleDatabaseChange('db_user', e.target.value)}
                    placeholder="postgres"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_password">Password</Label>
                  <Input
                    id="db_password"
                    type="password"
                    value={localConfig.db_connection_info.db_password}
                    onChange={(e) => handleDatabaseChange('db_password', e.target.value)}
                    placeholder="Enter database password"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_schema">Schema (Optional)</Label>
                  <Input
                    id="db_schema"
                    value={localConfig.db_connection_info.db_schema || ''}
                    onChange={(e) => handleDatabaseChange('db_schema', e.target.value || null)}
                    placeholder="Leave empty for default"
                  />
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
