/**
 * Analytics Components Package
 *
 * This package contains all React components for the analytics dashboard feature.
 * Components are organized by functionality to maintain clean separation of concerns.
 *
 * Component Architecture:
 * - DashboardAnalytics.jsx: Main dashboard management interface
 * - PinToDashboard.jsx: Pin query results to dashboards
 * - DashboardBuilder.jsx: Dashboard creation and editing (to be implemented)
 * - DashboardGrid.jsx: Grid layout for dashboard cards (to be implemented)
 * - cards/: Individual card components (to be implemented)
 *
 * Design Principles:
 * - Reusable components with clear interfaces
 * - Proper state management and data flow
 * - Responsive design with Tailwind CSS
 * - Accessibility and user experience focus
 * - Clean separation of UI and business logic
 */

export { default as DashboardAnalytics } from './DashboardAnalytics.jsx'
export { default as PinToDashboard, PinButton } from './PinToDashboard.jsx'

// Export placeholder for future components
export const DashboardBuilder = () => <div>Dashboard Builder - Coming Soon</div>
export const DashboardGrid = () => <div>Dashboard Grid - Coming Soon</div>
