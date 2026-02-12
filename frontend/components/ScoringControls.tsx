import React from 'react';
import { Settings2 } from 'lucide-react';

interface ScoringWeights {
    price: number;
    lead_time: number;
    compliance: number;
}

interface ScoringControlsProps {
    weights: ScoringWeights;
    setWeights: (weights: ScoringWeights) => void;
    onRecalculate: () => void;
}

const ScoringControls = ({ weights, setWeights, onRecalculate }: ScoringControlsProps) => {

    const handleChange = (key: keyof ScoringWeights, value: string) => {
        const numVal = parseFloat(value);
        setWeights({ ...weights, [key]: numVal });
    };

    const totalWeight = weights.price + weights.lead_time + weights.compliance;
    const isBalanced = Math.abs(totalWeight - 1.0) < 0.01;

    return (
        <div className="bg-white/5 backdrop-blur-md rounded-xl p-6 mb-6 border border-white/10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-2 text-white/90">
                    <Settings2 className="w-5 h-5" />
                    <span className="font-semibold">Scoring Algorithm Weights</span>
                </div>
                <div className="text-xs font-mono text-white/50 bg-black/20 px-3 py-1.5 rounded-lg border border-white/5">
                    Formula: (Price_Norm × {weights.price}) + (LeadTime_Norm × {weights.lead_time}) + (Compliance_Norm × {weights.compliance})
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-xs font-bold text-blue-300 uppercase tracking-wider">
                            Price Impact
                        </label>
                        <span className="text-xs font-mono text-white">{weights.price.toFixed(1)}</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={weights.price}
                        onChange={(e) => handleChange('price', e.target.value)}
                        className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-all"
                    />
                    <p className="mt-1.5 text-[10px] text-white/40">Higher value prioritizes lower cost.</p>
                </div>

                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-xs font-bold text-green-300 uppercase tracking-wider">
                            Lead Time Impact
                        </label>
                        <span className="text-xs font-mono text-white">{weights.lead_time.toFixed(1)}</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={weights.lead_time}
                        onChange={(e) => handleChange('lead_time', e.target.value)}
                        className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-green-500 hover:accent-green-400 transition-all"
                    />
                    <p className="mt-1.5 text-[10px] text-white/40">Higher value prioritizes faster delivery.</p>
                </div>

                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-xs font-bold text-purple-300 uppercase tracking-wider">
                            Compliance Impact
                        </label>
                        <span className="text-xs font-mono text-white">{weights.compliance.toFixed(1)}</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={weights.compliance}
                        onChange={(e) => handleChange('compliance', e.target.value)}
                        className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-purple-500 hover:accent-purple-400 transition-all"
                    />
                    <p className="mt-1.5 text-[10px] text-white/40">Higher value prioritizes adherence to requirements.</p>
                </div>
            </div>

            <div className="mt-6 pt-4 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                <div className={`text-xs px-3 py-1.5 rounded-full border ${isBalanced ? 'bg-green-500/10 text-green-300 border-green-500/20' : 'bg-yellow-500/10 text-yellow-300 border-yellow-500/20'}`}>
                    Total Weight: <span className="font-bold">{totalWeight.toFixed(1)}</span> {isBalanced ? '✅ Balanced' : '⚠️ Top-up to 1.0 recommended'}
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={() => setWeights({ price: 0.5, lead_time: 0.3, compliance: 0.2 })}
                        className="px-4 py-2 hover:bg-white/5 text-white/60 hover:text-white rounded-lg text-sm font-medium transition-colors border border-transparent hover:border-white/10"
                    >
                        Reset Defaults
                    </button>
                    <button
                        onClick={onRecalculate}
                        className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-bold shadow-lg shadow-blue-900/20 transition-all transform active:scale-95"
                    >
                        Apply & Recalculate Scores
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ScoringControls;
