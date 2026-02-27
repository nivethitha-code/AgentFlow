import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Plus, Zap, ArrowRight, Activity, Cpu } from 'lucide-react';
import { NamingModal } from './NamingModal';

export function Home() {
    const navigate = useNavigate();
    const [isModalOpen, setIsModalOpen] = useState(false);

    return (
        <div className="max-w-6xl mx-auto pt-4 pb-12 px-4">
            <NamingModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />

            {/* Hero Section */}
            <div className="text-center space-y-6 mb-12">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20 mb-4"
                >
                    <Zap size={16} fill="currentColor" />
                    <span className="text-sm font-semibold uppercase tracking-wider">Next-Gen Automation</span>
                </motion.div>

                <motion.h1
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="text-6xl md:text-7xl font-extrabold tracking-tight"
                >
                    Welcome to the <br />
                    <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
                        Agentic Workflow Builder
                    </span>
                </motion.h1>

                <motion.p
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed"
                >
                    Design, deploy, and manage powerful AI agents that collaborate to solve complex tasks.
                    Create your own multi-step workflows with ease.
                </motion.p>

                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
                >
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setIsModalOpen(true)}
                        className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-2xl font-bold shadow-xl shadow-blue-500/20 text-lg group"
                    >
                        <Plus size={24} />
                        Create a New Workflow
                        <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                    </motion.button>
                </motion.div>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {[
                    {
                        icon: Cpu,
                        title: "Multi-Model Support",
                        desc: "Chain together different LLMs like Llama 3 and Mixtral for specialized tasks.",
                        color: "blue"
                    },
                    {
                        icon: Activity,
                        title: "Real-time Execution",
                        desc: "Monitor your workflows as they execute step-by-step with detailed feedback.",
                        color: "purple"
                    },
                    {
                        icon: Zap,
                        title: "Smart Validation",
                        desc: "Use LLM-based judging or precise pattern matching to ensure quality outputs.",
                        color: "pink"
                    }
                ].map((feature, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 + i * 0.1 }}
                        className="bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm border border-gray-200 dark:border-gray-800 p-8 rounded-3xl hover:border-blue-500/50 transition-colors group"
                    >
                        <div className={`w-14 h-14 rounded-2xl bg-${feature.color}-500/10 flex items-center justify-center text-${feature.color}-500 mb-6 group-hover:scale-110 transition-transform`}>
                            <feature.icon size={28} />
                        </div>
                        <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                        <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                            {feature.desc}
                        </p>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
