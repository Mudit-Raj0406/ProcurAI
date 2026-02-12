"use client";

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Loader2, FileType, CheckCircle2 } from 'lucide-react';
import api from '../lib/api';
import GlassCard from './GlassCard';

interface FileUploadProps {
    onUploadComplete: () => void;
    rfqId: string;
    type?: 'rfq' | 'bid';
}

export default function FileUpload({ onUploadComplete, rfqId, type = 'bid' }: FileUploadProps) {
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        if (!rfqId) {
            setError("Please enter an RFQ ID first.");
            return;
        }

        setUploading(true);
        setSuccess(false);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('rfq_id', rfqId);

        const endpoint = type === 'rfq' ? '/quotes/upload-rfq' : '/quotes/upload';

        try {
            const response = await api.post(endpoint, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setSuccess(true);
            setTimeout(() => setSuccess(false), 3000);
            onUploadComplete();
        } catch (err: any) {
            console.error(err);
            const detail = err.response?.data?.detail || `Failed to upload and extract ${type === 'rfq' ? 'Master RFQ' : 'Vendor Bid'}.`;
            setError(detail);
        } finally {
            setUploading(false);
        }
    }, [onUploadComplete, rfqId, type]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf']
        },
        multiple: false
    });

    return (
        <GlassCard className="w-full mx-auto transform transition-all hover:scale-[1.01] duration-300">
            <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300
          ${isDragActive
                        ? 'border-white bg-white/20 scale-105'
                        : 'border-white/30 hover:border-white/60 hover:bg-white/5'}
        `}
            >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center justify-center space-y-4">
                    {uploading ? (
                        <>
                            <div className="relative">
                                <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 animate-pulse rounded-full"></div>
                                <Loader2 className="w-12 h-12 text-white animate-spin relative z-10" />
                            </div>
                            <p className="text-white/80 animate-pulse font-medium">Ingesting document...</p>
                        </>
                    ) : success ? (
                        <>
                            <div className="p-4 bg-green-500/20 rounded-full mb-2 backdrop-blur-sm shadow-inner ring-1 ring-green-500/50">
                                <CheckCircle2 className="w-10 h-10 text-green-400" />
                            </div>
                            <div>
                                <p className="text-xl font-bold text-green-400 mb-1">Upload Successful!</p>
                                <p className="text-sm text-white/50">Document is ready for analysis.</p>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="p-4 bg-white/10 rounded-full mb-2 backdrop-blur-sm shadow-inner ring-1 ring-white/20">
                                <UploadCloud className="w-10 h-10 text-white" />
                            </div>
                            <div>
                                <p className="text-xl font-bold text-white mb-2">
                                    {isDragActive ? "Drop the PDF here" : "Click or drag PDF to upload"}
                                </p>
                                <div className="flex items-center justify-center gap-2 text-sm text-white/50">
                                    <FileType className="w-4 h-4" />
                                    <span>Accepts PDF {type === 'rfq' ? 'Master RFQ' : 'Vendor Quote'} documents</span>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
            {error && (
                <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-200 text-center text-sm backdrop-blur-md">
                    {error}
                </div>
            )}
        </GlassCard>
    );
}


