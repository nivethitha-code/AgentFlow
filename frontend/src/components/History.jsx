import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileClock, ChevronRight, Activity, Trash2 } from 'lucide-react';

export function History() {
    const [runs, setRuns] = useState([]);

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    const fetchHistory = async () => {
        try {
            const res = await fetch(`${API_URL}/history`);
            if (res.ok) {
                const data = await res.json();
                setRuns(data);
            } else {
                console.error('Failed to fetch history:', res.status, res.statusText);
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const handleDeleteRun = async (e, runId) => {
        e.preventDefault();
        e.stopPropagation();
        if (!window.confirm('Delete this execution run?')) return;
        try {
            const res = await fetch(`${API_URL}/run/${runId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                fetchHistory(); // Refresh list
            }
        } catch (e) {
            console.error(e);
            alert('Failed to delete run');
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold">Execution History</h1>

            <div className="grid gap-4">
                {runs.map((run, i) => (
                    <Link key={run.id} to={`/run/${run.id}`}>
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 p-4 rounded-xl shadow-sm hover:shadow-md hover:border-blue-500/30 transition-all flex items-center justify-between"
                        >
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${run.status === 'completed' ? 'bg-green-100 text-green-600' :
                                    run.status === 'failed' ? 'bg-red-100 text-red-600' :
                                        'bg-blue-100 text-blue-600'
                                    }`}>
                                    <Activity size={20} />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg">{run.workflows?.name || 'Untitled Workflow'}</h3>
                                    <div className="flex items-center gap-3 text-sm text-gray-500">
                                        <span>{new Date(run.created_at).toLocaleString()}</span>
                                        <span className="w-1 h-1 rounded-full bg-gray-300" />
                                        <span className="capitalize">{run.status}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <button
                                    onClick={(e) => handleDeleteRun(e, run.id)}
                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                    title="Delete run"
                                >
                                    <Trash2 size={18} />
                                </button>
                                <ChevronRight className="text-gray-300 group-hover:text-blue-500 transition-colors" />
                            </div>
                        </motion.div>
                    </Link>
                ))}
            </div>
        </div>
    );
}
