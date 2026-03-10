"use client";

import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { CheckCircle, XCircle, HelpCircle, Clock, ChevronDown, ChevronUp, MessageSquare, Shield, AlertTriangle, Bookmark, X } from 'lucide-react';
import GlassCard from './GlassCard';
import ScoringControls from './ScoringControls';
import ExecutiveSummary from './ExecutiveSummary';
import { useAuth } from '../context/AuthContext';

interface ScoreBreakdownItem {
    value: string | number;
    normalized: number;
    weight: number;
    score: number;
}

interface Bid {
    id: number;
    rfq_id: string;
    vendor_name: string;
    total_cost: number;
    lead_time: string;
    payment_terms: string;
    compliance_status: string;
    incoterms?: string;
    warranty_terms?: string;
    is_iatf_certified?: boolean;
    risk_flags?: string;
    score?: number;
    status?: string;
    reviewer_comments?: string;
    score_breakdown?: {
        price: ScoreBreakdownItem;
        lead_time: ScoreBreakdownItem;
        compliance: ScoreBreakdownItem;
    };
}

// Decision Modal Component
function DecisionModal({ bid, action, onClose, onSubmit }: {
    bid: Bid;
    action: string;
    onClose: () => void;
    onSubmit: (bidId: number, status: string, comment: string) => void;
}) {
    const [comment, setComment] = useState(bid.reviewer_comments || '');
    const [submitting, setSubmitting] = useState(false);

    const actionConfig: Record<string, { label: string; color: string; bgClass: string; borderClass: string }> = {
        shortlisted: { label: 'Shortlist', color: 'text-emerald-300', bgClass: 'bg-emerald-500/20 hover:bg-emerald-500/40', borderClass: 'border-emerald-500/30' },
        hold: { label: 'Hold', color: 'text-amber-300', bgClass: 'bg-amber-500/20 hover:bg-amber-500/40', borderClass: 'border-amber-500/30' },
        rejected: { label: 'Reject', color: 'text-red-300', bgClass: 'bg-red-500/20 hover:bg-red-500/40', borderClass: 'border-red-500/30' },
        approved: { label: 'Approve', color: 'text-green-300', bgClass: 'bg-green-500/20 hover:bg-green-500/40', borderClass: 'border-green-500/30' },
    };

    const config = actionConfig[action] || actionConfig.hold;

    const handleSubmit = async () => {
        setSubmitting(true);
        await onSubmit(bid.id, action, comment);
        setSubmitting(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
            <div
                className="bg-[#1a1a2e] border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className={`flex items-center justify-between px-6 py-4 border-b border-white/10`}>
                    <div className="flex items-center gap-3">
                        <Shield className={`w-5 h-5 ${config.color}`} />
                        <h3 className="text-lg font-bold text-white">
                            {config.label} Decision
                        </h3>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="px-6 py-5 space-y-4">
                    <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                        <p className="text-[10px] text-white/40 uppercase font-black tracking-widest mb-1">Vendor</p>
                        <p className="text-sm font-bold text-white">{bid.vendor_name}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-white/50">
                            <span>Score: {bid.score ?? 0}/100</span>
                            <span>Cost: ${bid.total_cost?.toLocaleString() || '—'}</span>
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-white/60 uppercase tracking-wider mb-2">
                            <MessageSquare className="w-3 h-3 inline mr-1.5" />
                            Decision Rationale / Comment
                        </label>
                        <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="Provide your rationale for this decision..."
                            rows={4}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 resize-none transition-all"
                        />
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-white/10 flex items-center justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-5 py-2 text-sm text-white/60 hover:text-white hover:bg-white/5 rounded-xl transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={submitting}
                        className={`px-6 py-2 text-sm font-bold rounded-xl border transition-all ${config.bgClass} ${config.borderClass} ${config.color} ${submitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {submitting ? 'Submitting...' : `Confirm ${config.label}`}
                    </button>
                </div>
            </div>
        </div>
    );
}

// Status badge helper
function StatusBadge({ status }: { status?: string }) {
    if (!status || status === 'pending' || status === 'ingested') return null;

    const config: Record<string, { label: string; bg: string; text: string; border: string }> = {
        approved: { label: 'APPROVED', bg: 'bg-green-500/20', text: 'text-green-300', border: 'border-green-500/30' },
        shortlisted: { label: 'SHORTLISTED', bg: 'bg-emerald-500/20', text: 'text-emerald-300', border: 'border-emerald-500/30' },
        hold: { label: 'ON HOLD', bg: 'bg-amber-500/20', text: 'text-amber-300', border: 'border-amber-500/30' },
        rejected: { label: 'REJECTED', bg: 'bg-red-500/20', text: 'text-red-300', border: 'border-red-500/30' },
    };

    const c = config[status] || { label: status.toUpperCase(), bg: 'bg-white/10', text: 'text-white/60', border: 'border-white/20' };

    return (
        <span className={`inline-flex items-center gap-1 mt-1 text-[10px] px-2 py-0.5 rounded-full font-black tracking-tighter border ${c.bg} ${c.text} ${c.border}`}>
            {status === 'shortlisted' && <Bookmark className="w-2.5 h-2.5" />}
            {status === 'hold' && <AlertTriangle className="w-2.5 h-2.5" />}
            {c.label}
        </span>
    );
}

export default function ComparisonTable({ refreshTrigger, rfqId }: { refreshTrigger: number, rfqId: string }) {
    const [bids, setBids] = useState<Bid[]>([]);
    const [loading, setLoading] = useState(false);
    const [summary, setSummary] = useState("");
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [weights, setWeights] = useState({ price: 0.5, lead_time: 0.3, compliance: 0.2 });
    const [expandedBidId, setExpandedBidId] = useState<number | null>(null);
    const [decisionModal, setDecisionModal] = useState<{ bid: Bid; action: string } | null>(null);
    const [editingComments, setEditingComments] = useState<Record<number, string>>({});
    const [savingComment, setSavingComment] = useState<number | null>(null);
    const { user } = useAuth();

    const isManager = user?.role === 'manager' || user?.role === 'procurement_manager';

    useEffect(() => {
        if (rfqId) {
            fetchData();
        }
    }, [refreshTrigger, rfqId]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/quotes/compare-bids/${rfqId}`);
            setBids(response.data);

            if (response.data.length > 0) {
                fetchSummary();
                handleRecalculate();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchSummary = async () => {
        setSummaryLoading(true);
        try {
            const res = await api.post('/quotes/analyze', { rfq_id: rfqId });
            setSummary(res.data.summary);
        } catch (err) {
            console.error(err);
        } finally {
            setSummaryLoading(false);
        }
    };

    const handleRecalculate = async () => {
        try {
            const res = await api.post('/quotes/score', { rfq_id: rfqId, weights });
            const sortedBids = res.data.sort((a: Bid, b: Bid) => (b.score || 0) - (a.score || 0));
            setBids(sortedBids);
        } catch (err) {
            console.error(err);
        }
    };

    const handleDecisionSubmit = async (bidId: number, status: string, comment: string) => {
        try {
            await api.patch(`/quotes/bids/${bidId}/status`, { status, comment });
            setBids(prev => prev.map(b =>
                b.id === bidId ? { ...b, status, reviewer_comments: comment } : b
            ));
            setDecisionModal(null);
        } catch (err) {
            console.error("Failed to update status", err);
        }
    };

    const handleSaveComment = async (bidId: number) => {
        const comment = editingComments[bidId];
        if (comment === undefined) return;
        setSavingComment(bidId);
        try {
            await api.patch(`/quotes/bids/${bidId}/comment`, { comment });
            setBids(prev => prev.map(b =>
                b.id === bidId ? { ...b, reviewer_comments: comment } : b
            ));
            // Clear from editing state
            setEditingComments(prev => {
                const copy = { ...prev };
                delete copy[bidId];
                return copy;
            });
        } catch (err) {
            console.error("Failed to save comment", err);
        } finally {
            setSavingComment(null);
        }
    };

    const toggleExpand = (id: number) => {
        setExpandedBidId(expandedBidId === id ? null : id);
    };

    if (loading) return (
        <GlassCard className="text-center p-12">
            <div className="animate-pulse text-white/70">Loading bids for {rfqId}...</div>
        </GlassCard>
    );

    if (bids.length === 0) {
        return (
            <GlassCard className="text-center p-12">
                <p className="text-white/50 text-lg">
                    No bids found for RFQ ID: &quot;{rfqId}&quot;. <br />
                    Upload a quote to see results.
                </p>
            </GlassCard>
        );
    }

    const minPrice = Math.min(...bids.map(b => b.total_cost || Infinity));

    return (
        <div className="space-y-6">
            <ExecutiveSummary summary={summary} loading={summaryLoading} />

            <ScoringControls
                weights={weights}
                setWeights={setWeights}
                onRecalculate={() => handleRecalculate()}
            />

            <GlassCard className="overflow-hidden !p-0">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left text-white/80">
                        <thead className="text-xs text-white uppercase bg-white/10 border-b border-white/10">
                            <tr>
                                <th className="px-6 py-4 font-bold tracking-wider w-16"></th>
                                <th className="px-6 py-4 font-bold tracking-wider">Rank & Score</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Vendor</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Total Cost</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Lead Time</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Incoterms</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Warranty</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Compliance</th>
                                <th className="px-6 py-4 font-bold tracking-wider text-right min-w-[320px]">Review & Decision</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {bids.map((bid, index) => {
                                const isLowestPrice = bid.total_cost === minPrice && minPrice !== Infinity;
                                const isNonCompliant = bid.compliance_status?.toLowerCase().includes("no") ||
                                    bid.compliance_status?.toLowerCase().includes("non");
                                const isCompliant = bid.compliance_status?.toLowerCase().includes("yes");
                                const rankClass = index === 0 ? "text-yellow-300 font-bold" : "";
                                const isExpanded = expandedBidId === bid.id;

                                return (
                                    <React.Fragment key={bid.id}>
                                        <tr
                                            className={`hover:bg-white/5 transition-colors duration-200 cursor-pointer ${isExpanded ? 'bg-white/5' : ''}`}
                                            onClick={() => toggleExpand(bid.id)}
                                        >
                                            <td className="px-6 py-5 text-center">
                                                {isExpanded ? <ChevronUp className="w-4 h-4 text-white/50" /> : <ChevronDown className="w-4 h-4 text-white/50" />}
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className="flex flex-col">
                                                    <span className={`text-lg ${rankClass}`}>#{index + 1}</span>
                                                    <div className="flex items-center gap-1 text-xs text-white/50">
                                                        <span>{bid.score ?? 0} / 100</span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-5 font-semibold text-white">
                                                <div className="flex items-center gap-2 whitespace-nowrap">
                                                    {bid.vendor_name}
                                                    {bid.is_iatf_certified && (
                                                        <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-300 text-[10px] font-black rounded border border-blue-500/30">IATF</span>
                                                    )}
                                                </div>
                                                <StatusBadge status={bid.status} />
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ring-1 ring-inset
                                                    ${isLowestPrice
                                                        ? 'bg-green-400/10 text-green-200 ring-green-400/30'
                                                        : 'bg-white/5 text-white/70 ring-white/10'}`}>
                                                    {bid.total_cost ? `$${bid.total_cost.toLocaleString()}` : "-"}
                                                    {isLowestPrice && <span className="ml-1">★</span>}
                                                </div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className="flex items-center gap-2">
                                                    <Clock className="w-3 h-3 opacity-50" />
                                                    {bid.lead_time || "-"}
                                                </div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <span className="text-white/60 font-mono text-xs uppercase tracking-widest">{bid.incoterms || "N/A"}</span>
                                            </td>
                                            <td className="px-6 py-5">
                                                <span className="text-white/60 text-xs">{bid.warranty_terms || "-"}</span>
                                            </td>
                                            <td className="px-6 py-5">
                                                {isCompliant ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-500/20 text-green-200 text-xs font-medium border border-green-500/30">
                                                        <CheckCircle className="w-3 h-3" /> Yes
                                                    </span>
                                                ) : isNonCompliant ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-red-500/20 text-red-200 text-xs font-medium border border-red-500/30">
                                                        <XCircle className="w-3 h-3" /> No
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-200 text-xs font-medium border border-yellow-500/30">
                                                        <HelpCircle className="w-3 h-3" /> {bid.compliance_status || "?"}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-right align-top" onClick={(e) => e.stopPropagation()}>
                                                {isManager ? (
                                                    <div className="flex flex-col gap-2 min-w-[280px]">
                                                        {/* Decision Buttons Row */}
                                                        <div className="flex items-center justify-end gap-1.5 text-xs">
                                                            <button
                                                                onClick={() => setDecisionModal({ bid, action: 'shortlisted' })}
                                                                className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/40 text-emerald-200 rounded border border-emerald-500/30 transition-colors flex items-center gap-1"
                                                                title="Shortlist this vendor"
                                                            >
                                                                <Bookmark className="w-3 h-3" />
                                                                Shortlist
                                                            </button>
                                                            <button
                                                                onClick={() => setDecisionModal({ bid, action: 'hold' })}
                                                                className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/40 text-amber-200 rounded border border-amber-500/30 transition-colors flex items-center gap-1"
                                                                title="Put on hold"
                                                            >
                                                                <AlertTriangle className="w-3 h-3" />
                                                                Hold
                                                            </button>
                                                            <button
                                                                onClick={() => setDecisionModal({ bid, action: 'rejected' })}
                                                                className="px-2.5 py-1 bg-red-500/20 hover:bg-red-500/40 text-red-200 rounded border border-red-500/30 transition-colors flex items-center gap-1"
                                                                title="Reject this vendor"
                                                            >
                                                                <XCircle className="w-3 h-3" />
                                                                Reject
                                                            </button>
                                                            <button
                                                                onClick={async () => {
                                                                    if (confirm("Delete this bid?")) {
                                                                        await api.delete(`/quotes/bids/${bid.id}`);
                                                                        fetchData();
                                                                    }
                                                                }}
                                                                className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-white/40 rounded border border-white/10 transition-colors"
                                                                title="Delete Bid"
                                                            >
                                                                Delete
                                                            </button>
                                                        </div>
                                                        {/* Inline Comment Box */}
                                                        <div className="flex gap-1.5 items-start">
                                                            <textarea
                                                                value={editingComments[bid.id] ?? bid.reviewer_comments ?? ''}
                                                                onChange={(e) => setEditingComments(prev => ({ ...prev, [bid.id]: e.target.value }))}
                                                                onClick={(e) => e.stopPropagation()}
                                                                placeholder="Write a review..."
                                                                rows={2}
                                                                className="flex-1 px-2.5 py-1.5 bg-white/5 border border-white/10 rounded text-[11px] text-white placeholder-white/25 focus:outline-none focus:border-blue-500/40 resize-none transition-all leading-tight"
                                                            />
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); handleSaveComment(bid.id); }}
                                                                disabled={savingComment === bid.id || editingComments[bid.id] === undefined}
                                                                className={`px-2 py-1.5 text-[10px] font-bold rounded border transition-all shrink-0
                                                                    ${editingComments[bid.id] !== undefined
                                                                        ? 'bg-blue-500/20 hover:bg-blue-500/40 text-blue-200 border-blue-500/30'
                                                                        : 'bg-white/5 text-white/20 border-white/10 cursor-not-allowed'
                                                                    }`}
                                                                title="Save comment"
                                                            >
                                                                {savingComment === bid.id ? '...' : 'Save'}
                                                            </button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="min-w-[240px] text-left">
                                                        {bid.reviewer_comments ? (
                                                            <div className="p-2.5 bg-blue-500/5 rounded-lg border border-blue-500/15">
                                                                <p className="text-[9px] text-blue-300/60 uppercase font-black tracking-widest mb-1 flex items-center gap-1">
                                                                    <MessageSquare className="w-3 h-3" />
                                                                    Manager Review
                                                                </p>
                                                                <p className="text-[11px] text-white/70 leading-relaxed whitespace-pre-wrap">
                                                                    {bid.reviewer_comments}
                                                                </p>
                                                            </div>
                                                        ) : (
                                                            <span className="text-white/25 text-[11px] italic">No review yet</span>
                                                        )}
                                                    </div>
                                                )}
                                            </td>
                                        </tr>
                                        {isExpanded && (
                                            <tr className="bg-white/5 border-t border-white/5">
                                                <td colSpan={9} className="px-6 py-6">
                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                                        {/* Score Breakdown */}
                                                        {bid.score_breakdown && (
                                                            <div className="space-y-4">
                                                                <h4 className="text-xs font-bold text-white/60 uppercase tracking-widest mb-3">Score Breakdown</h4>

                                                                {/* Price Breakdown */}
                                                                <div>
                                                                    <div className="flex justify-between text-xs mb-1">
                                                                        <span className="text-blue-300">Price (w: {bid.score_breakdown.price.weight})</span>
                                                                        <span className="text-white font-mono">
                                                                            {bid.score_breakdown.price.normalized}% × {bid.score_breakdown.price.weight} = <span className="text-blue-400 font-bold">{bid.score_breakdown.price.score}</span>
                                                                        </span>
                                                                    </div>
                                                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                                        <div className="h-full bg-blue-500" style={{ width: `${bid.score_breakdown.price.normalized}%` }} />
                                                                    </div>
                                                                    <p className="text-[10px] text-white/40 mt-1">
                                                                        Raw Value: ${Number(bid.score_breakdown.price.value).toLocaleString()}
                                                                    </p>
                                                                </div>

                                                                {/* Lead Time Breakdown */}
                                                                <div>
                                                                    <div className="flex justify-between text-xs mb-1">
                                                                        <span className="text-green-300">Lead Time (w: {bid.score_breakdown.lead_time.weight})</span>
                                                                        <span className="text-white font-mono">
                                                                            {bid.score_breakdown.lead_time.normalized}% × {bid.score_breakdown.lead_time.weight} = <span className="text-green-400 font-bold">{bid.score_breakdown.lead_time.score}</span>
                                                                        </span>
                                                                    </div>
                                                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                                        <div className="h-full bg-green-500" style={{ width: `${bid.score_breakdown.lead_time.normalized}%` }} />
                                                                    </div>
                                                                    <p className="text-[10px] text-white/40 mt-1">
                                                                        Raw Value: {bid.score_breakdown.lead_time.value}
                                                                    </p>
                                                                </div>

                                                                {/* Compliance Breakdown */}
                                                                <div>
                                                                    <div className="flex justify-between text-xs mb-1">
                                                                        <span className="text-purple-300">Compliance (w: {bid.score_breakdown.compliance.weight})</span>
                                                                        <span className="text-white font-mono">
                                                                            {bid.score_breakdown.compliance.normalized}% × {bid.score_breakdown.compliance.weight} = <span className="text-purple-400 font-bold">{bid.score_breakdown.compliance.score}</span>
                                                                        </span>
                                                                    </div>
                                                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                                        <div className="h-full bg-purple-500" style={{ width: `${bid.score_breakdown.compliance.normalized}%` }} />
                                                                    </div>
                                                                    <p className="text-[10px] text-white/40 mt-1">
                                                                        Status: {bid.score_breakdown.compliance.value}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Risk Factors */}
                                                        <div className="md:col-span-2 space-y-4">
                                                            <div>
                                                                <h4 className="text-xs font-bold text-white/60 uppercase tracking-widest mb-3">Analysis & Risks</h4>
                                                                <div className="p-3 bg-white/5 rounded-lg border border-white/10 text-xs text-white/80 leading-relaxed">
                                                                    {bid.risk_flags ? (
                                                                        <ul className="list-disc list-inside">
                                                                            {(() => {
                                                                                try {
                                                                                    const risks = JSON.parse(bid.risk_flags);
                                                                                    return Array.isArray(risks) ? risks.map((r: any, i: number) => (
                                                                                        <li key={i} className="text-red-200/80 mb-2 leading-tight">
                                                                                            <span className="font-semibold">{typeof r === 'string' ? r : r.risk}</span>
                                                                                            {typeof r === 'object' && r.evidence && (
                                                                                                <span className="block text-[10px] text-white/50 italic mt-1 ml-5">
                                                                                                    ↳ {r.evidence}
                                                                                                </span>
                                                                                            )}
                                                                                        </li>
                                                                                    )) : <li>{bid.risk_flags}</li>
                                                                                } catch {
                                                                                    return <li>{bid.risk_flags}</li>
                                                                                }
                                                                            })()}
                                                                        </ul>
                                                                    ) : (
                                                                        <span className="text-white/40 italic">No specific risk flags detected.</span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Procurement Manager Review / Comments Section - Full Width */}
                                                        <div className="md:col-span-3">
                                                            <div className="p-5 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-xl border border-blue-500/15">
                                                                <h4 className="text-xs font-bold text-blue-300/80 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                                    <MessageSquare className="w-4 h-4" />
                                                                    Procurement Manager Review
                                                                    {bid.status && !['pending', 'ingested'].includes(bid.status) && (
                                                                        <StatusBadge status={bid.status} />
                                                                    )}
                                                                </h4>

                                                                {/* Display existing comment */}
                                                                {bid.reviewer_comments && editingComments[bid.id] === undefined && (
                                                                    <div className="mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
                                                                        <p className="text-xs text-white/40 uppercase font-bold tracking-wider mb-1">Current Review</p>
                                                                        <p className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
                                                                            {bid.reviewer_comments}
                                                                        </p>
                                                                    </div>
                                                                )}

                                                                {/* Editable comment area for managers */}
                                                                {isManager ? (
                                                                    <div className="space-y-3">
                                                                        <textarea
                                                                            value={editingComments[bid.id] ?? bid.reviewer_comments ?? ''}
                                                                            onChange={(e) => setEditingComments(prev => ({ ...prev, [bid.id]: e.target.value }))}
                                                                            placeholder="Add your review, comments, or decision rationale for this bid..."
                                                                            rows={3}
                                                                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/25 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 resize-none transition-all"
                                                                        />
                                                                        <div className="flex items-center justify-between">
                                                                            <p className="text-[10px] text-white/25">Comments are logged in the audit trail</p>
                                                                            <button
                                                                                onClick={(e) => { e.stopPropagation(); handleSaveComment(bid.id); }}
                                                                                disabled={savingComment === bid.id || editingComments[bid.id] === undefined}
                                                                                className={`px-5 py-1.5 text-xs font-bold rounded-lg border transition-all flex items-center gap-1.5
                                                                                    ${editingComments[bid.id] !== undefined
                                                                                        ? 'bg-blue-500/20 hover:bg-blue-500/40 text-blue-200 border-blue-500/30 cursor-pointer'
                                                                                        : 'bg-white/5 text-white/20 border-white/10 cursor-not-allowed'
                                                                                    }`}
                                                                            >
                                                                                <MessageSquare className="w-3 h-3" />
                                                                                {savingComment === bid.id ? 'Saving...' : 'Save Comment'}
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                ) : (
                                                                    !bid.reviewer_comments && (
                                                                        <p className="text-xs text-white/30 italic">No review comments yet.</p>
                                                                    )
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
                <div className="px-6 py-4 bg-white/5 border-t border-white/5 text-center">
                    <p className="text-[10px] text-white/30 uppercase tracking-widest">
                        AI-Generated Results • Verify Independent of this Dashboard
                    </p>
                </div>
            </GlassCard>

            {/* Decision Modal */}
            {decisionModal && (
                <DecisionModal
                    bid={decisionModal.bid}
                    action={decisionModal.action}
                    onClose={() => setDecisionModal(null)}
                    onSubmit={handleDecisionSubmit}
                />
            )}
        </div>
    );
}
