"""Analytics Dashboard Schema Migration

This migration creates the database tables needed for the analytics dashboard feature:
- dashboards: Main dashboard configuration and metadata
- insight_cards: Individual cards pinned to dashboards  
- dashboard_comments: Collaboration comments on cards
- dashboard_shares: Dashboard sharing permissions

Revision ID: analytics_dashboard_v1
Created: 2025-01-18
"""

# Database migration for analytics dashboard tables
ANALYTICS_SCHEMA_SQL = """
-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dashboards table
CREATE TABLE IF NOT EXISTS dashboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Will reference users table when implemented
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout_config JSONB DEFAULT '{"breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0}, "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2}}',
    sharing_config JSONB DEFAULT '{"public": false, "permissions": []}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insight cards table
CREATE TABLE IF NOT EXISTS insight_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    database_type VARCHAR(50) NOT NULL DEFAULT 'postgresql',
    database_config JSONB,
    visualization_type VARCHAR(50) DEFAULT 'table',
    visualization_config JSONB DEFAULT '{}',
    position_config JSONB DEFAULT '{"x": 0, "y": 0, "w": 6, "h": 4}',
    refresh_frequency VARCHAR(50) DEFAULT 'manual',
    auto_refresh_enabled BOOLEAN DEFAULT false,
    last_refreshed TIMESTAMP WITH TIME ZONE,
    last_result JSONB,
    error_message TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dashboard comments table
CREATE TABLE IF NOT EXISTS dashboard_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID REFERENCES insight_cards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- Will reference users table when implemented
    comment_text TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dashboard sharing table
CREATE TABLE IF NOT EXISTS dashboard_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    shared_with_user_id UUID, -- NULL for public links
    permission_level VARCHAR(20) DEFAULT 'view', -- 'view', 'edit', 'admin'
    access_token VARCHAR(255) UNIQUE, -- For public sharing links
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_dashboards_user_id ON dashboards(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboards_created_at ON dashboards(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_insight_cards_dashboard_id ON insight_cards(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_insight_cards_last_refreshed ON insight_cards(last_refreshed DESC);
CREATE INDEX IF NOT EXISTS idx_dashboard_comments_card_id ON dashboard_comments(card_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_shares_dashboard_id ON dashboard_shares(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_shares_access_token ON dashboard_shares(access_token);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_dashboards_updated_at 
    BEFORE UPDATE ON dashboards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_insight_cards_updated_at 
    BEFORE UPDATE ON insight_cards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_comments_updated_at 
    BEFORE UPDATE ON dashboard_comments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""

# Rollback SQL for development purposes
ROLLBACK_SQL = """
DROP TRIGGER IF EXISTS update_dashboard_comments_updated_at ON dashboard_comments;
DROP TRIGGER IF EXISTS update_insight_cards_updated_at ON insight_cards;
DROP TRIGGER IF EXISTS update_dashboards_updated_at ON dashboards;

DROP FUNCTION IF EXISTS update_updated_at_column();

DROP TABLE IF EXISTS dashboard_shares;
DROP TABLE IF EXISTS dashboard_comments;
DROP TABLE IF EXISTS insight_cards;
DROP TABLE IF EXISTS dashboards;
"""

if __name__ == "__main__":
    print("Analytics Dashboard Schema Migration")
    print("=====================================")
    print()
    print("To apply this migration, run the SQL commands in ANALYTICS_SCHEMA_SQL")
    print("against your PostgreSQL database.")
    print()
    print("Tables to be created:")
    print("- dashboards: Main dashboard configuration")
    print("- insight_cards: Individual dashboard cards")
    print("- dashboard_comments: Collaboration comments")
    print("- dashboard_shares: Sharing permissions")
    print()
    print(f"SQL Length: {len(ANALYTICS_SCHEMA_SQL)} characters")
