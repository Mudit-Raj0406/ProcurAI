"use client";

import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import ComparisonTable from '../components/ComparisonTable';
import GlassCard from '../components/GlassCard';
import ProjectList from '../components/ProjectList';
import CreateProjectModal from '../components/CreateProjectModal';
import AuditTrail from '../components/AuditTrail';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import api from '../lib/api';
import { LogOut, User, Plus, LayoutGrid, ArrowLeft, History as HistoryIcon, FileText, CheckCircle2, Sparkles, RefreshCw, Loader2, Trash2, BarChart3 } from 'lucide-react';

export default function Home() {
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [rfqId, setRfqId] = useState(""); // Empty by default
    const [view, setView] = useState<'dashboard' | 'analysis' | 'audit'>('dashboard');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [projectData, setProjectData] = useState<any>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const { user, loading, logout } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !user) {
            router.push('/login');
        }
    }, [user, loading, router]);

    useEffect(() => {
        if (rfqId && view === 'analysis') {
            fetchProjectDetails();
        }
    }, [rfqId, view, refreshTrigger]);

    const fetchProjectDetails = async () => {
        try {
            const response = await api.get(`/quotes/projects/${rfqId}`);
            setProjectData(response.data);
        } catch (err) {
            console.error("Failed to fetch project details", err);
        }
    };

    const handleUploadComplete = () => {
        setRefreshTrigger(prev => prev + 1);
    };

    const handleStartAnalysis = async () => {
        if (!rfqId) return;
        setIsAnalyzing(true);
        try {
            await api.post(`/quotes/process-analysis/${rfqId}`);
            setRefreshTrigger(prev => prev + 1);
        } catch (error) {
            console.error("Analysis failed", error);
            alert("Analysis failed. Please check the backend logs.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSelectProject = (id: string) => {
        setRfqId(id);
        setView('analysis');
    };

    const handleRemoveBid = async (bidId: number) => {
        if (!confirm("Are you sure you want to remove this vendor bid?")) return;
        try {
            await api.delete(`/quotes/bids/${bidId}`);
            setRefreshTrigger(prev => prev + 1);
        } catch (error) {
            console.error("Failed to remove bid", error);
            alert("Failed to remove bid.");
        }
    };

    const handleRemoveRFQ = async () => {
        if (!confirm("Are you sure you want to remove the Master RFQ? This will reset the baseline requirements.")) return;
        try {
            await api.delete(`/quotes/projects/${rfqId}/rfq`);
            setRefreshTrigger(prev => prev + 1);
        } catch (error) {
            console.error("Failed to remove RFQ", error);
            alert("Failed to remove RFQ.");
        }
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center text-white">Loading...</div>;
    if (!user) return null; // Prevent flash of content before redirect

    return (
        <main className="min-h-screen p-8 flex flex-col items-center justify-center font-sans">
            <div className="w-full max-w-6xl z-10">
                <header className="mb-12 text-center relative">
                    <div className="absolute top-0 right-0 z-50 flex items-center gap-4">
                        <div className="flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full border border-white/20">
                            <User className="w-4 h-4 text-white/70" />
                            <span className="text-sm font-medium text-white/90">
                                {user.email} <span className="opacity-50 mx-1">|</span>
                                <span className="text-blue-300 uppercase tracking-tighter text-xs font-black">{user.role}</span>
                            </span>
                        </div>
                        <button
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); logout(); }}
                            className="bg-red-500/20 hover:bg-red-500/40 p-2.5 rounded-full border border-red-500/30 transition-all group cursor-pointer relative z-50"
                            title="Log Out"
                            type="button"
                        >
                            <LogOut className="w-5 h-5 text-red-200 group-hover:scale-110 transition-transform pointer-events-none" />
                        </button>
                    </div>
                    <h1 className="text-6xl font-black text-white drop-shadow-lg mb-2 tracking-tight">
                        ProcurAI
                    </h1>
                    <p className="text-xl text-white/90 font-light tracking-wide uppercase">
                        Intelligent Procurement Assistant
                    </p>
                </header>

                {(view === 'dashboard' || view === 'audit') ? (
                    <>
                        <div className="flex items-center justify-between mb-8">
                            <h2 className="text-3xl font-bold text-white drop-shadow-md flex items-center gap-3">
                                <LayoutGrid className="w-8 h-8 text-blue-400" />
                                RFQ Projects
                            </h2>
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setView(view === 'audit' ? 'dashboard' : 'audit')}
                                    className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white/70 rounded-xl text-sm font-bold transition-all border border-white/10 flex items-center gap-2"
                                >
                                    <HistoryIcon className="w-4 h-4" />
                                    {view === 'audit' ? 'View Projects' : 'Governance Log'}
                                </button>
                                <button
                                    onClick={() => setIsModalOpen(true)}
                                    className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-bold transition-all shadow-lg hover:shadow-blue-500/30 flex items-center gap-2"
                                >
                                    <Plus className="w-4 h-4" />
                                    New Project
                                </button>
                            </div>
                        </div>

                        {view === 'audit' ? (
                            <AuditTrail />
                        ) : (
                            <ProjectList onSelectProject={handleSelectProject} />
                        )}

                        <CreateProjectModal
                            isOpen={isModalOpen}
                            onClose={() => setIsModalOpen(false)}
                            onSuccess={(id) => handleSelectProject(id)}
                        />
                    </>
                ) : (
                    <>
                        <button
                            onClick={() => setView('dashboard')}
                            className="flex items-center gap-2 text-white/60 hover:text-white mb-8 transition-colors font-medium"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back to Dashboard
                        </button>

                        <GlassCard className="mb-10">
                            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                                <div className="flex-1 w-full">
                                    <label className="block text-sm font-semibold text-white/80 mb-2 uppercase tracking-wider">
                                        Current RFQ Identifier
                                    </label>
                                    <input
                                        type="text"
                                        value={rfqId}
                                        readOnly
                                        className="w-full px-5 py-3 bg-white/5 border border-white/10 rounded-lg text-white/50 cursor-not-allowed opacity-70"
                                    />
                                </div>
                                <div className="flex-1 w-full">
                                    <div className="text-sm text-white/70 italic mb-2">
                                        Active analysis session
                                    </div>
                                    <div className="bg-blue-500/10 rounded-lg p-3 text-center border border-blue-500/20">
                                        <span className="font-bold text-blue-300">Automotive Intelligence Enabled</span>
                                    </div>
                                </div>
                            </div>
                        </GlassCard>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                            <section>
                                <h2 className="text-2xl font-bold text-white mb-6 drop-shadow-md flex items-center gap-2">
                                    <FileText className="w-6 h-6 text-blue-400" />
                                    1. Master RFQ Baseline
                                </h2>
                                <FileUpload
                                    onUploadComplete={handleUploadComplete}
                                    rfqId={rfqId}
                                    type="rfq"
                                />

                                {projectData?.rfq_filename && (
                                    <GlassCard className={`mt-6 ${projectData.status === 'Extraction Failed' ? 'border-red-500/30 bg-red-500/5' : 'border-blue-500/30 bg-blue-500/5'}`}>
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-sm font-black text-blue-300 uppercase tracking-widest flex items-center gap-2">
                                                <CheckCircle2 className="w-4 h-4" />
                                                Master RFQ: {projectData.rfq_filename}
                                            </h3>
                                            <button
                                                onClick={handleRemoveRFQ}
                                                className="p-1.5 rounded-md hover:bg-red-500/20 text-white/30 hover:text-red-400 transition-colors"
                                                title="Remove RFQ Baseline"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>

                                        {/* Document Status Badge */}
                                        <div className={`mb-4 flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider w-fit border ${projectData.status === 'Extraction Failed'
                                            ? 'bg-red-500/10 border-red-500/20 text-red-400'
                                            : 'bg-green-500/10 border-green-500/20 text-green-400'
                                            }`}>
                                            <div className={`w-1.5 h-1.5 rounded-full ${projectData.status === 'Extraction Failed' ? 'bg-red-400' : 'bg-green-400 animate-pulse'}`} />
                                            {projectData.status}
                                        </div>

                                        {projectData.rfq_requirements && (
                                            <div className="space-y-4">
                                                {JSON.parse(projectData.rfq_requirements).summary && (
                                                    <div className="bg-white/5 p-4 rounded-xl border border-white/10 mb-4">
                                                        <span className="text-[10px] text-blue-300 uppercase font-black tracking-widest block mb-1">Project Summary</span>
                                                        <p className="text-sm text-white/80 italic leading-relaxed">
                                                            "{JSON.parse(projectData.rfq_requirements).summary}"
                                                        </p>
                                                    </div>
                                                )}

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {Object.entries(JSON.parse(projectData.rfq_requirements))
                                                        .filter(([key]) => key !== 'summary')
                                                        .map(([key, value]: [string, any]) => (
                                                            <div key={key} className="flex flex-col p-2 bg-white/5 rounded-lg border border-white/5">
                                                                <span className="text-[9px] text-white/30 uppercase font-black tracking-tighter mb-1">{key.replace('_', ' ')}</span>
                                                                <span className="text-xs text-white/90 font-medium">
                                                                    {Array.isArray(value)
                                                                        ? (value.length > 0
                                                                            ? value.map(v => typeof v === 'object' ? JSON.stringify(v) : String(v)).join(', ')
                                                                            : 'None')
                                                                        : (typeof value === 'object' && value !== null
                                                                            ? Object.entries(value).map(([k, v]) => `${k}: ${v}`).join(', ')
                                                                            : (value || 'Not specified'))}
                                                                </span>
                                                            </div>
                                                        ))}
                                                </div>
                                            </div>
                                        )}
                                        {projectData.status === 'Extraction Failed' && (
                                            <p className="text-xs text-red-300/60 italic mt-4">
                                                Advanced extraction failed for this PDF. AI analysis will use plain text fallback.
                                            </p>
                                        )}
                                    </GlassCard>
                                )}
                            </section>

                            <section>
                                <h2 className="text-2xl font-bold text-white mb-6 drop-shadow-md flex items-center gap-2">
                                    <Plus className="w-6 h-6 text-purple-400" />
                                    2. Vendor Submissions
                                </h2>
                                <FileUpload
                                    onUploadComplete={handleUploadComplete}
                                    rfqId={rfqId}
                                    type="bid"
                                />

                                {projectData?.bids && projectData.bids.length > 0 && (
                                    <div className="mt-6 space-y-3">
                                        <h3 className="text-xs font-black text-purple-300 uppercase tracking-widest mb-2 flex items-center gap-2">
                                            <HistoryIcon className="w-3 h-3" />
                                            Successfully Uploaded Bids ({projectData.bids.length})
                                        </h3>
                                        <div className="grid grid-cols-1 gap-2">
                                            {projectData.bids.map((bid: any) => (
                                                <div key={bid.id} className="flex items-center justify-between bg-white/5 border border-white/10 p-3 rounded-lg group hover:border-purple-500/30 transition-all">
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2 bg-purple-500/10 rounded-md">
                                                            <FileText className="w-4 h-4 text-purple-300" />
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-bold text-white/90 truncate max-w-[200px]">{bid.filename}</p>
                                                            <p className="text-[10px] text-white/40">{bid.vendor_name}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase border ${bid.status === 'extraction_failed'
                                                            ? 'bg-red-500/20 text-red-400 border-red-500/20'
                                                            : 'bg-green-500/20 text-green-400 border-green-500/20'
                                                            }`}>
                                                            {bid.status === 'extraction_failed' ? 'Failed' : 'Ready'}
                                                        </span>
                                                        <button
                                                            onClick={() => handleRemoveBid(bid.id)}
                                                            className="p-1.5 rounded-md hover:bg-red-500/20 text-white/30 hover:text-red-400 transition-colors"
                                                            title="Remove Bid"
                                                        >
                                                            <Trash2 className="w-3.5 h-3.5" />
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {!projectData?.rfq_requirements && (
                                    <p className="mt-4 text-sm text-yellow-300/70 italic text-center">
                                        Tip: Upload the Master RFQ first for requirement-based scoring.
                                    </p>
                                )}
                            </section>
                        </div>

                        <section className="w-full">
                            <div className="flex items-center justify-between mb-8">
                                <h2 className="text-3xl font-bold text-white drop-shadow-md flex items-center gap-3">
                                    <span className="bg-white/20 p-2 rounded-lg"><BarChart3 className="w-6 h-6" /></span> Comparative Analysis
                                </h2>
                                <div className="flex gap-4">
                                    <button
                                        onClick={handleStartAnalysis}
                                        disabled={isAnalyzing}
                                        className={`px-8 py-2.5 rounded-xl text-sm font-black transition-all shadow-xl flex items-center gap-2 ${isAnalyzing
                                            ? 'bg-blue-600/50 cursor-not-allowed text-white/50'
                                            : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white hover:scale-105 active:scale-95'
                                            }`}
                                    >
                                        {isAnalyzing ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                Processing AI Analysis...
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="w-4 h-4" />
                                                Start AI Analysis
                                            </>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => setRefreshTrigger(prev => prev + 1)}
                                        className="px-6 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-bold transition-all shadow-lg border border-white/10 backdrop-blur-md flex items-center gap-2"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Refresh Data
                                    </button>
                                </div>
                            </div>
                            {projectData?.status === 'Analyzed' ? (
                                <ComparisonTable refreshTrigger={refreshTrigger} rfqId={rfqId} />
                            ) : (
                                <GlassCard className="p-16 text-center border-dashed border-white/10">
                                    <Sparkles className="w-16 h-16 text-blue-400/20 mx-auto mb-6" />
                                    <h3 className="text-2xl font-bold text-white mb-2">Ready for AI Analysis</h3>
                                    <p className="text-white/50 max-w-md mx-auto">
                                        Once you have uploaded the Master RFQ and all vendor bids, click the <span className="text-blue-400 font-bold">Start AI Analysis</span> button above to generate scores and the executive summary.
                                    </p>
                                    {isAnalyzing && (
                                        <div className="mt-8 flex flex-col items-center gap-4">
                                            <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full">
                                                <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                                                <span className="text-sm font-bold text-blue-300 animate-pulse uppercase tracking-widest">Processing Automotive Big Data...</span>
                                            </div>
                                        </div>
                                    )}
                                </GlassCard>
                            )}
                        </section>
                    </>
                )}
            </div>
        </main>
    );
}
