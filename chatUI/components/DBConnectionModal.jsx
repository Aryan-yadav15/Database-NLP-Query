'use client'

import { useState } from 'react'
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

export default function DBConnectionModal({ 
  isOpen, 
  onClose, 
  onSave, 
  currentConnection 
}) {
  const [formData, setFormData] = useState({
    db_host: currentConnection?.db_host || 'localhost',
    db_port: currentConnection?.db_port || 5432,
    db_user: currentConnection?.db_user || 'postgres',
    db_password: currentConnection?.db_password || '',
    db_name: currentConnection?.db_name || '',
    db_schema: currentConnection?.db_schema || null
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave({
      ...formData,
      db_port: parseInt(formData.db_port)
    })
    onClose()
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-gray-800 text-white border-gray-700">
        <DialogHeader>
          <DialogTitle>Database Connection</DialogTitle>
          <DialogDescription className="text-gray-400">
            Connect to your PostgreSQL database to enable data queries.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="host">Host</Label>
              <Input
                id="host"
                value={formData.db_host}
                onChange={(e) => handleChange('db_host', e.target.value)}
                className="bg-gray-700 border-gray-600 text-white"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port">Port</Label>
              <Input
                id="port"
                type="number"
                value={formData.db_port}
                onChange={(e) => handleChange('db_port', e.target.value)}
                className="bg-gray-700 border-gray-600 text-white"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={formData.db_user}
              onChange={(e) => handleChange('db_user', e.target.value)}
              className="bg-gray-700 border-gray-600 text-white"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={formData.db_password}
              onChange={(e) => handleChange('db_password', e.target.value)}
              className="bg-gray-700 border-gray-600 text-white"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="database">Database Name</Label>
            <Input
              id="database"
              value={formData.db_name}
              onChange={(e) => handleChange('db_name', e.target.value)}
              className="bg-gray-700 border-gray-600 text-white"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="schema">Schema (Optional)</Label>
            <Input
              id="schema"
              value={formData.db_schema || ''}
              onChange={(e) => handleChange('db_schema', e.target.value || null)}
              className="bg-gray-700 border-gray-600 text-white"
              placeholder="public"
            />
          </div>

          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={onClose}
              className="bg-gray-700 border-gray-600 text-white hover:bg-gray-600"
            >
              Cancel
            </Button>
            <Button 
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Connect
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
