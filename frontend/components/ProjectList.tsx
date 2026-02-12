"use client";

import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import GlassCard from './GlassCard';
import { LayoutGrid, Clock, ChevronRight, Package, Box, Trash2, AlertCircle } from 'lucide-react';

interface Project {
    id: number;
    rfq_id: string;
    title: string;
    category: string;
    status: string;
    created_at: string;
}

export default function ProjectList({ onSelectProject }: { onSelectProject: (rfqId: string) => void }) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const res = await api.get('/quotes/projects');
            setProjects(res.data);
        } catch (err) {
            console.error("Failed to fetch projects", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteProject = async (e: React.MouseEvent, rfqId: string) => {
        e.stopPropagation();
        if (!confirm(`Are you sure you want to delete project ${rfqId}? This will remove all associated bids.`)) return;

        try {
            await api.delete(`/quotes/projects/${rfqId}`);
            fetchProjects();
        } catch (err) {
            console.error("Failed to delete project", err);
            alert("Failed to delete project. Please try again.");
        }
    };

    if (loading) return <div className="text-white/50 animate-pulse text-center p-10">Loading projects...</div>;

    if (projects.length === 0) return (
        <GlassCard className="text-center p-12">
            <Package className="w-12 h-12 text-white/20 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Projects Yet</h3>
            <p className="text-white/50">Create your first RFQ project to start comparing vendor quotes.</p>
        </GlassCard>
    );

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
                <GlassCard
                    key={project.id}
                    className="group cursor-pointer hover:scale-[1.02] transition-all duration-300 border-white/5 hover:border-white/20"
                    onClick={() => onSelectProject(project.rfq_id)}
                >
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                            <Box className="w-5 h-5 text-blue-300" />
                        </div>
                        <div className="flex items-center gap-2">
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-white/10 ${project.status === 'Open' ? 'text-green-400' : 'text-blue-400'}`}>
                                {project.status}
                            </span>
                            <button
                                onClick={(e) => handleDeleteProject(e, project.rfq_id)}
                                className="p-1.5 rounded-md hover:bg-red-500/20 text-white/30 hover:text-red-400 transition-colors"
                                title="Delete Project"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    </div>
                    <h3 className="text-lg font-bold text-white mb-1 group-hover:text-blue-300 transition-colors">
                        {project.title}
                    </h3>
                    <p className="text-xs text-white/40 mb-4 font-mono">{project.rfq_id}</p>

                    <div className="flex items-center gap-4 text-[11px] text-white/50 mb-6 font-medium">
                        <div className="flex items-center gap-1.5 uppercase tracking-wider">
                            <LayoutGrid className="w-3.5 h-3.5" />
                            {project.category || "Uncategorized"}
                        </div>
                        <div className="flex items-center gap-1.5 uppercase tracking-wider">
                            <Clock className="w-3.5 h-3.5" />
                            {new Date(project.created_at).toLocaleDateString()}
                        </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-white/5 text-xs font-bold text-white/70 group-hover:text-white transition-colors">
                        View Analysis
                        <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </div>
                </GlassCard>
            ))}
        </div>
    );
}
