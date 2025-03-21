import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../theme-provider'
import { BarChart3, FileQuestion, Home, History, TestTube, Moon, Sun, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '../ui/button'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const { theme, setTheme } = useTheme()
  const location = useLocation()

  const navigationItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Ask Question', href: '/ask', icon: FileQuestion },
    { name: 'History', href: '/history', icon: History },
    { name: 'Test Connection', href: '/testing', icon: TestTube },
  ]

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">FinOps Expert</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Button variant="ghost" size="icon" title="Settings">
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="container flex-1 items-start md:grid md:grid-cols-[220px_1fr] md:gap-6 lg:grid-cols-[240px_1fr] lg:gap-10 py-6">
        {/* Sidebar */}
        <aside className="fixed top-20 z-30 hidden h-[calc(100vh-80px)] w-full shrink-0 overflow-y-auto border-r md:sticky md:block">
          <nav className="grid items-start px-2 py-4 text-sm">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 transition-all",
                    isActive
                      ? "bg-accent text-accent-foreground font-medium"
                      : "hover:bg-accent/50 hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </aside>

        {/* Content */}
        <main className="w-full">{children}</main>
      </div>

      {/* Footer */}
      <footer className="border-t py-4 bg-background/95">
        <div className="container flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} FinOps Expert. All rights reserved.
          </p>
          <p className="text-sm text-muted-foreground">
            Powered by Azure AI Foundry and Bing Grounding
          </p>
        </div>
      </footer>
    </div>
  )
} 