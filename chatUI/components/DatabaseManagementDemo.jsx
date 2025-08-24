'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import DatabaseConnectionManager from '@/components/DatabaseConnectionManager'
import DatabaseSelector from '@/components/DatabaseSelector'
import { Database, Settings, TestTube } from 'lucide-react'

export default function DatabaseManagementDemo() {
  const [showConnectionManager, setShowConnectionManager] = useState(false)
  const [currentDbType, setCurrentDbType] = useState('postgresql')
  const [activeConnection, setActiveConnection] = useState(null)
  
  // Mock saved connections for demo
  const [savedConnections] = useState([
    {
      id: 'pg_1',
      name: 'Production PostgreSQL',
      type: 'postgresql',
      host: 'prod-db.company.com',
      port: 5432,
      username: 'readonly_user',
      database: 'analytics_db',
      schema: 'public',
      isActive: true,
      created_at: new Date('2025-08-15'),
      last_used: new Date('2025-08-18')
    },
    {
      id: 'mysql_1',
      name: 'E-commerce MySQL',
      type: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'ecommerce_user',
      database: 'shopify_data',
      isActive: false,
      created_at: new Date('2025-08-10'),
      last_used: new Date('2025-08-17')
    },
    {
      id: 'sqlite_1',
      name: 'Local Development DB',
      type: 'sqlite',
      database: '/Users/dev/projects/data/dev.sqlite3',
      isActive: false,
      created_at: new Date('2025-08-08')
    }
  ])

  const handleConnectionSaved = (connection) => {
    setActiveConnection(connection)
    console.log('Connection saved:', connection)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold flex items-center justify-center gap-3">
            <Database className="w-10 h-10 text-blue-400" />
            Database Connection Management
          </h1>
          <p className="text-gray-400 text-lg">
            Comprehensive database connectivity for AI-powered data analysis
          </p>
        </div>

        {/* Current Status */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Current Database Configuration
            </CardTitle>
            <CardDescription className="text-gray-400">
              Active database connection and type selection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Database Type Selector */}
            <div>
              <label className="block text-sm font-medium mb-2">Database Type</label>
              <DatabaseSelector
                currentDbType={currentDbType}
                onDatabaseTypeChange={setCurrentDbType}
              />
            </div>

            {/* Active Connection Status */}
            <div>
              <label className="block text-sm font-medium mb-2">Active Connection</label>
              {activeConnection ? (
                <div className="p-4 bg-green-900/20 border border-green-800 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-green-300">{activeConnection.name}</h4>
                      <p className="text-sm text-green-400">
                        {activeConnection.type.toUpperCase()} • {activeConnection.host || activeConnection.database}
                      </p>
                    </div>
                    <div className="text-green-300">
                      <Database className="w-6 h-6" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-amber-900/20 border border-amber-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <TestTube className="w-5 h-5 text-amber-400" />
                    <span className="text-amber-300">No active connection</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Management Actions */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle>Connection Management</CardTitle>
            <CardDescription className="text-gray-400">
              Manage your database connections for AI analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={() => setShowConnectionManager(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white p-6 h-auto flex-col gap-2"
              >
                <Database className="w-8 h-8" />
                <span className="text-lg font-medium">Manage Connections</span>
                <span className="text-sm opacity-80">Add, edit, test, and activate connections</span>
              </Button>

              <Button
                variant="outline"
                className="bg-gray-700 border-gray-600 hover:bg-gray-600 text-white p-6 h-auto flex-col gap-2"
                disabled={!activeConnection}
              >
                <TestTube className="w-8 h-8" />
                <span className="text-lg font-medium">Test Connection</span>
                <span className="text-sm opacity-80">Verify current connection status</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Feature Highlights */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle>Key Features</CardTitle>
            <CardDescription className="text-gray-400">
              What you can do with our database connection system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-blue-300">Multi-Database Support</h4>
                <p className="text-sm text-gray-400">
                  Connect to PostgreSQL, MySQL, SQLite, and Snowflake databases with native optimizations.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-green-300">Connection Testing</h4>
                <p className="text-sm text-gray-400">
                  Test connections before saving with detailed feedback and connection diagnostics.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-purple-300">Smart Management</h4>
                <p className="text-sm text-gray-400">
                  Save multiple connections, switch between environments, and track usage history.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-orange-300">Security First</h4>
                <p className="text-sm text-gray-400">
                  Encrypted password storage, secure connection handling, and audit logging.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-cyan-300">AI Integration</h4>
                <p className="text-sm text-gray-400">
                  Seamless integration with AI analysis tools for instant data insights.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-pink-300">Real-time Updates</h4>
                <p className="text-sm text-gray-400">
                  Live connection status, automatic reconnection, and performance monitoring.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Connection Troubleshooting */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle>Common Issues & Solutions</CardTitle>
            <CardDescription className="text-gray-400">
              Quick fixes for common database connection problems
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-medium">Connection Timeout</h4>
                <p className="text-sm text-gray-400">
                  Check firewall settings, verify host and port, ensure database server is running.
                </p>
              </div>
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-medium">Authentication Failed</h4>
                <p className="text-sm text-gray-400">
                  Verify username and password, check user permissions, confirm database name.
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-medium">Schema Access Denied</h4>
                <p className="text-sm text-gray-400">
                  Ensure user has SELECT permissions on system tables for schema introspection.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Database Connection Manager Modal */}
      <DatabaseConnectionManager
        isOpen={showConnectionManager}
        onClose={() => setShowConnectionManager(false)}
        onConnectionSaved={handleConnectionSaved}
        currentDbType={currentDbType}
        savedConnections={savedConnections}
      />
    </div>
  )
}
