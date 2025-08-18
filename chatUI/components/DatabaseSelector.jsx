'use client'

import { useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Server, Database, HardDrive, Snowflake } from 'lucide-react'

export default function DatabaseSelector({ 
  currentDbType, 
  onDatabaseTypeChange,
  className = "" 
}) {
  const [isOpen, setIsOpen] = useState(false)

  // Database type configuration
  const databaseTypes = [
    {
      value: 'postgresql',
      label: 'PostgreSQL',
      icon: <Server className="w-4 h-4" />,
      color: 'bg-blue-100 text-blue-800',
      description: 'Enterprise-grade relational database'
    },
    {
      value: 'mysql',
      label: 'MySQL',
      icon: <Database className="w-4 h-4" />,
      color: 'bg-orange-100 text-orange-800',
      description: 'Popular open-source database'
    },
    {
      value: 'sqlite',
      label: 'SQLite',
      icon: <HardDrive className="w-4 h-4" />,
      color: 'bg-green-100 text-green-800',
      description: 'Lightweight file-based database'
    },
    {
      value: 'snowflake',
      label: 'Snowflake',
      icon: <Snowflake className="w-4 h-4" />,
      color: 'bg-cyan-100 text-cyan-800',
      description: 'Cloud data warehouse platform'
    }
  ]

  const currentDb = databaseTypes.find(db => db.value === currentDbType) || databaseTypes[0]

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Current Database Badge */}
      <Badge variant="outline" className={`${currentDb.color} border-0 px-3 py-1`}>
        <div className="flex items-center gap-2">
          {currentDb.icon}
          <span className="font-medium">{currentDb.label}</span>
        </div>
      </Badge>

      {/* Database Type Selector */}
      <Select
        value={currentDbType}
        onValueChange={onDatabaseTypeChange}
        open={isOpen}
        onOpenChange={setIsOpen}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select database">
            <div className="flex items-center gap-2">
              {currentDb.icon}
              <span>{currentDb.label}</span>
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {databaseTypes.map((db) => (
            <SelectItem key={db.value} value={db.value}>
              <div className="flex items-center gap-3 py-1">
                <div className={`p-1 rounded ${db.color}`}>
                  {db.icon}
                </div>
                <div className="flex flex-col">
                  <span className="font-medium">{db.label}</span>
                  <span className="text-xs text-gray-500">{db.description}</span>
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

// Export database type utilities for use in other components
export const getDatabaseIcon = (dbType) => {
  const iconMapping = {
    postgresql: <Server className="w-4 h-4" />,
    mysql: <Database className="w-4 h-4" />,
    sqlite: <HardDrive className="w-4 h-4" />,
    snowflake: <Snowflake className="w-4 h-4" />
  }
  return iconMapping[dbType] || <Database className="w-4 h-4" />
}

export const getDatabaseColor = (dbType) => {
  const colorMapping = {
    postgresql: 'bg-blue-100 text-blue-800',
    mysql: 'bg-orange-100 text-orange-800',
    sqlite: 'bg-green-100 text-green-800',
    snowflake: 'bg-cyan-100 text-cyan-800'
  }
  return colorMapping[dbType] || 'bg-gray-100 text-gray-800'
}
