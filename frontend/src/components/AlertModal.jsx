import React from 'react';
import { AlertCircle, X, CheckCircle } from 'lucide-react';

const AlertModal = ({ isOpen, onClose, title, message, type = 'error' }) => {
    if (!isOpen) return null;

    const isError = type === 'error';
    const Icon = isError ? AlertCircle : CheckCircle;
    const colorClass = isError ? 'text-red-600 bg-red-100' : 'text-green-600 bg-green-100';
    const btnClass = isError ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700';

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6 relative transform transition-all scale-100">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <X size={24} />
                </button>
                <div className="flex flex-col items-center text-center">
                    <div className={`p-3 rounded-full mb-4 ${colorClass}`}>
                        <Icon size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
                    <p className="text-gray-500 mb-6">{message}</p>
                    <button
                        onClick={onClose}
                        className={`w-full px-4 py-2 rounded-lg text-white font-medium transition-colors ${btnClass}`}
                    >
                        Entendido
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AlertModal;
