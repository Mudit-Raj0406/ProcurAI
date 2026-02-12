"use client";

import React, { useState } from 'react';
import api from '../lib/api';
import GlassCard from './GlassCard';
import { X, Plus, Loader2 } from 'lucide-react';

export default function CreateProjectModal({ isOpen, onClose, onSuccess }: { isOpen: boolean, onClose: () => void, onSuccess: (rfqId: string) => void }) {
    const [title, setTitle] = useState('');
    const [rfqId, setRfqId] = useState('');
    const [category, setCategory] = useState('Machined Parts');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const response = await api.post('/quotes/projects', {
                title,
                rfq_id: rfqId,
                category,
                description: ""
            });
            onSuccess(response.data.rfq_id);
            // Reset fields
            setTitle('');
            setRfqId('');
            onClose();
        } catch (err: any) {
            console.error("Failed to create project", err);
            const detail = err.response?.data?.detail || "Could not connect to the server. Please try again later.";
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <GlassCard className="w-full max-w-md !p-8 relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-white/50 hover:text-white">
                    <X className="w-5 h-5" />
                </button>

                <h2 className="text-2xl font-bold text-white mb-6">Create New RFQ Project</h2>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-xs font-black text-white/50 uppercase tracking-widest mb-2">Project Title</label>
                        <input
                            required
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            placeholder="e.g., Engine Block Casting Q1"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-black text-white/50 uppercase tracking-widest mb-2">RFQ ID</label>
                        <input
                            required
                            type="text"
                            value={rfqId}
                            onChange={(e) => setRfqId(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            placeholder="e.g., RFQ-2024-001"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-black text-white/50 uppercase tracking-widest mb-2">Category</label>
                        <select
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none"
                        >
                            <option value="Machined Parts">Machined Parts</option>
                            <option value="Electronics">Electronics</option>
                            <option value="Fasteners">Fasteners</option>
                            <option value="Packaging">Packaging</option>
                            <option value="Services">Services</option>
                        </select>
                    </div>

                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-200 text-xs text-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg hover:shadow-blue-500/25 flex items-center justify-center gap-2"
                    >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                        Create Project
                    </button>
                </form>
            </GlassCard>
        </div>
    );
}
