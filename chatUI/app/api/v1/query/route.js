import { NextResponse } from 'next/server'

export async function POST(request) {
  try {
    const body = await request.json()
    
    // Transform the frontend payload to match the exact backend expected format
    const backendPayload = {
      query_text: body.query,
      user_id: body.user_id || process.env.DEFAULT_USER_ID || "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
      conversation_id: body.conversation_id || "cebf932f-addb-48de-91c3-d7d462aa84b8",
      message_id: body.message_id || `msg-${Date.now()}`,
      chat_history: body.chat_history || [],
      short_term_memory: body.short_term_memory || [
        "SUMMARY: The table names are case sensitive, use double quotes while generating commands"
      ],
      model_name: body.model_name || "gemini-2.0-flash",
      temperature: body.temperature || 0.2,
      api_key: body.api_key || process.env.GEMINI_API_KEY || "AIzaSyBja5P8lEZQ6qYs1SM2ZRXwzm9EgCsERLc",
      db_connection_info: body.db_connection_info || body.db_connection || {
        db_type: body.db_type || "postgresql", // NEW: Multi-database support - defaults to PostgreSQL for backward compatibility
        db_host: process.env.DEFAULT_DB_HOST || "localhost",
        db_port: parseInt(process.env.DEFAULT_DB_PORT) || 5432,
        db_user: process.env.DEFAULT_DB_USER || "postgres",
        db_name: process.env.DEFAULT_DB_NAME || "chinook",
        db_password: process.env.DEFAULT_DB_PASSWORD || "iamaryan15",
        db_schema: null
      }
    }
    
    console.log('Forwarding payload to backend:', JSON.stringify(backendPayload, null, 2))
    
    // Forward the request to your FastAPI backend streaming endpoint
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/v1/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(backendPayload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error:', errorText)
      return NextResponse.json(
        { error: `Backend request failed: ${errorText}` },
        { status: response.status }
      )
    }

    // Return the streaming response
    return new NextResponse(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type, Accept',
      },
    })
  } catch (error) {
    console.error('API route error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Accept',
    },
  })
}
