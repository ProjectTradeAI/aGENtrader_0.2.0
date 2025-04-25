import React from 'react';
import { Link, useLocation } from 'wouter';
import { 
  Home, 
  MessageSquare, 
  LineChart, 
  Settings,
  Radio,
  BarChart3
} from 'lucide-react';

interface NavigationProps {
  className?: string;
}

export function Navigation({ className = '' }: NavigationProps) {
  const [location] = useLocation();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/market-analysis', label: 'Market Analysis', icon: BarChart3 },
    { href: '/agent-comms', label: 'Agent Communications', icon: MessageSquare },
    { href: '/trades', label: 'Trades', icon: LineChart },
    { href: '/trading-ws', label: 'Live Trading', icon: Radio },
    { href: '/settings', label: 'Settings', icon: Settings }
  ];

  return (
    <nav className={`flex items-center space-x-4 lg:space-x-6 ${className}`}>
      {navItems.map((item) => {
        const isActive = location === item.href;
        return (
          <Link 
            key={item.href}
            href={item.href}
            className={`
              flex items-center text-sm font-medium transition-colors hover:text-primary 
              ${isActive
                ? 'text-primary font-semibold'
                : 'text-muted-foreground'
              }
            `}
          >
            <item.icon className="w-4 h-4 mr-2" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}