"use client";

import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { CheckCircle, XCircle, HelpCircle, Clock } from 'lucide-react';
import GlassCard from './GlassCard';
import ScoringControls from './ScoringControls';
import ExecutiveSummary from './ExecutiveSummary';
import { useAuth } from '../context/AuthContext';

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
    risk_flags?: string; // JSON string
    score?: number;
    status?: string;
}

export default function ComparisonTable({ refreshTrigger, rfqId }: { refreshTrigger: number, rfqId: string }) {
    const [bids, setBids] = useState<Bid[]>([]);
    const [loading, setLoading] = useState(false);
    const [summary, setSummary] = useState("");
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [weights, setWeights] = useState({ price: 0.5, lead_time: 0.3, compliance: 0.2 });
    const [expandedBidId, setExpandedBidId] = useState<number | null>(null);
    const { user } = useAuth();

    // ... fetchData, fetchSummary, etc. same as before ... 

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
            // Sort by score descending
            const sortedBids = res.data.sort((a: Bid, b: Bid) => (b.score || 0) - (a.score || 0));
            setBids(sortedBids);
        } catch (err) {
            console.error(err);
        }
    };

    const handleStatusUpdate = async (bidId: number, status: string) => {
        try {
            await api.patch(`/quotes/bids/${bidId}/status?status=${status}`);
            setBids(prev => prev.map(b => b.id === bidId ? { ...b, status } : b));
        } catch (err) {
            console.error("Failed to update status", err);
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
                                <th className="px-6 py-4 font-bold tracking-wider">Rank &amp; Score</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Vendor</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Total Cost</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Lead Time</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Incoterms</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Warranty</th>
                                <th className="px-6 py-4 font-bold tracking-wider">Compliance</th>
                                <th className="px-6 py-4 font-bold tracking-wider text-right">Actions</th>
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
                                            <td className="px-6 py-5 font-semibold text-white whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    {bid.vendor_name}
                                                    {bid.is_iatf_certified && (
                                                        <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-300 text-[10px] font-black rounded border border-blue-500/30">IATF</span>
                                                    )}
                                                </div>
                                                {bid.status === "approved" && <span className="mt-1 inline-block text-[10px] bg-green-500 text-white px-1.5 py-0.5 rounded font-black tracking-tighter">APPROVED</span>}
                                                {bid.status === "rejected" && <span className="mt-1 inline-block text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded font-black tracking-tighter">REJECTED</span>}
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
                                            <td className="px-6 py-5 text-right" onClick={(e) => e.stopPropagation()}>
                                                {user?.role === 'manager' || user?.role === 'procurement_manager' ? (
                                                    <div className="flex items-center justify-end gap-2 text-xs">
                                                        <button
                                                            onClick={() => handleStatusUpdate(bid.id, "approved")}
                                                            className="px-3 py-1 bg-green-500/20 hover:bg-green-500/40 text-green-200 rounded border border-green-500/30 transition-colors"
                                                        >
                                                            Approve
                                                        </button>
                                                        <button
                                                            onClick={() => handleStatusUpdate(bid.id, "rejected")}
                                                            className="px-3 py-1 bg-red-500/20 hover:bg-red-500/40 text-red-200 rounded border border-red-500/30 transition-colors"
                                                        >
                                                            Reject
                                                        </button>
                                                        <button
                                                            onClick={async () => {
                                                                if (confirm("Delete this bid?")) {
                                                                    await api.delete(`/quotes/bids/${bid.id}`);
                                                                    fetchData();
                                                                }
                                                            }}
                                                            className="px-3 py-1 bg-white/5 hover:bg-white/10 text-white/50 rounded border border-white/10 transition-colors"
                                                            title="Delete Bid"
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <span className="text-white/30 text-xs italic">View Only</span>
                                                )}
                                            </td>
                                        </tr>
                                        {isExpanded && bid.score_breakdown && (
                                            <tr className="bg-white/5 border-t border-white/5">
                                                <td colSpan={9} className="px-6 py-6">
                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
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

                                                        {/* Risk Factors */}
                                                        <div className="md:col-span-2">
                                                            <h4 className="text-xs font-bold text-white/60 uppercase tracking-widest mb-3">Analysis & Risks</h4>
                                                            <div className="p-3 bg-white/5 rounded-lg border border-white/10 text-xs text-white/80 leading-relaxed">
                                                                {bid.risk_flags ? (
                                                                    <ul className="list-disc list-inside space-y-1">
                                                                        {(() => {
                                                                            try {
                                                                                const risks = JSON.parse(bid.risk_flags);
                                                                                return Array.isArray(risks) ? risks.map((r: string, i: number) => (
                                                                                    <li key={i} className="text-red-200/80">{r}</li>
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
        </div>
    );
}

// Helper types
import { ChevronDown, ChevronUp } from 'lucide-react';

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
    score_breakdown?: {
        price: ScoreBreakdownItem;
        lead_time: ScoreBreakdownItem;
        compliance: ScoreBreakdownItem;
    };
}
