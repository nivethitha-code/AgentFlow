import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Play, ArrowLeft, Type } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const MODELS = [
    { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', cost: 'High' },
    { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B', cost: 'Low' },
    { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', cost: 'Medium' }
];

export function WorkflowEditor() {
    const navigate = useNavigate();
    const location = useLocation();
    const [name, setName] = useState('New Workflow');
    const [steps, setSteps] = useState([
        { id: 1, name: '', model: 'llama-3.1-8b-instant', prompt: '', criteria: { type: 'contains', value: '' } }
    ]);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (location.state?.workflowName) {
            setName(location.state.workflowName);
        }
    }, [location.state]);

    const addStep = () => {
        setSteps([
            ...steps,
            { id: Date.now(), name: '', model: 'llama-3.1-8b-instant', prompt: '', criteria: { type: 'contains', value: '' } }
        ]);
    };

    const removeStep = (id) => {
        setSteps(steps.filter(s => s.id !== id));
    };

    const updateStep = (id, field, value) => {
        setSteps(steps.map(s => s.id === id ? { ...s, [field]: value } : s));
    };

    const updateCriteria = (id, field, value) => {
        setSteps(steps.map(s => s.id === id ? { ...s, criteria: { ...s.criteria, [field]: value } } : s));
    };

    const handleSaveAndRun = async () => {
        setIsSaving(true);
        try {
            // 1. Create Workflow
            const formattedSteps = steps.map((s, index) => ({
                name: s.name || `Step ${index + 1}`,
                order: index,
                prompt_template: s.prompt,
                model: s.model,
                retry_limit: 3,
                completion_criteria: {
                    type: s.criteria.type,
                    value: s.criteria.value,
                    instruction: s.criteria.type === 'llm_judge' ? s.criteria.value : undefined
                }
            }));

            const response = await fetch('http://localhost:8000/workflows', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, steps: formattedSteps })
            });

            if (!response.ok) throw new Error('Failed to save');
            const workflow = await response.json();

            // 2. Run Workflow
            const runRes = await fetch(`http://localhost:8000/run/${workflow.id}`, {
                method: 'POST'
            });
            const run = await runRes.json();

            // 3. Navigate to Run View
            navigate(`/run/${run.run_id}`);
        } catch (e) {
            console.error(e);
            alert('Error saving workflow');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-20">
            <div className="flex items-center gap-4 mb-2">
                <button
                    onClick={() => navigate('/')}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors text-gray-500"
                    title="Back to Home"
                >
                    <ArrowLeft size={24} />
                </button>
                <div className="h-6 w-px bg-gray-200 dark:bg-gray-800 mx-2" />
                <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Workflow Builder</h2>
            </div>

            <div className="flex items-center justify-between">
                <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="text-4xl font-bold bg-transparent border-none focus:outline-none focus:ring-0 placeholder-gray-400 w-full"
                    placeholder="Workflow Name"
                />
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSaveAndRun}
                    disabled={isSaving}
                    className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-500/20 disabled:opacity-50 shrink-0"
                >
                    {isSaving ? 'Starting...' : <> <Play size={20} /> Save & Run </>}
                </motion.button>
            </div>

            <div className="space-y-6">
                <AnimatePresence mode="popLayout">
                    {steps.map((step, index) => (
                        <motion.div
                            key={step.id}
                            layout
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="relative group"
                        >
                            {/* Connector Line */}
                            {index < steps.length - 1 && (
                                <div className="absolute left-8 top-full h-6 w-0.5 bg-gray-200 dark:bg-gray-800 z-0" />
                            )}

                            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm relative z-10 transition-colors hover:border-blue-500/30">
                                <div className="flex items-start justify-between mb-6">
                                    <div className="flex items-center gap-3 flex-1">
                                        <div className="w-10 h-10 rounded-xl bg-blue-500 text-white flex items-center justify-center font-bold shrink-0 shadow-lg shadow-blue-500/20">
                                            {index + 1}
                                        </div>
                                        <div className="flex-1 space-y-1">
                                            <label className="text-[10px] uppercase tracking-widest font-bold text-gray-400 px-1">Step Name</label>
                                            <div className="relative group/input">
                                                <Type className="absolute left-0 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within/input:text-blue-500 transition-colors" size={16} />
                                                <input
                                                    value={step.name}
                                                    onChange={(e) => updateStep(step.id, 'name', e.target.value)}
                                                    className="w-full pl-6 bg-transparent border-none focus:outline-none focus:ring-0 font-semibold text-lg text-gray-700 dark:text-gray-200 placeholder-gray-300 dark:placeholder-gray-700"
                                                    placeholder="Enter the step name..."
                                                />
                                            </div>
                                        </div>
                                    </div>
                                    <button onClick={() => removeStep(step.id)} className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all ml-4">
                                        <Trash2 size={20} />
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-50 dark:border-gray-800/50">
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-500 mb-2 px-1">Model Selection</label>
                                            <select
                                                value={step.model}
                                                onChange={(e) => updateStep(step.id, 'model', e.target.value)}
                                                className="w-full bg-gray-50 dark:bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-xl p-3 text-sm focus:ring-0 transition-all outline-none"
                                            >
                                                {MODELS.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-500 mb-2 px-1">Prompt Template</label>
                                            <textarea
                                                value={step.prompt}
                                                onChange={(e) => updateStep(step.id, 'prompt', e.target.value)}
                                                placeholder="Use {{context}} to insert previous output"
                                                className="w-full bg-gray-50 dark:bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-xl p-4 text-sm focus:ring-0 h-32 resize-none transition-all outline-none"
                                            />
                                            <p className="text-xs text-gray-400 mt-2 px-1 flex items-center gap-1">
                                                <span className="w-1 h-1 rounded-full bg-blue-500" />
                                                Tip: Type <code>{'{{context}}'}</code> to use input from previous step.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="space-y-4 border-l border-gray-100 dark:border-gray-800/50 pl-6">
                                        <label className="block text-sm font-medium text-gray-500 mb-2 px-1">Completion Criteria</label>
                                        <div className="space-y-4">
                                            <select
                                                value={step.criteria.type}
                                                onChange={(e) => updateCriteria(step.id, 'type', e.target.value)}
                                                className="w-full bg-gray-50 dark:bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-xl p-3 text-sm focus:ring-0 transition-all outline-none"
                                            >
                                                <option value="contains">Contains Text</option>
                                                <option value="json_valid">Valid JSON</option>
                                                <option value="llm_judge">LLM Judge (AI Check)</option>
                                            </select>

                                            {step.criteria.type !== 'json_valid' && (
                                                <div className="relative group/criteria">
                                                    <input
                                                        value={step.criteria.value}
                                                        onChange={(e) => updateCriteria(step.id, 'value', e.target.value)}
                                                        placeholder={step.criteria.type === 'contains' ? 'Text to match...' : 'Describe what counts as success...'}
                                                        className="w-full bg-gray-50 dark:bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-xl p-3 text-sm focus:ring-0 transition-all outline-none"
                                                    />
                                                </div>
                                            )}

                                            <div className="p-4 rounded-xl bg-orange-500/5 border border-orange-500/10">
                                                <p className="text-xs text-orange-500/80 leading-relaxed">
                                                    <strong>System Note:</strong> The agent will automatically retry up to 3 times if the output fails this check.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={addStep}
                    className="w-full py-6 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-3xl flex items-center justify-center gap-3 text-gray-400 hover:text-blue-500 hover:border-blue-500/50 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all font-bold text-lg group"
                >
                    <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-hover:bg-blue-500 group-hover:text-white transition-colors">
                        <Plus size={20} />
                    </div>
                    Add Step
                </motion.button>
            </div>
        </div>
    );
}
