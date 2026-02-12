import React from 'react';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
}

const GlassCard = ({ children, className = '', onClick }: GlassCardProps) => {
    return (
        <div className={`glass-panel p-6 ${className}`} onClick={onClick}>
            {children}
        </div>
    );
};

export default GlassCard;
