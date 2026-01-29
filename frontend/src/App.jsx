import React, { useState, useEffect } from 'react';
import { supabase } from './lib/supabaseClient';
import Login from './components/Login';
import QuotesTable from './components/QuotesTable';
import BroadcastListModal from './components/BroadcastListModal';
import ProductManagementPage from './components/ProductManagementPage';
import { quotesAPI, broadcastAPI } from './services/api';
import { MessageSquare, RefreshCw, LogOut, AlertCircle, ShoppingBag, LayoutDashboard } from 'lucide-react';

function App() {
    const [session, setSession] = useState(null);
    const [loadingSession, setLoadingSession] = useState(true);

    // Estados de la aplicación
    const [quotes, setQuotes] = useState([]);
    const [selectedClients, setSelectedClients] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' | 'products'

    // Manejo de sesión
    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setLoadingSession(false);
        });

        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
        });

        return () => subscription.unsubscribe();
    }, []);

    // Cargar datos solo si hay sesión
    useEffect(() => {
        if (session) {
            loadQuotes();
        }
    }, [session]);

    const loadQuotes = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await quotesAPI.getAll();
            // La respuesta paginada viene en response.quotes
            const quotesArray = response.quotes || [];
            // Ordenar por ID descendente
            const sortedData = quotesArray.sort((a, b) => b.id - a.id);
            setQuotes(sortedData);
        } catch (err) {
            console.error('Error loading quotes:', err);
            setError('Error al cargar las cotizaciones. Intente nuevamente.');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectClient = (client) => {
        setSelectedClients((prev) => {
            const exists = prev.some((c) => c.phone === client.phone);
            if (exists) {
                return prev.filter((c) => c.phone !== client.phone);
            }
            return [...prev, client];
        });
    };

    const handleOpenBroadcastModal = () => {
        if (selectedClients.length === 0) return;
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedClients([]);
    };

    const handleSendBroadcast = async (clients, templateName, languageCode, parameters) => {
        try {
            const result = await broadcastAPI.sendTemplate(
                clients,
                templateName,
                languageCode,
                parameters
            );
            return result;
        } catch (error) {
            throw new Error(error.response?.data?.detail || 'Error al enviar mensajes');
        }
    };

    const handleLogout = async () => {
        await supabase.auth.signOut();
    };

    if (loadingSession) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    if (!session) {
        return <Login />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="bg-primary-600 p-2 rounded-lg">
                            <span className="text-white font-bold text-xl">SC</span>
                        </div>
                        <h1 className="text-xl font-bold text-gray-900">
                            Sistema de Cotizaciones
                        </h1>
                    </div>
                    <nav className="flex items-center space-x-1 mr-4">
                        <button
                            onClick={() => setCurrentView('dashboard')}
                            className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center ${currentView === 'dashboard'
                                    ? 'bg-primary-50 text-primary-700'
                                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                        >
                            <LayoutDashboard size={18} className="mr-1.5" />
                            Dashboard
                        </button>
                        <button
                            onClick={() => setCurrentView('products')}
                            className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center ${currentView === 'products'
                                    ? 'bg-primary-50 text-primary-700'
                                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                        >
                            <ShoppingBag size={18} className="mr-1.5" />
                            Productos
                        </button>
                    </nav>

                    <div className="flex items-center space-x-2 border-l pl-4">
                        <span className="text-sm text-gray-500 hidden sm:block">
                            {session.user.email}
                        </span>
                        <button
                            onClick={loadQuotes}
                            disabled={loading}
                            className="p-2 text-gray-500 hover:text-primary-600 hover:bg-gray-100 rounded-full transition disabled:opacity-50"
                            title="Actualizar tabla"
                        >
                            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
                        </button>
                        <button
                            onClick={handleLogout}
                            className="p-2 text-gray-500 hover:text-red-600 hover:bg-gray-100 rounded-full transition"
                            title="Cerrar sesión"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {currentView === 'products' ? (
                    <ProductManagementPage />
                ) : (
                    <>
                        {/* Actions Bar */}
                        <div className="mb-6 flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200">
                                    <span className="text-sm font-medium text-gray-500">
                                        Seleccionados:
                                    </span>
                                    <span className="ml-2 text-lg font-bold text-primary-600">
                                        {selectedClients.length}
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={handleOpenBroadcastModal}
                                disabled={selectedClients.length === 0}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition ${selectedClients.length > 0
                                    ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-md transform hover:-translate-y-0.5'
                                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                <MessageSquare size={20} />
                                <span>Crear Lista de Difusión</span>
                            </button>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
                                <div className="flex bg-red-50 p-4 rounded-lg items-start gap-3">
                                    <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
                                    <div>
                                        <h3 className="font-semibold text-red-900">Error</h3>
                                        <p className="text-red-700 text-sm mt-1">{error}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Loading State */}
                        {loading && quotes.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600 mb-4"></div>
                                <p className="text-gray-500">Cargando cotizaciones...</p>
                            </div>
                        )}

                        {/* Quotes Table */}
                        {!loading && quotes.length === 0 && !error ? (
                            <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
                                <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
                                    <RefreshCw className="mx-auto h-12 w-12 text-gray-400" />
                                </div>
                                <h3 className="mt-2 text-sm font-medium text-gray-900">
                                    No hay cotizaciones
                                </h3>
                                <p className="mt-1 text-sm text-gray-500">
                                    Las cotizaciones llegarán automáticamente desde WhatsApp.
                                </p>
                            </div>
                        ) : (
                            <QuotesTable
                                quotes={quotes}
                                selectedClients={selectedClients}
                                onSelectClient={handleSelectClient}
                            />
                        )}

                        {/* Stats */}
                        {!loading && quotes.length > 0 && (
                            <div className="mt-4 text-sm text-gray-500 flex justify-between px-2">
                                <span>Total: {quotes.length} cotizaciones</span>
                                <span>
                                    Última actualización:{' '}
                                    {new Date().toLocaleTimeString('es-ES', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                    })}
                                </span>
                            </div>
                        )}
                    </>
                )}
            </main>

            {/* Broadcast Modal */}
            <BroadcastListModal
                isOpen={isModalOpen}
                onClose={handleCloseModal}
                selectedClients={selectedClients}
                onSend={handleSendBroadcast}
            />
        </div>
    );
}

export default App;
