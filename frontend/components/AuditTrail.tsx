"use client";

import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import GlassCard from './GlassCard';
import { History as HistoryIcon, User, Activity } from 'lucide-react';

interface Log {
    id: number;
    action: string;
    details: string;
    created_at: string;
    user_id: number;
}

export default function AuditTrail() {
    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLogs();
    }, []);

    const fetchLogs = async () => {
        try {
            const res = await api.get('/auth/audit-logs'); // Assuming we add this endpoint
            setLogs(res.data);
        } catch (err) {
            console.error("Failed to fetch logs", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-white/50 animate-pulse text-center p-10">Loading audit trail...</div>;

    return (
        <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                <HistoryIcon className="w-6 h-6 text-blue-400" />
                Audit Trail & Governance
            </h2>
            <div className="space-y-3">
                {logs.length === 0 ? (
                    <p className="text-white/40 italic text-center p-8 bg-white/5 rounded-xl border border-white/5">No activity recorded yet.</p>
                ) : (
                    logs.map((log) => (
                        <GlassCard key={log.id} className="!p-4 border-white/5">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-lg ${log.action.includes('APPROVE') ? 'bg-green-500/20 text-green-300' :
                                        log.action.includes('REJECT') ? 'bg-red-500/20 text-red-300' :
                                            'bg-blue-500/20 text-blue-300'
                                        }`}>
                                        <Activity className="w-4 h-4" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-white">{log.action}</p>
                                        <p className="text-xs text-white/50">{log.details}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="flex items-center gap-1.5 text-[10px] text-white/40 mb-1">
                                        <User className="w-3 h-3" />
                                        User ID: {log.user_id}
                                    </div>
                                    <p className="text-[10px] text-white/30 font-mono">
                                        {new Date(log.created_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </GlassCard>
                    ))
                )}
            </div>
        </div>
    );
}
