import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Loader2, XCircle, ArrowLeft, RotateCcw, Trash2, Play } from 'lucide-react';
import confetti from 'canvas-confetti';
import { cn } from '../lib/utils';

export function RunViewer() {
    const { runId } = useParams();
    const navigate = useNavigate();
    const [run, setRun] = useState(null);
    const [isRerunning, setIsRerunning] = useState(false);
    const [runningStepIndex, setRunningStepIndex] = useState(null);

    useEffect(() => {
        fetchRun();

        // Subscribe to realtime updates
        const channel = supabase
            .channel('workflow_updates')
            .on(
                'postgres_changes',
                {
                    event: 'UPDATE',
                    schema: 'public',
                    table: 'workflow_runs',
                    filter: `id=eq.${runId}`,
                },
                (payload) => {
                    setRun(payload.new);
                    if (payload.new.status === 'completed') {
                        confetti({
                            particleCount: 100,
                            spread: 70,
                            origin: { y: 0.6 }
                        });
                    }
                }
            )
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, [runId]);

    const fetchRun = async () => {
        const res = await fetch(`http://localhost:8000/run/${runId}`);
        if (res.ok) {
            const data = await res.json();
            setRun(data);
        }
    };

    const handleRerun = async () => {
        if (!run?.workflow_id) return;

        setIsRerunning(true);
        try {
            const res = await fetch(`http://localhost:8000/run/${run.workflow_id}`, {
                method: 'POST'
            });

            if (!res.ok) throw new Error('Failed to start rerun');

            const data = await res.json();
            navigate(`/run/${data.run_id}`);
        } catch (e) {
            console.error(e);
            alert('Failed to start rerun');
        } finally {
            setIsRerunning(false);
        }
    };

    const handleRunStep = async (index) => {
        setRunningStepIndex(index);
        try {
            const res = await fetch(`http://localhost:8000/run/${runId}/step/${index}`, {
                method: 'POST'
            });
            if (!res.ok) throw new Error('Failed to run step');
        } catch (e) {
            console.error(e);
            alert('Failed to run step');
        } finally {
            setRunningStepIndex(null);
        }
    };



    const handleDeleteWorkflow = async () => {
        if (!window.confirm('Delete this workflow and ALL its runs PERMANENTLY? This cannot be undone.')) return;
        try {
            const res = await fetch(`http://localhost:8000/workflow/${run.workflow_id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                navigate('/history');
            }
        } catch (e) {
            console.error(e);
            alert('Failed to delete workflow');
        }
    };

    if (!run) return (
        <div className="flex items-center justify-center h-full">
            <Loader2 className="animate-spin text-blue-500" size={40} />
        </div>
    );

    return (
        <div className="max-w-3xl mx-auto space-y-8 pb-20">
            <div className="flex items-center justify-between gap-4 mb-2">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors text-gray-500"
                        title="Go Back"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div className="h-6 w-px bg-gray-200 dark:bg-gray-800 mx-2" />
                    <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Execution View</h2>
                </div>

                <div className="flex items-center gap-2">
                    {run.status !== 'running' && (
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleRerun}
                            disabled={isRerunning}
                            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition-all hover:shadow-indigo-500/40"
                        >
                            <motion.div
                                animate={isRerunning ? { rotate: 360 } : { rotate: 0 }}
                                transition={isRerunning ? { repeat: Infinity, duration: 1, ease: "linear" } : { duration: 0.3 }}
                            >
                                <RotateCcw size={18} />
                            </motion.div>
                            {isRerunning ? 'Starting...' : 'Rerun Workflow'}
                        </motion.button>
                    )}
                    <button
                        onClick={handleDeleteWorkflow}
                        className="flex items-center gap-2 px-6 py-2.5 text-sm font-bold bg-red-600 text-white hover:bg-red-700 rounded-xl transition-colors shadow-sm"
                        title="Delete workflow template and ALL history"
                    >
                        <Trash2 size={18} />
                        Workflow
                    </button>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Execution Status</h2>
                    <div className="flex items-center gap-2 mt-2">
                        <span className={cn(
                            "px-3 py-1 rounded-full text-xs font-medium capitalize",
                            run.status === 'completed' ? "bg-green-100 text-green-700" :
                                run.status === 'failed' ? "bg-red-100 text-red-700" :
                                    "bg-blue-100 text-blue-700"
                        )}>
                            {run.status}
                        </span>
                        <span className="text-gray-500 text-sm">ID: {run.id.slice(0, 8)}</span>
                    </div>
                </div>
            </div>

            <div className="space-y-6 relative">
                {/* Vertical Line */}
                <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-gray-200 dark:bg-gray-800 z-0" />

                {run.steps_results?.map((result, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="relative z-10 pl-14"
                    >
                        <div className={cn(
                            "absolute left-2 top-2 w-8 h-8 rounded-full border-4 border-gray-50 dark:border-gray-950 flex items-center justify-center transition-colors",
                            result.status === 'completed' ? "bg-green-500 text-white" :
                                result.status === 'running' ? "bg-blue-500 text-white animate-pulse" :
                                    result.status === 'failed' ? "bg-red-500 text-white" :
                                        "bg-gray-200 dark:bg-gray-800 text-gray-500"
                        )}>
                            {result.status === 'completed' && <CheckCircle2 size={16} />}
                            {result.status === 'running' && <Loader2 size={16} className="animate-spin" />}
                            {result.status === 'failed' && <XCircle size={16} />}
                            {result.status === 'pending' && <Circle size={16} />}
                        </div>

                        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden shadow-sm">
                            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
                                <div className="flex items-center gap-4">
                                    <h3 className="font-semibold text-blue-600 dark:text-blue-400">
                                        {result.step_name || `Step ${index + 1}`}
                                    </h3>
                                    <button
                                        onClick={() => handleRunStep(index)}
                                        disabled={runningStepIndex === index}
                                        className="p-1.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-500 rounded-md transition-colors disabled:opacity-50"
                                        title="Run this step only"
                                    >
                                        {runningStepIndex === index ? (
                                            <Loader2 size={14} className="animate-spin" />
                                        ) : (
                                            <Play size={14} />
                                        )}
                                    </button>
                                </div>
                                {result.retries_used > 0 && (
                                    <span className="text-xs text-orange-500 font-medium">{result.retries_used} Retries</span>
                                )}
                            </div>

                            <div className="p-4 bg-gray-50 dark:bg-black/20 font-mono text-sm space-y-3">
                                {result.input_context && (
                                    <div className="text-gray-500 truncate">
                                        <span className="text-xs uppercase tracking-wider font-bold text-gray-400 block mb-1">Input Context</span>
                                        {result.input_context.slice(0, 100)}...
                                    </div>
                                )}

                                {result.output ? (
                                    <div>
                                        <span className="text-xs uppercase tracking-wider font-bold text-gray-400 block mb-1">Output</span>
                                        <div className="whitespace-pre-wrap">{result.output}</div>
                                    </div>
                                ) : result.error ? (
                                    <div className="text-red-500">
                                        <span className="hidden">Error: </span>
                                        {result.error}
                                    </div>
                                ) : (
                                    <div className="text-gray-400 italic">Waiting to execute...</div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
