import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  Cpu, 
  Award, 
  FileSearch, 
  UserCheck, 
  FolderKanban, 
  BarChart3,
  Database
} from 'lucide-react';

interface NavigationProps {
  currentCaseId?: string | null;
}

export const Navigation: React.FC<NavigationProps> = ({ currentCaseId }) => {
  const location = useLocation();
  const caseParam = currentCaseId ? `?caseId=${encodeURIComponent(currentCaseId)}` : '';

  const navItems = [
    {
      name: 'Overview',
      path: '/overview',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      name: 'New Verification',
      path: '/upload',
      icon: UploadCloud,
      step: '01',
    },
    {
      name: 'Analyze',
      path: `/processing${caseParam}`,
      icon: Cpu,
      step: '02',
    },
    {
      name: 'Result',
      path: `/result${caseParam}`,
      icon: Award,
      step: '03',
    },
    {
      name: 'Evidence',
      path: `/evidence${caseParam}`,
      icon: FileSearch,
      badge: null,
    },
    {
      name: 'Human Review',
      path: `/human-review${caseParam}`,
      icon: UserCheck,
      badge: null,
    },
    {
      name: 'Cases',
      path: '/cases',
      icon: FolderKanban,
      badge: null,
    },
    {
      name: 'Master Registry',
      path: '/registry',
      icon: Database,
      badge: null,
    },
    {
      name: 'Reports',
      path: '/reports',
      icon: BarChart3,
      badge: null,
    },
  ];

  return (
    <nav className="border-b border-[#e0e2e6] bg-white shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-1.5 overflow-x-auto py-2 scrollbar-none items-center">
          {navItems.map((item) => {
            const Icon = item.icon;
            // Check active based on pathname
            const isActive = 
              (item.path === '/overview' && (location.pathname === '/' || location.pathname === '/overview')) ||
              (item.path.startsWith('/upload') && location.pathname === '/upload') ||
              (item.path.startsWith('/processing') && location.pathname === '/processing') ||
              (item.path.startsWith('/result') && location.pathname === '/result') ||
              (item.path.startsWith('/evidence') && location.pathname === '/evidence') ||
              (item.path.startsWith('/human-review') && location.pathname === '/human-review') ||
              (item.path.startsWith('/cases') && location.pathname === '/cases') ||
              (item.path.startsWith('/registry') && location.pathname === '/registry') ||
              (item.path.startsWith('/reports') && location.pathname === '/reports');

            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-full text-xs font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-[#e8f0fe] text-[#1a73e8] font-semibold shadow-xs'
                    : 'text-[#5f6368] hover:text-[#202124] hover:bg-[#f1f3f4]'
                }`}
              >
                {item.step && (
                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-[#1a73e8] text-white' : 'bg-[#dadce0] text-[#5f6368]'
                  }`}>
                    {item.step}
                  </span>
                )}
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#1a73e8]' : 'text-[#5f6368]'}`} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
