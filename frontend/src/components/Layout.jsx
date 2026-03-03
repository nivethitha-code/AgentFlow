import React from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, History, Zap, Home } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { NamingModal } from './NamingModal';

const SidebarItem = ({ icon: Icon, label, path, active, onClick }) => {
    const content = (
        <motion.div
            whileHover={{ x: 5 }}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all relative ${active
                ? 'bg-primary/10 text-primary font-medium shadow-sm border border-primary/20'
                : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
        >
            <Icon size={20} />
            <span>{label}</span>
            {active && (
                <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 w-1 h-8 bg-primary rounded-r-full"
                />
            )}
        </motion.div>
    );

    if (onClick) {
        return (
            <button onClick={onClick} className="w-full text-left">
                {content}
            </button>
        );
    }

    return (
        <Link to={path}>
            {content}
        </Link>
    );
};

export function Layout({ children }) {
    const location = useLocation();
    const [isModalOpen, setIsModalOpen] = React.useState(false);

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 overflow-hidden transition-colors duration-300">
            <NamingModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />

            {/* Sidebar */}
            <motion.aside
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                className="w-64 bg-white/70 dark:bg-black/40 backdrop-blur-md border-r border-gray-200 dark:border-gray-800 p-6 flex flex-col z-20"
            >
                <div className="flex items-center gap-2 mb-10 px-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        <Zap size={18} fill="currentColor" />
                    </div>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
                        AgentFlow
                    </h1>
                </div>

                <nav className="flex-1 space-y-2">
                    <SidebarItem
                        icon={Home}
                        label="Home"
                        path="/"
                        active={location.pathname === '/'}
                    />
                    <SidebarItem
                        icon={LayoutDashboard}
                        label="Builder"
                        path="/builder"
                        active={location.pathname === '/builder'}
                        onClick={() => setIsModalOpen(true)}
                    />
                    <SidebarItem
                        icon={History}
                        label="History"
                        path="/history"
                        active={location.pathname === '/history'}
                    />
                </nav>

                <div className="mt-auto pt-6 border-t border-gray-200 dark:border-gray-800">
                    <div className="flex items-center gap-3 px-2 py-2 text-sm text-gray-500">
                        <span>v1.0.0</span>
                    </div>
                </div>
            </motion.aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-full relative overflow-hidden">
                {/* Background Gradients */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-3xl pointer-events-none translate-y-1/2 -translate-x-1/2" />

                {/* Top Bar */}
                <header className="h-16 flex items-center justify-between px-8 z-10 pt-4">
                    <div className="flex items-center gap-4">
                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20"
                        >
                            <Zap size={14} fill="currentColor" />
                            <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider">Next-Gen Automation</span>
                        </motion.div>
                    </div>

                    <div className="flex items-center gap-6">
                        {/* Model Health Status */}
                        <div className="flex items-center gap-4 text-xs font-medium px-4 py-2 rounded-full bg-white/50 dark:bg-black/20 border border-gray-200 dark:border-gray-800 backdrop-blur-sm">
                            <div className="flex items-center gap-2">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                </span>
                                <span className="text-gray-600 dark:text-gray-400">Llama 3.3</span>
                            </div>
                            <div className="w-px h-3 bg-gray-300 dark:bg-gray-700" />
                            <div className="flex items-center gap-2">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                </span>
                                <span className="text-gray-600 dark:text-gray-400">Llama 3.1</span>
                            </div>
                        </div>

                        <ThemeToggle />
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto p-8 z-10">
                    {children}
                </main>
            </div>
        </div>
    );
}
