'use client'

import { ScrollArea } from '@/components/ui/scroll-area'

export default function DataTable({ data }) {
  if (!data || !data.columns || !data.rows) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 text-gray-400">
        No data to display
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
      <ScrollArea className="h-96">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                {data.columns.map((column, index) => (
                  <th 
                    key={index}
                    className="text-left p-3 font-medium text-gray-700 whitespace-nowrap"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row, rowIndex) => (
                <tr 
                  key={rowIndex}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  {row.map((cell, cellIndex) => (
                    <td 
                      key={cellIndex}
                      className="p-3 text-gray-700 whitespace-nowrap"
                    >
                      {cell !== null && cell !== undefined ? String(cell) : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ScrollArea>
      
      {/* Table info */}
      <div className="px-3 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
        Showing {data.rows.length} rows × {data.columns.length} columns
      </div>
    </div>
  )
}
